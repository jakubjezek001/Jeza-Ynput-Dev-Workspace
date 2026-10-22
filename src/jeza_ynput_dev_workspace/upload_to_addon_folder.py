#!/usr/bin/env python

"""Upload addon zip using ayon-python-api.

It's used to upload addons versions that epcified as arguments.
It requires having a .env file with the following keys:
- 'AYON_SERVER_URL': AYON server URL
- 'AYON_API_KEY': AYON service user api key
- 'AYON_STUDIO_BUNDLE_NAME': (optional) development bundle which gets the
  new addon version and its addon directory activated after the restart

Script usage examples:
  python upload-addon-folder.py --addon ayon-core --addon ayon-nuke
Support flags:
'--debug': used to make log more verbose.
'--bundle': development bundle name, overrides 'AYON_STUDIO_BUNDLE_NAME'.
'--no-bundle-update': skip updating the development bundle.
'--force-bundle': skip server side bundle compatibility validation.
'--addon' ('-a'): used to specify addon repo full path, it'll be used to get addon zip name.

Notes:
    users must at least one of these flags '--addon or '--package-dir'.
    if '--package-dir' not found, the code will fall to default package dir in the given addon paths.
    if '--addon' not found, the code will upload all packages found in the given package dir.

"""

from __future__ import annotations

import logging
import os
import runpy
import subprocess
import sys
import time
from http import HTTPStatus
from pathlib import Path

import ayon_api
import click
import requests
from ayon_api import ServerAPI, get_server_api_connection
from dotenv import load_dotenv

from .repo_context import resolve_checkout
from .workspace_common import resolve_workspace_root

load_dotenv()

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
    context = resolve_checkout(file_path, workspace_dir)
    if context is None:
        return None
    return context.addon_name, context.checkout_root


def _read_package_info(addon_repo_dir: Path) -> tuple[str, str] | None:
    """Read the server addon name and version from ``package.py``.

    The bundle is keyed by the server addon name (e.g. ``"core"``), not by
    the repository name (e.g. ``"ayon-core"``).

    Returns:
        tuple[str, str] | None: ``(addon_name, addon_version)``, or ``None``
        if ``package.py`` is missing or incomplete.
    """
    package_file = addon_repo_dir / "package.py"
    if not package_file.is_file():
        return None
    package = runpy.run_path(str(package_file))
    name = package.get("name")
    version = package.get("version")
    if not name or not version:
        return None
    return name, version


def _wait_for_server_restart(
    server_url: str,
    log: logging.Logger,
    down_timeout: float = 15.0,
    up_timeout: float = 90.0,
    interval: float = 1.0,
) -> bool:
    """Wait until the server went down after restart and is up again.

    The restart request returns before the server actually shuts down, so
    waiting only for the server to respond could pass on the old process.
    If the down state is never observed (fast restart), continue anyway.

    Returns:
        bool: ``True`` when the server responds again within ``up_timeout``.
    """
    info_url = f"{server_url.rstrip('/')}/api/info"

    def is_up() -> bool:
        try:
            response = requests.get(info_url, timeout=2)
        except requests.RequestException:
            return False
        return response.status_code == HTTPStatus.OK

    deadline = time.monotonic() + down_timeout
    while time.monotonic() < deadline:
        if not is_up():
            log.debug("Server is down, waiting for it to come back")
            break
        time.sleep(interval)
    else:
        log.debug("Server restart was not observed, continuing")

    deadline = time.monotonic() + up_timeout
    while time.monotonic() < deadline:
        if is_up():
            return True
        time.sleep(interval)
    return False


def _wait_for_addon_version(
    server: ServerAPI,
    addon_name: str,
    addon_version: str,
    timeout: float = 60.0,
    interval: float = 2.0,
) -> bool:
    """Wait until the server lists ``addon_version`` of ``addon_name``.

    Returns:
        bool: ``True`` when the version is available within ``timeout``.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            addons = server.get_addons_info(details=False)["addons"]
        except (requests.RequestException, ayon_api.exceptions.ServerError):
            addons = []
        for addon in addons:
            if (
                addon["name"] == addon_name
                and addon_version in addon["versions"]
            ):
                return True
        time.sleep(interval)
    return False


def update_dev_bundle(  # noqa: PLR0913
    server: ServerAPI,
    *,
    bundle_name: str,
    addon_name: str,
    addon_version: str,
    client_dir: Path,
    log: logging.Logger,
    force: bool = False,
) -> bool:
    """Set addon version and addon directory on a development bundle.

    ``addonDevelopment`` is replaced as a whole by the server, so the
    existing entries of other addons are fetched and sent back unchanged.

    Returns:
        bool: ``True`` when the bundle was updated.
    """
    bundles = server.get_bundles()["bundles"]
    bundle = next((b for b in bundles if b["name"] == bundle_name), None)
    if bundle is None:
        log.error(f"Bundle '{bundle_name}' not found on server")
        return False
    if not bundle.get("isDev"):
        log.error(f"Bundle '{bundle_name}' is not a development bundle")
        return False

    previous_version = bundle.get("addons", {}).get(addon_name)
    addon_development = dict(bundle.get("addonDevelopment") or {})
    addon_development[addon_name] = {
        "enabled": True,
        "path": str(client_dir),
    }

    entrypoint = f"bundles/{bundle_name}"
    if force:
        entrypoint += "?force=true"
    response = server.patch(
        entrypoint,
        addons={addon_name: addon_version},
        addonDevelopment=addon_development,
    )
    if not response.ok:
        log.error(
            f"Failed to update bundle '{bundle_name}' "
            f"({response.status_code}): {response.detail}"
        )
        return False

    log.info(
        f"Bundle '{bundle_name}': {addon_name} "
        f"{previous_version} -> {addon_version}, "
        f"addon directory -> {client_dir}"
    )
    return True


def _update_dev_bundles(
    server: ServerAPI,
    processed_addons: list[tuple[str, Path]],
    *,
    bundle_name: str,
    force: bool,
    log: logging.Logger,
) -> bool:
    """Wait for the restarted server and update the dev bundle per addon.

    Returns:
        bool: ``True`` when every addon was set on the bundle.
    """
    log.info("Waiting for server to restart")
    if not _wait_for_server_restart(os.environ["AYON_SERVER_URL"], log):
        log.error("Server did not come back after restart")
        return False

    failed = False
    for addon, addon_repo_dir in processed_addons:
        package_info = _read_package_info(addon_repo_dir)
        if package_info is None:
            log.error(f"Could not read name/version from {addon} package.py")
            failed = True
            continue
        addon_name, addon_version = package_info

        if not _wait_for_addon_version(server, addon_name, addon_version):
            log.error(
                f"Server did not load {addon_name} {addon_version} in time"
            )
            failed = True
            continue

        if not update_dev_bundle(
            server,
            bundle_name=bundle_name,
            addon_name=addon_name,
            addon_version=addon_version,
            client_dir=addon_repo_dir / "client",
            log=log,
            force=force,
        ):
            failed = True

    return not failed


@click.command()
@click.option("--debug", is_flag=True, help="Debug log messages.")
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    help="File path, relative or absolute, pointing inside the workspace.",
)
@click.option(
    "--bundle",
    "bundle_name",
    default=None,
    help="Development bundle name. Defaults to AYON_STUDIO_BUNDLE_NAME.",
)
@click.option(
    "--no-bundle-update",
    is_flag=True,
    help="Do not update the development bundle after the restart.",
)
@click.option(
    "--force-bundle",
    is_flag=True,
    help="Skip server side bundle compatibility validation.",
)
def upload_to_addon_folder(
    debug, file_path, bundle_name, no_bundle_update, force_bundle
):
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

    workspace_dir = resolve_workspace_root()
    docker_addons_dir = workspace_dir / "ayon-docker" / "addons"
    if not docker_addons_dir.exists():
        log.error(f"Docker addons directory not found: {docker_addons_dir}")
        log.error("Please ensure ayon-docker repository is cloned")
        sys.exit(1)

    addon_resolved = _resolve_addon(Path(file_path), workspace_dir)
    if addon_resolved is None:
        log.error(f"No valid addon path found for {file_path}")
        sys.exit(1)
    addons = [addon_resolved]

    processed_addons = []
    for addon, addon_repo_dir in addons:
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
                cmd,
                cwd=str(addon_repo_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            log.info(f"Package created successfully for {addon}")
            if debug:
                log.debug(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to create package for {addon}: {e}")
            log.error(f"Error output: {e.stderr}")
            continue

        processed_addons.append((addon, addon_repo_dir))

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

    server = get_server_api_connection()
    if not server:
        log.error("Could not get server connection - restart failed")
        sys.exit(1)
    try:
        server.trigger_server_restart()
        log.info("Server restart triggered successfully")
    except Exception as e:
        log.error(f"Failed to restart server: {e}")
        sys.exit(1)

    if no_bundle_update:
        return

    bundle_name = bundle_name or os.getenv("AYON_STUDIO_BUNDLE_NAME")
    if not bundle_name:
        log.warning(
            "AYON_STUDIO_BUNDLE_NAME is not set - skipping bundle update"
        )
        return

    if not _update_dev_bundles(
        server,
        processed_addons,
        bundle_name=bundle_name,
        force=force_bundle,
        log=log,
    ):
        sys.exit(1)
