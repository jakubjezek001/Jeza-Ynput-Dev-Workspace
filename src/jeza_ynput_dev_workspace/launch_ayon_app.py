"""Launch AYON addon commands via the ayon-launcher venv.

A universal wrapper that handles env validation, path verification, and
platform-appropriate terminal spawning for *any* AYON addon subcommand.
All arguments are passed through verbatim to start.py with one enhancement:
when the command is ``addon applications launch`` and --app is absent, an
interactive numbered menu lets you pick the DCC without editing tasks.json.

Aligned with launcher_dev_mode.py:
  - Reads env vars from .env via python-dotenv
  - Uses the Poetry venv Python from ayon-launcher/.venv
  - Opens in a new terminal window (iTerm on macOS, cmd.exe on Windows, zsh on Linux)

Examples (as tasks.json "args" values)::

    ["addon", "applications", "launch",
     "--project", "AY01_VFX_demo", "--folder", "shots/sq001/sh010", "--task", "comp"]

    ["addon", "traypublisher", "launch",
     "--project", "AY01_VFX_demo", "--folder-path", "/editorial", "--task-name", "edit"]
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

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

def _get_arg_value(args: List[str], flag: str) -> Optional[str]:
    """Return the value following *flag* in *args*, or None.

    Handles both ``--flag value`` and ``--flag=value`` forms.
    """
    for i, arg in enumerate(args):
        if arg == flag and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1]
    return None


def _has_flag(args: List[str], flag: str) -> bool:
    """Return True if *flag* (or ``*flag*=...") appears anywhere in *args*."""
    return any(arg == flag or arg.startswith(f"{flag}=") for arg in args)


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


def _select_app(task: Optional[str], log: logging.Logger) -> str:
    """Show an interactive numbered menu and return the chosen app key.

    Filters by *task* when recognised in AVAILABLE_APPS; otherwise shows
    all apps combined as a flat list.
    """
    apps = AVAILABLE_APPS.get(task or "", [])
    if not apps:
        apps = [app for group in AVAILABLE_APPS.values() for app in group]
        if task:
            log.warning(
                "Task '%s' not found in AVAILABLE_APPS — showing all apps.", task
            )

    print()
    print("  Available applications:")
    print()
    for i, app in enumerate(apps, 1):
        print(f"  {i}.  {app['name']:<20}  ({app['key']})")
    print()

    while True:
        try:
            raw = input(f"  Select [1-{len(apps)}]: ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(apps):
                print()
                return apps[idx]["key"]
            print(f"  Enter a number between 1 and {len(apps)}.")
        except ValueError:
            print("  Invalid input — please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print()
            log.info("Cancelled.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@click.command(
    context_settings=dict(allow_extra_args=True, ignore_unknown_options=True)
)
@click.argument("addon_args", nargs=-1, type=click.UNPROCESSED)
def launch_ayon_app(addon_args: tuple) -> None:
    """Launch any AYON addon command via the ayon-launcher venv.

    Pass the full addon subcommand and its arguments directly after the
    command name. The script handles env validation, path verification,
    and platform-appropriate terminal spawning.

    \b
    Examples:
        uv run ayon-launch-app addon applications launch \\
            --project AY01_VFX_demo --folder shots/sq001/sh010 --task comp

        uv run ayon-launch-app addon traypublisher launch \\
            --project AY01_VFX_demo --folder-path /editorial --task-name edit

    For 'addon applications launch' without --app an interactive DCC selector
    is shown, filtered by --task name when recognised in AVAILABLE_APPS.
    """
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

    args_list = list(addon_args)

    if not args_list:
        log.error("No addon subcommand provided.")
        log.error(
            "Example: uv run ayon-launch-app addon applications launch "
            "--project PROJ --folder shots/sh010 --task comp"
        )
        sys.exit(1)

    # -- Interactive app selector ------------------------------------------------
    # Activates only for `addon applications launch` when --app is absent.
    is_app_launch = (
        args_list[:3] == ["addon", "applications", "launch"]
        and not _has_flag(args_list, "--app")
    )
    if is_app_launch:
        task_name = _get_arg_value(args_list, "--task")
        selected_app = _select_app(task_name, log)
        args_list += ["--app", selected_app]

    # -- Logging header ----------------------------------------------------------
    log.info("=" * 70)
    log.info("AYON Launcher")
    log.info("=" * 70)
    log.info("Subcommand:    %s", " ".join(args_list[:3]))
    for flag in ("--project", "--folder", "--folder-path", "--task", "--task-name", "--app"):
        val = _get_arg_value(args_list, flag)
        if val:
            log.info("%-16s %s", flag + ":", val)
    log.info("=" * 70)

    # -- Build and spawn ---------------------------------------------------------
    launch_args = [str(venv_python), str(start_script)] + args_list

    env = os.environ.copy()
    env.pop("AYON_API_KEY", None)
    env["PYTHON_EXECUTABLE"] = python_executable

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

    log.info("\u2713 Launch initiated!")


if __name__ == "__main__":
    launch_ayon_app()
