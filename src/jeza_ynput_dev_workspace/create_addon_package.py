#!/usr/bin/env python

"""Create addon package and open browser.

Script is used to create an addon package and open the browser to the package.

"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

scripts_dir = Path(__file__).resolve().parent
workspace_dir = Path(__file__).resolve().parent.parent.parent

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
def create_addon_package(debug, file_path):
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
            log.warning(f"Addon {addon} not found in workspace")
            continue

        addon_repo_dir = workspace_dir / addon
        addon_package_dir = addon_repo_dir / "package"
        create_package_script = addon_repo_dir / "create_package.py"

        if not create_package_script.exists():
            log.error(f"create_package.py not found in {addon_repo_dir}")
            continue

        # Use subprocess instead of os.system for better error handling
        cmd = [
            python_exe,
            str(create_package_script),
        ]

        log.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
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

    # now open default file explorer to show the package root folder
    # make sure it treats macos and windows or linux differently
    log.info(f"Opening file explorer for {addon_package_dir}")
    if sys.platform == "darwin":
        subprocess.run(["open", str(addon_package_dir)])
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(addon_package_dir)])
    else:
        subprocess.run(["xdg-open", str(addon_package_dir)])
