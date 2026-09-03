#!/usr/bin/env python

"""Assert every §2 invariant this plan depends on — Phase D5 ``doctor``.

This is the regression suite for the whole plan (D5): every cheaply-testable
invariant from §2/§7 becomes one check here, so drift is *detected*, not
*discovered*. Read-only — ``doctor`` never writes anything, and is also the
final step of ``ayon-sdd bootstrap`` (G3 step 8) and the acceptance gate of
the Phase G clean-folder proof (G5).

Checks:

- ``~/.config/zed/tasks.json`` parses as JSON (A1).
- ``~/.config/zed/AGENTS.md`` and ``~/.config/goose/AGENTS.md`` exist (A2/A3).
- The central repo (``ayon-agentic-instructions``) is present at ``<ROOT>``.
- Per in-scope repo present on disk: L2 linkage is clean (reuses
  ``sdd_status.check_repo`` — one definition, no drift between ``status``
  and ``doctor``).
- ``goose skills list`` (run from the first available in-scope repo) lists
  the shared skills (N1 regression test) — best-effort: warns instead of
  failing if ``goose`` itself is not installed on this machine.

Script usage:
  uv run ayon-sdd doctor
  uv run ayon-sdd-doctor
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import List

import click

from .sdd_common import CENTRAL_REPO, SCOPE_REPOS, resolve_workspace_root
from .sdd_install_global import SHARED_SKILLS
from .sdd_status import check_repo


def _check_global_tasks_json(log: logging.Logger) -> List[str]:
    """Return drift messages for ``~/.config/zed/tasks.json`` (A1)."""
    path = Path.home() / ".config" / "zed" / "tasks.json"
    if not path.is_file():
        return [f"{path} is missing — run `ayon-sdd install-global`"]
    try:
        json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{path} does not parse as JSON: {exc}"]
    log.info(f"{path}: OK (parses)")
    return []


def _check_global_agents_md(log: logging.Logger) -> List[str]:
    """Return drift messages for the global L0 AGENTS.md files (A2/A3)."""
    problems = []
    zed_path = Path.home() / ".config" / "zed" / "AGENTS.md"
    goose_path = Path.home() / ".config" / "goose" / "AGENTS.md"
    if not zed_path.is_file():
        problems.append(
            f"{zed_path} is missing — run `ayon-sdd install-global`"
        )
    if not goose_path.is_file():
        problems.append(
            f"{goose_path} is missing — run `ayon-sdd install-global`"
        )
    if not problems:
        log.info(f"{zed_path} and {goose_path}: OK")
    return problems


def _check_central_repo(root: Path, log: logging.Logger) -> List[str]:
    """Return drift messages for the L1 central repo checkout."""
    central = root / CENTRAL_REPO
    if not central.is_dir():
        return [f"{central} is missing — run `ayon-sdd bootstrap`"]
    log.info(f"{central}: OK (present)")
    return []


def _check_goose_skills(root: Path, log: logging.Logger) -> List[str]:
    """Return drift messages for the shared-skills regression test (N1)."""
    if shutil.which("goose") is None:
        log.warning("goose not on PATH — skipping shared-skills check")
        return []

    sample_repo = next(
        (root / name for name in SCOPE_REPOS if (root / name).is_dir()), None
    )
    if sample_repo is None:
        log.warning("No in-scope repo on disk — skipping shared-skills check")
        return []

    result = subprocess.run(
        ["goose", "skills", "list"],
        cwd=str(sample_repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"`goose skills list` failed: {result.stderr.strip()}"]

    missing = [name for name in SHARED_SKILLS if name not in result.stdout]
    if missing:
        names = ", ".join(missing)
        return [f"goose skills list is missing shared skill(s): {names}"]
    log.info(f"goose skills list (from {sample_repo.name}): OK")
    return []


def _check_repo_linkage(root: Path, log: logging.Logger) -> List[str]:
    """Return drift messages for every in-scope repo present on disk (D5)."""
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
    problems += _check_global_agents_md(log)
    problems += _check_central_repo(root, log)
    problems += _check_repo_linkage(root, log)
    problems += _check_goose_skills(root, log)
    return problems


@click.command(name="doctor")
def doctor() -> None:
    """Assert every §2/§7 invariant on this machine; exit 1 on any drift.

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
