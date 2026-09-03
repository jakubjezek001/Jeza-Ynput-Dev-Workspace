#!/usr/bin/env python

"""Upload addon zip using ayon-python-api.

It's used to upload addons versions that epcified as arguments.
It requires having a .env file with the following keys:
- 'AYON_SERVER_URL': AYON server URL
- 'AYON_API_KEY': AYON service user api key

Script usage examples:
  python upload-addon-folder.py --addon ayon-core --addon ayon-nuke
Support flags:
'--debug': used to make log more verbose.
'--addon' ('-a'): used to specify addon repo full path, it'll be used to get addon zip name.

Notes:
    users must at least one of these flags '--addon or '--package-dir'.
    if '--package-dir' not found, the code will fall to default package dir in the given addon paths.
    if '--addon' not found, the code will upload all packages found in the given package dir.

"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

import ayon_api
import click
from ayon_api import get_server_api_connection
from dotenv import load_dotenv

load_dotenv()

scripts_dir = Path(__file__).resolve().parent
workspace_dir = Path(__file__).resolve().parent.parent.parent

docker_addons_dir = workspace_dir / "ayon-docker" / "addons"

python_exe = sys.executable


def _resolve_addon(
    file_path: Path, workspace_dir: Path
) -> tuple[str, Path] | None:
    """Resolve the addon name and its actual checkout directory for a file.

    Returns both the addon's name (e.g. ``"ayon-resolve"``) and the directory
    that actually contains the addon's working copy for this file. Those are
    *not* always the same as ``<workspace_dir>/<addon-name>``: a file may live
    inside a worktree, either one created via `git worktree add`
    (`<ROOT>/<addon>.worktrees/<branch>/...`) or via Zed's own picker
    (`<ROOT>/worktrees/<addon>/<random-name>/<addon>/...`). Package generation
    must run from *that* checkout, or it silently packages and uploads the
    main checkout's code instead of the one the file actually belongs to.

    Uses git itself to answer both questions from the file's containing
    directory:
      - ``--git-common-dir``'s parent folder name is the addon name (stable
        across every checkout of the same repo, main or worktree).
      - ``--show-toplevel`` is the checkout root that actually contains the
        file (the worktree root, if the file is inside one; the main
        checkout root otherwise).

    Falls back to the first path segment relative to the workspace root, and
    ``workspace_dir / addon_name`` as the directory, for files that are not
    inside a git repository at all.

    Returns:
        tuple[str, Path] | None: ``(addon_name, addon_repo_dir)``, or
        ``None`` if the addon could not be determined.
    """
    search_dir = file_path if file_path.is_dir() else file_path.parent

    def _git(*args: str) -> str | None:
        try:
            return subprocess.run(
                ["git", "-C", str(search_dir), *args],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    common_dir = _git(
        "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    if common_dir:
        addon_name = Path(common_dir).parent.name
        if addon_name.startswith("ayon-"):
            toplevel = _git("rev-parse", "--show-toplevel")
            addon_dir = (
                Path(toplevel) if toplevel else workspace_dir / addon_name
            )
            return addon_name, addon_dir

    if file_path.is_absolute():
        try:
            file_path = file_path.relative_to(workspace_dir)
        except ValueError:
            return None
    if not file_path.parts:
        return None
    first_folder = file_path.parts[0]
    if first_folder.startswith("ayon-"):
        return first_folder, workspace_dir / first_folder
    return None


@click.command()
@click.option("--debug", is_flag=True, help="Debug log messages.")
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    help="File path, relative or absolute, pointing inside the workspace.",
)
def upload_to_addon_folder(debug, file_path):
    # Set Log Level and create log object
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    log: logging.Logger = logging.getLogger("upload_package")

    # Validate required environment variables
    required_env_vars = ["AYON_SERVER_URL", "AYON_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        log.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        log.error("Please ensure these are set in your .env file")
        sys.exit(1)

    # Check if docker addons directory exists
    if not docker_addons_dir.exists():
        log.error(f"Docker addons directory not found: {docker_addons_dir}")
        log.error("Please ensure ayon-docker repository is cloned")
        sys.exit(1)

    repo_folders = os.listdir(workspace_dir.as_posix())

    addon_resolved = _resolve_addon(Path(file_path), workspace_dir)
    if addon_resolved is None:
        log.error(f"No valid addon path found for {file_path}")
        sys.exit(1)
    addons = [addon_resolved]

    processed_addons = []
    for addon, addon_repo_dir in addons:
        if addon not in repo_folders:
            log.warning(f"Addon {addon} not found in workspace")
            continue

        create_package_script = addon_repo_dir / "create_package.py"

        if not create_package_script.exists():
            log.error(f"create_package.py not found in {addon_repo_dir}")
            continue

        # Use subprocess instead of os.system for better error handling
        cmd = [
            python_exe,
            str(create_package_script),
            "--skip-zip",
            "--output",
            str(docker_addons_dir),
        ]

        log.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            log.info(f"Package created successfully for {addon}")
            if debug:
                log.debug(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to create package for {addon}: {e}")
            log.error(f"Error output: {e.stderr}")
            continue

        processed_addons.append(addon)

    if not processed_addons:
        log.error("No addons found to process.")
        sys.exit(1)

    # Log in and Try to upload addons
    try:
        ayon_api.init_service()
        log.info("AYON API initialized successfully")
    except Exception as e:
        log.error(f"Failed to initialize AYON API: {e}")
        log.error(
            "Please check your AYON_SERVER_URL and AYON_API_KEY in .env file"
        )
        sys.exit(1)

    log.info("Trying to restart server")

    try:
        server = get_server_api_connection()
        if server:
            server.trigger_server_restart()
            log.info("Server restart triggered successfully")
        else:
            log.warning("Could not get server connection - restart failed")
    except Exception as e:
        log.error(f"Failed to restart server: {e}")
