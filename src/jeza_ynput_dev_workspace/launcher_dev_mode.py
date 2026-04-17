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
import platform

from dotenv import load_dotenv

load_dotenv()

workspace_dir = Path(__file__).resolve().parent.parent.parent
this_filepath = Path(__file__).resolve()


def _validate_env_vars(log: logging.Logger) -> str:
    """Validate required environment variables and return python_executable."""
    required_env_vars = [
        "PYTHON_EXECUTABLE",
        "AYON_SERVER_URL",
        "AYON_STUDIO_BUNDLE_NAME",
        "AYON_USE_DEV",
        "AYON_DEBUG",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        log.error(
            "Missing required environment variables: %s",
            ", ".join(missing_vars),
        )
        log.error("Please ensure these are set in your .env file")
        sys.exit(1)

    python_executable = os.getenv("PYTHON_EXECUTABLE")
    if python_executable is None:
        log.error("PYTHON_EXECUTABLE environment variable is not set")
        sys.exit(1)

    return python_executable


def _verify_paths(
    log: logging.Logger,
    launcher_root: Path,
    venv_python: Path,
    start_script: Path,
    python_executable: str,
) -> None:
    """Verify that all required paths exist."""
    if not Path(python_executable).exists():
        log.error("Python executable not found: %s", python_executable)
        log.error("Please check PYTHON_EXECUTABLE path in your .env file")
        sys.exit(1)

    if not launcher_root.exists():
        log.error("Launcher directory not found: %s", launcher_root)
        sys.exit(1)

    if not venv_python.exists():
        log.error("Poetry venv Python not found at: %s", venv_python)
        log.error(
            r"Please run: cd ayon-launcher && .\tools\manage.ps1 create-env"
        )
        sys.exit(1)

    if not start_script.exists():
        log.error("start.py not found at: %s", start_script)
        sys.exit(1)


def launcher_dev_mode() -> None:
    """Launch AYON launcher in dev mode using Poetry venv."""
    level = logging.INFO
    logging.basicConfig(level=level)
    log = logging.getLogger("launcher")

    python_executable = _validate_env_vars(log)

    launcher_root = workspace_dir / "ayon-launcher"
    poetry_venv = launcher_root / ".venv"

    if platform.system() == "Windows":
        venv_python = poetry_venv / "Scripts" / "python.exe"
    else:
        venv_python = poetry_venv / "bin" / "python3"
    start_script = launcher_root / "start.py"

    _verify_paths(
        log, launcher_root, venv_python, start_script, python_executable
    )

    # Copy environment variables and ensure PYTHON_EXECUTABLE is set
    env = os.environ.copy()
    env.pop("AYON_API_KEY", None)
    env["PYTHON_EXECUTABLE"] = python_executable

    # Build the command: Use Poetry's venv Python directly
    # (bypasses 'poetry run' system Python check)
    # Wrap in cmd.exe /k to keep the terminal window open after execution
    # Note: When passing as a list, cmd.exe doesn't need quotes around
    # paths with spaces
    if platform.system() == "Windows":
        cmd = [
            "cmd.exe",
            "/k",
            str(venv_python),
            str(start_script)
        ]
    elif platform.system() == "Darwin":
        # get path to run_in_iterm.sh
        script_path = this_filepath.parent / "run_in_iterm.sh"
        cmd = [
            str(script_path),
            f"{venv_python} {start_script}"
        ]
    else:
        cmd = [
            "zsh",
            "-c",
            f"{venv_python} {start_script}"
        ]

    log.info("=" * 70)
    log.info("AYON Launcher Dev Mode")
    log.info("=" * 70)
    log.info("Working directory: %s", launcher_root)
    log.info("Venv Python: %s", venv_python)
    log.info("Python executable (from .env): %s", python_executable)
    log.info("Start script: %s", start_script)
    log.info("Command: %s", " ".join(cmd))
    log.info("=" * 70)
    log.info("")
    log.info("Launching in new terminal window...")
    log.info("The terminal will STAY OPEN after execution.")
    log.info("You can see any errors and close it manually when done.")
    log.info("")

    # Launch in a new console window
    # Use CREATE_NEW_CONSOLE to open detached terminal
    creation_flags = (
        0x00000010 if platform.system() == "Windows" else 0  # CREATE_NEW_CONSOLE
    )

    subprocess.Popen(
        cmd,
        cwd=str(launcher_root),
        env=env,
        creationflags=creation_flags,
    )

    log.info("\u2713 AYON Launcher started successfully!")




if __name__ == "__main__":
    launcher_dev_mode()
