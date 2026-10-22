#!/usr/bin/env python

"""Bootstrap a brand-new workspace root from scratch.

This is the single command a brand-new, empty workspace folder needs to
reach a working state: ``uv run ayon-workspace bootstrap``. It never
reimplements any of the individual steps — it only sequences the existing,
already-idempotent building blocks:

1. Preflight — assert ``git``/``uv`` are on ``PATH`` (hard requirement);
   warn, don't fail, if ``zed`` is missing (the global tasks are still
   writable).
2. Resolve ``<NEW_ROOT>`` (``--root``, else ``$AYON_WORKSPACE_ROOT``, else
   cwd); refuse to run against ``$HOME`` or ``/``.
3. Clone the default repos (or ``--all`` for the full ~40) via
   ``git_clone_all_repos.clone_repos`` — reused, not reimplemented.
4. ``install-global`` — the global Zed tasks.
5. ``link`` every in-scope repo on disk (``.zed`` symlink + shared hook).
6. ``doctor`` — fail loudly with a per-check report if anything is off.

Every step honours ``--dry-run``; the whole command is idempotent.

Script usage:
  uv run ayon-workspace bootstrap [--root PATH] [--dry-run] [--skip-clone]
      [--all]
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

import click

from .git_clone_all_repos import ALL_REPOS, clone_repos
from .workspace_common import DEFAULT_CLONE_REPOS, SCOPE_REPOS
from .workspace_doctor import run_doctor
from .workspace_install_global import install_global
from .workspace_link import link_one

# Tools this command needs; "hard" ones abort bootstrap if missing, "soft"
# ones only produce a warning (the global tasks are still writable).
HARD_REQUIREMENTS = ["git", "uv"]
SOFT_REQUIREMENTS = ["zed"]


def _tool_version(tool: str) -> str:
    """Best-effort ``<tool> --version`` for the preflight report.

    Args:
        tool (str): executable name.

    Returns:
        str: first line of its ``--version`` output, or ``"unknown"``.
    """
    result = subprocess.run(
        [tool, "--version"], capture_output=True, text=True, check=False
    )
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else "unknown"


def _preflight(log: logging.Logger) -> None:
    """Assert hard requirements, warn on missing soft ones.

    Args:
        log (logging.Logger): logger to report progress on.

    Raises:
        click.ClickException: if a hard requirement is missing.
    """
    for tool in HARD_REQUIREMENTS:
        if shutil.which(tool) is None:
            raise click.ClickException(
                f"'{tool}' is not on PATH — required to bootstrap."
            )
        log.info(f"{tool}: {_tool_version(tool)}")

    for tool in SOFT_REQUIREMENTS:
        if shutil.which(tool) is None:
            log.warning(
                f"'{tool}' is not on PATH — the global tasks will still "
                f"be written, but you need {tool} to use them."
            )
        else:
            log.info(f"{tool}: {_tool_version(tool)}")


def _resolve_new_root(root_option: str) -> Path:
    """Resolve ``<NEW_ROOT>`` and refuse dangerous targets.

    Args:
        root_option (str): the ``--root`` CLI value (may be empty).

    Returns:
        Path: absolute, resolved target workspace root.

    Raises:
        click.ClickException: if the resolved root is ``$HOME`` or ``/``.
    """
    candidate = (
        root_option
        or os.environ.get("AYON_WORKSPACE_ROOT")
        or os.getcwd()
    )
    root = Path(candidate).expanduser().resolve()

    if root in (Path.home(), Path("/")):
        raise click.ClickException(
            f"Refusing to bootstrap directly into '{root}' — pass an "
            f"explicit, dedicated --root."
        )
    return root


@click.command(name="bootstrap")
@click.option(
    "--root",
    "root_option",
    default="",
    type=click.Path(),
    help="Target workspace root (default: $AYON_WORKSPACE_ROOT or cwd).",
)
@click.option(
    "--dry-run", is_flag=True, help="Print the plan without writing anything."
)
@click.option("--skip-clone", is_flag=True, help="Skip the repo-cloning step.")
@click.option(
    "--all",
    "use_all",
    is_flag=True,
    help="Clone the full ~40-repo set instead of the default ten.",
)
def bootstrap(
    root_option: str, dry_run: bool, skip_clone: bool, use_all: bool
) -> None:
    """Bring a brand-new workspace root to a working state.

    Args:
        root_option (str): the ``--root`` CLI value (may be empty).
        dry_run (bool): if set, print the plan without writing anything.
        skip_clone (bool): if set, skip step 3 (cloning repos).
        use_all (bool): if set, clone the full ~40-repo set instead of
            the default ten.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("bootstrap")

    log.info("=== 1. Preflight ===")
    _preflight(log)

    root = _resolve_new_root(root_option)
    log.info(f"=== 2. Target workspace root: {root} ===")
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)

    # Every downstream subcommand resolves <ROOT> from this override
    # (workspace_common.resolve_workspace_root) — set once here so bootstrap
    # can target a root other than its own installed location (the Zed-task
    # case).
    os.environ["AYON_WORKSPACE_ROOT"] = str(root)

    log.info("=== 3. Clone repos ===")
    if skip_clone:
        log.info("--skip-clone set, not cloning anything")
    else:
        target_list = ALL_REPOS if use_all else DEFAULT_CLONE_REPOS
        clone_repos(root, target_list, dry_run=dry_run)

    log.info("=== 4. Install global Zed tasks ===")
    install_global.callback(dry_run=dry_run)

    log.info("=== 5. Link repos ===")
    for name in SCOPE_REPOS:
        repo = root / name
        if repo.is_dir():
            link_one(repo, root, dry_run, log)
        else:
            log.info(f"{name}: not on disk, skipping link")

    log.info("=== 6. Doctor ===")
    if dry_run:
        log.info("[dry-run] would run `ayon-workspace doctor`")
        return

    problems = run_doctor(root, log)
    if problems:
        log.info("")
        log.info("BOOTSTRAP: DOCTOR FOUND PROBLEMS")
        for problem in problems:
            log.info(f"  - {problem}")
        raise SystemExit(1)

    log.info("")
    log.info("BOOTSTRAP: complete, doctor is clean.")


if __name__ == "__main__":
    bootstrap()
