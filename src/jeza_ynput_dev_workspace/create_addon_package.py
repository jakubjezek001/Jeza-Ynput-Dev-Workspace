#!/usr/bin/env python

"""Create an AYON addon package from the selected checkout."""

import logging
import platform
import subprocess
import sys

import click
from dotenv import load_dotenv

from .repo_context import resolve_checkout
from .sdd_common import resolve_workspace_root

load_dotenv()


@click.command()
@click.option("--debug", is_flag=True, help="Debug log messages.")
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    help="File path, relative or absolute, inside an AYON checkout.",
)
def create_addon_package(debug, file_path):
    """Create a package using the selected file's actual checkout."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    log = logging.getLogger("create_package")
    workspace_root = resolve_workspace_root()
    context = resolve_checkout(file_path, workspace_root)
    if context is None:
        raise click.ClickException(
            f"Could not resolve an AYON checkout for {file_path}"
        )

    create_package_script = context.checkout_root / "create_package.py"
    if not create_package_script.is_file():
        raise click.ClickException(
            f"create_package.py not found in {context.checkout_root}"
        )

    command = [sys.executable, str(create_package_script)]
    log.info("Running from %s: %s", context.checkout_root, " ".join(command))
    try:
        result = subprocess.run(
            command,
            cwd=str(context.checkout_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            log.error(exc.stdout)
        if exc.stderr:
            log.error(exc.stderr)
        raise click.ClickException(
            f"Package creation failed for {context.addon_name}"
        ) from exc

    if debug:
        if result.stdout:
            log.debug(result.stdout)
        if result.stderr:
            log.debug(result.stderr)
    package_dir = context.checkout_root / "package"
    log.info("Package created successfully: %s", package_dir)
    if platform.system() == "Darwin":
        subprocess.run(["open", str(package_dir)], check=False)
    elif platform.system() == "Windows":
        subprocess.run(["explorer", str(package_dir)], check=False)
    else:
        subprocess.run(["xdg-open", str(package_dir)], check=False)
