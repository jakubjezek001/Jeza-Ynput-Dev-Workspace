#!/usr/bin/env python

"""Assert every workspace invariant on this machine — ``doctor``.

Read-only — ``doctor`` never writes anything, and is also the final step of
``ayon-workspace bootstrap``.

Checks:

- ``~/.config/zed/tasks.json`` exists and parses as JSON.
- Per in-scope repo present on disk: the linkage is clean (reuses
  ``workspace_status.check_repo`` — one definition, no drift between
  ``status`` and ``doctor``).

Script usage:
  uv run ayon-workspace doctor
"""

import json
import logging
from pathlib import Path
from typing import List

import click

from .workspace_common import SCOPE_REPOS, resolve_workspace_root
from .workspace_status import check_repo


def _check_global_tasks_json(log: logging.Logger) -> List[str]:
    """Return drift messages for ``~/.config/zed/tasks.json``."""
    path = Path.home() / ".config" / "zed" / "tasks.json"
    if not path.is_file():
        return [f"{path} is missing — run `ayon-workspace install-global`"]
    try:
        json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{path} does not parse as JSON: {exc}"]
    log.info(f"{path}: OK (parses)")
    return []


def _check_repo_linkage(root: Path, log: logging.Logger) -> List[str]:
    """Return drift messages for every in-scope repo present on disk."""
    problems = []
    for name in SCOPE_REPOS:
        repo = root / name
        if not repo.is_dir():
            log.info(f"{name}: not on disk, skipping linkage check")
            continue
        repo_problems = check_repo(repo, root, log)
        for problem in repo_problems:
            problems.append(f"{name}: {problem}")
        if not repo_problems:
            log.info(f"{name}: linkage OK")
    return problems


def run_doctor(root: Path, log: logging.Logger) -> List[str]:
    """Run every doctor check and return the combined list of problems.

    Args:
        root (Path): resolved workspace root.
        log (logging.Logger): logger to report progress on.

    Returns:
        List[str]: human-readable problem descriptions; empty means clean.
    """
    problems: List[str] = []
    problems += _check_global_tasks_json(log)
    problems += _check_repo_linkage(root, log)
    return problems


@click.command(name="doctor")
def doctor() -> None:
    """Assert every workspace invariant on this machine; exit 1 on drift.

    Raises:
        SystemExit: with code 1 if any check fails; otherwise exits 0.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("doctor")

    root = resolve_workspace_root()
    log.info(f"Workspace root: {root}")

    problems = run_doctor(root, log)

    if problems:
        log.info("")
        log.info("DOCTOR: FAIL")
        for problem in problems:
            log.info(f"  - {problem}")
        raise SystemExit(1)

    log.info("")
    log.info("DOCTOR: OK — every check passed.")


if __name__ == "__main__":
    doctor()
