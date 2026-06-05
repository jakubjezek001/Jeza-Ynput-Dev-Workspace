"""Launch AYON Application

Interactive launcher for AYON-managed DCC applications (Nuke, Fusion, Flame, …).
Uses the ayon-launcher venv Python to run start.py with the
'addon applications launch' CLI subcommand — the same mechanism as
launcher_dev_mode.py.

Aligned with launcher_dev_mode.py:
  - Reads env vars from .env via python-dotenv
  - Uses the Poetry venv Python from ayon-launcher/.venv
  - Opens in a new terminal window (iTerm on macOS, cmd.exe on Windows, zsh on Linux)

When --app is omitted an interactive numbered menu is displayed so you can
choose which DCC to open without editing any config.
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

load_dotenv()

workspace_dir = Path(__file__).resolve().parent.parent.parent
this_filepath = Path(__file__).resolve()

# ---------------------------------------------------------------------------
# Configure available apps — edit this list to match your AYON setup.
# Format: {"name": "<Display Name>", "key": "<ayon_app_name>/<version>"}
# ---------------------------------------------------------------------------
AVAILABLE_APPS = {
    "comp": [
        {"name": "Nuke 15.2", "key": "nuke/15-2"},
        {"name": "Nuke 16.1", "key": "nuke/16-1"},
        {"name": "Nuke 17.0", "key": "nuke/17-0"},
        {"name": "Photoshop 2026", "key": "photoshop/2026"},
    ],
    "conform": [
        {"name": "Hiero 15.2", "key": "hiero/15-2"},
        {"name": "Hiero 16.1", "key": "hiero/16-1"},
        {"name": "Hiero 17.0", "key": "hiero/17-0"},
        {"name": "Flame 2026.2", "key": "flame/2026-2"},
        {"name": "Resolve stable", "key": "resolve/stable"},
    ]
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_env_vars(log: logging.Logger) -> str:
    """Validate required environment variables and return python_executable."""
    required_env_vars = [
        "PYTHON_EXECUTABLE",
        "AYON_SERVER_URL",
        "AYON_USE_DEV",
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


def _select_app(
    preselected: Optional[str], task: str, log: logging.Logger) -> str:
    """Show an interactive numbered menu and return the chosen app key.

    If ``preselected`` is provided it is used directly, allowing non-interactive
    calls (e.g. ``uv run ayon-launch-app --app nuke/15-2 ...``).
    """
    if preselected:
        log.info("App:      %s  (pre-selected via --app)", preselected)
        return preselected

    print()
    print("  Available applications:")
    print()
    for i, app in enumerate(AVAILABLE_APPS.get(task, []), 1):
        print(f"  {i}.  {app['name']:<15}  ({app['key']})")
    print()

    while True:
        try:
            raw = input(
                f"  Select [1-{len(AVAILABLE_APPS[task])}]: ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(AVAILABLE_APPS[task]):
                print()
                return AVAILABLE_APPS[task][idx]["key"]
            print(f"  Enter a number between 1 and {len(AVAILABLE_APPS.get(task, []))}.")
        except ValueError:
            print("  Invalid input — please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print()
            log.info("Cancelled.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--app",
    default=None,
    help=(
        "App key, e.g. 'nuke/15-2'. "
        "Omit to get an interactive selector."
    ),
)
@click.option("--project", required=True, help="AYON project name.")
@click.option(
    "--folder",
    required=True,
    help="Folder path within the project (e.g. shots/sq001/sh010).",
)
@click.option("--task", required=True, help="Task name (e.g. comp).")
def launch_ayon_app(
    app: Optional[str],
    project: str,
    folder: str,
    task: str,
) -> None:
    """Launch an AYON-managed DCC application via the ayon-launcher venv."""
    level = logging.INFO
    logging.basicConfig(level=level)
    log = logging.getLogger("ayon-launch-app")

    python_executable = _validate_env_vars(log)

    launcher_root = workspace_dir / "ayon-launcher"
    poetry_venv = launcher_root / ".venv"

    if platform.system() == "Windows":
        venv_python = poetry_venv / "Scripts" / "python.exe"
    else:
        venv_python = poetry_venv / "bin" / "python3"
    start_script = launcher_root / "start.py"

    _verify_paths(log, launcher_root, venv_python, start_script, python_executable)

    log.info("=" * 70)
    log.info("AYON Application Launcher")
    log.info("=" * 70)
    log.info("Project:  %s", project)
    log.info("Folder:   %s", folder)
    log.info("Task:     %s", task)

    # Interactive (or direct) app selection
    selected_app = _select_app(app, task, log)
    log.info("App:      %s", selected_app)
    log.info("=" * 70)

    # Build core launch command using the ayon-launcher venv Python
    launch_args = [
        str(venv_python),
        str(start_script),
        "addon", "applications", "launch",
        "--app", selected_app,
        "--folder", folder,
        "--project", project,
        "--task", task,
    ]

    # Inherit full env, strip the API key (mirrors launcher_dev_mode.py)
    env = os.environ.copy()
    env.pop("AYON_API_KEY", None)
    env["PYTHON_EXECUTABLE"] = python_executable

    # Wrap in a platform-appropriate terminal window (mirrors launcher_dev_mode.py)
    if platform.system() == "Windows":
        cmd = ["cmd.exe", "/k"] + launch_args
    elif platform.system() == "Darwin":
        iterm_script = this_filepath.parent / "run_in_iterm.sh"
        cmd = [str(iterm_script), " ".join(launch_args)]
    else:
        cmd = ["zsh", "-c", " ".join(launch_args)]

    log.info("Launching in new terminal window...")
    log.info("Command: %s", " ".join(str(a) for a in launch_args))
    log.info("")

    creation_flags = (
        0x00000010 if platform.system() == "Windows" else 0  # CREATE_NEW_CONSOLE
    )

    subprocess.Popen(
        cmd,
        cwd=str(launcher_root),
        env=env,
        creationflags=creation_flags,
    )

    log.info(
        "\u2713 %s launch initiated!  (project: %s / folder: %s / task: %s)",
        selected_app, project, folder, task,
    )


if __name__ == "__main__":
    launch_ayon_app()
