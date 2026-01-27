"""Launcher Dev Mode

Pure Python script that launches AYON launcher in dev mode.
This script directly activates the Poetry virtual environment and runs start.py,
bypassing PowerShell and pyenv complexities.
"""

import logging
import os
import sys
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

workspace_dir = Path(__file__).resolve().parent.parent.parent


def launcher_dev_mode():
    """Launch AYON launcher in dev mode using Poetry venv."""
    level = logging.INFO
    logging.basicConfig(level=level)
    log = logging.getLogger("launcher")

    # Validate required environment variables
    required_env_vars = [
        "PYTHON_EXECUTABLE",
        "AYON_SERVER_URL",
        "AYON_STUDIO_BUNDLE_NAME",
        "AYON_USE_DEV",
        "AYON_DEBUG",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        log.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        log.error("Please ensure these are set in your .env file")
        sys.exit(1)

    python_executable = os.getenv("PYTHON_EXECUTABLE")

    # Verify Python executable exists
    if not Path(python_executable).exists():
        log.error(f"Python executable not found: {python_executable}")
        log.error("Please check PYTHON_EXECUTABLE path in your .env file")
        sys.exit(1)

    launcher_root = workspace_dir / "ayon-launcher"
    poetry_venv = launcher_root / ".venv"
    venv_python = poetry_venv / "Scripts" / "python.exe"
    start_script = launcher_root / "start.py"

    # Verify paths exist
    if not launcher_root.exists():
        log.error(f"Launcher directory not found: {launcher_root}")
        sys.exit(1)

    if not venv_python.exists():
        log.error(f"Poetry venv Python not found at: {venv_python}")
        log.error("Please run: cd ayon-launcher && .\\tools\\manage.ps1 create-env")
        sys.exit(1)

    if not start_script.exists():
        log.error(f"start.py not found at: {start_script}")
        sys.exit(1)

    # Copy environment variables and ensure PYTHON_EXECUTABLE is set
    env = os.environ.copy()
    env.pop("AYON_API_KEY", None)
    env["PYTHON_EXECUTABLE"] = python_executable

    # Build the command: Use Poetry's venv Python directly (bypasses 'poetry run' system Python check)
    # Wrap in cmd.exe /k to keep the terminal window open after execution
    # Note: When passing as a list, cmd.exe doesn't need quotes around paths with spaces
    cmd = [
        "cmd.exe",
        "/k",
        str(venv_python),
        str(start_script)
    ]

    log.info("="*70)
    log.info("AYON Launcher Dev Mode")
    log.info("="*70)
    log.info(f"Working directory: {launcher_root}")
    log.info(f"Venv Python: {venv_python}")
    log.info(f"Python executable (from .env): {python_executable}")
    log.info(f"Start script: {start_script}")
    log.info(f"Command: {' '.join(cmd)}")
    log.info("="*70)
    log.info("")
    log.info("Launching in new terminal window...")
    log.info("The terminal will STAY OPEN after execution.")
    log.info("You can see any errors and close it manually when done.")
    log.info("")

    # Launch in a new console window
    # Use CREATE_NEW_CONSOLE to open detached terminal
    subprocess.Popen(
        cmd,
        cwd=str(launcher_root),
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    log.info("✓ AYON Launcher started successfully!")


if __name__ == "__main__":
    launcher_dev_mode()
