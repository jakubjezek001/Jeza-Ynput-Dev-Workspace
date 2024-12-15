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

import logging
import os
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


@click.command()
@click.option("--debug", is_flag=True, help="Debug log messages.")
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    help="Relative file path to workspace root.",
)
def upload_to_addon_folder(debug, file_path):
    # Set Log Level and create log object
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    log: logging.Logger = logging.getLogger("upload_package")

    repo_folders = os.listdir(workspace_dir.as_posix())

    # get first folder from file path and check if ayon-* is in name
    addons = []
    file_path = Path(file_path)
    # split path to get first folder
    first_folder = file_path.parts[0]
    if first_folder.startswith("ayon-"):
        addons.append(first_folder)
    else:
        log.error("No valid addon path found")
        sys.exit(1)

    processed_addons = []
    for addon in addons:
        if addon not in repo_folders:
            continue
        addon_repo_dir = workspace_dir / addon
        args = (
            f"{python_exe} {addon_repo_dir.as_posix()}/create_package.py "
            f"--skip-zip --output {docker_addons_dir.as_posix()}"
        )
        log.info(f"Running: {args}")
        os.system(args)

        processed_addons.append(addon)

    if not processed_addons:
        log.error("No addons found to process.")
        sys.exit(1)

    # Log in and Try to upload addons
    ayon_api.init_service()
    log.info("Trying restart server")

    server = get_server_api_connection()
    if server:
        server.trigger_server_restart()
    else:
        log.warning("Could not restart server")
