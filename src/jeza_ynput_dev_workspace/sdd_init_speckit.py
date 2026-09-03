#!/usr/bin/env python

"""Install Spec Kit into an in-scope repo — Phase C2, reused by bootstrap G3.

Runs ``specify init`` for the four integrations verified to stack cleanly
(S2) — ``goose``, ``zed``, ``copilot``, ``kilocode`` — then points
``.specify/memory/constitution.md`` at the single AYON constitution authored
in the central repo (``ayon-agentic-instructions/memory/ayon-constitution.md``,
Phase B2) via a relative symlink, instead of a copy, so the two never drift.

Every write is guarded by the §6 D1 branch assertion
(``sdd_common.assert_branch``): **never** switch branches, only stop and
report on a mismatch. This module never creates or checks out a branch
itself — that is ``ayon-sdd bootstrap``'s job (via
``sdd_common.ensure_branch``), and only ever for a repo it just cloned fresh.

Script usage:
  uv run ayon-sdd init-speckit [--repo PATH ...] [--all] [--dry-run]
  uv run ayon-sdd-init-speckit [--repo PATH ...] [--all] [--dry-run]
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

import click

from .sdd_common import (
    assert_branch,
    resolve_target_repos,
    resolve_workspace_root,
)

# The four Spec Kit integrations verified to stack cleanly in one repo (S2).
INTEGRATIONS = ["goose", "zed", "copilot", "kilocode"]

CONSTITUTION_RELATIVE_TARGET = "../../.agents-main/memory/ayon-constitution.md"


def _integration_installed(repo: Path, integration: str) -> bool:
    """Return whether ``specify init --integration <integration>`` already
    ran in ``repo`` (idempotency check).

    Args:
        repo (Path): repository being set up.
        integration (str): integration name, e.g. ``goose``.

    Returns:
        bool: True if the integration's manifest is already present.
    """
    manifest = (
        repo / ".specify" / "integrations" / f"{integration}.manifest.json"
    )
    return manifest.is_file()


def _run_specify_init(
    repo: Path,
    integration: str,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently run ``specify init`` for one integration.

    Args:
        repo (Path): repository to install Spec Kit into.
        integration (str): integration name, e.g. ``goose``.
        dry_run (bool): if set, only log the planned command.
        log (logging.Logger): logger to report progress on.

    Raises:
        click.ClickException: if the ``specify`` CLI is not on ``PATH``, or
            the command fails.
    """
    if _integration_installed(repo, integration):
        log.info(f"{repo.name}: {integration} integration already installed")
        return

    if shutil.which("specify") is None:
        message = (
            "'specify' is not on PATH. Install it with "
            "`uv tool install specify-cli` (Phase C2) and retry."
        )
        raise click.ClickException(message)

    command = [
        "specify", "init", ".", "--here", "--force",
        "--non-interactive", "--integration", integration,
        "--ignore-agent-tools",
    ]
    if dry_run:
        log.info(f"[dry-run] {repo.name}: would run {' '.join(command)}")
        return

    result = subprocess.run(
        command, cwd=str(repo), capture_output=True, text=True
    )
    if result.returncode != 0:
        message = (
            f"{repo.name}: `specify init` failed for '{integration}':\n"
            f"{result.stdout}\n{result.stderr}"
        )
        raise click.ClickException(message)
    log.info(f"{repo.name}: installed {integration} integration")


def _link_constitution(repo: Path, dry_run: bool, log: logging.Logger) -> None:
    """Point ``.specify/memory/constitution.md`` at the AYON constitution.

    Uses a relative symlink
    (``../../.agents-main/memory/ayon-constitution.md``) so it keeps
    resolving through the repo's own ``.agents-main`` symlink (Phase D2)
    rather than a hardcoded absolute path (§0 rule 5b).

    Args:
        repo (Path): repository whose ``.specify/memory/`` to update.
        dry_run (bool): if set, only log the planned change.
        log (logging.Logger): logger to report progress on.
    """
    link_path = repo / ".specify" / "memory" / "constitution.md"
    if not link_path.parent.is_dir():
        log.warning(
            f"{repo.name}: {link_path.parent} missing, run specify init first"
        )
        return

    if link_path.is_symlink() and os.readlink(link_path) == (
        CONSTITUTION_RELATIVE_TARGET
    ):
        log.info(f"{repo.name}: constitution already symlinked")
        return

    if dry_run:
        log.info(
            f"[dry-run] {repo.name}: would symlink constitution.md -> "
            f"{CONSTITUTION_RELATIVE_TARGET}"
        )
        return

    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(CONSTITUTION_RELATIVE_TARGET)
    log.info(
        f"{repo.name}: symlinked constitution.md -> "
        f"{CONSTITUTION_RELATIVE_TARGET}"
    )


def init_speckit_one(repo: Path, dry_run: bool, log: logging.Logger) -> None:
    """Install Spec Kit into a single in-scope repo (C2).

    Args:
        repo (Path): repository to set up.
        dry_run (bool): if set, only log the planned changes.
        log (logging.Logger): logger to report progress on.

    Raises:
        click.ClickException: if ``repo`` is not on its §6 D1 branch.
    """
    assert_branch(repo)
    for integration in INTEGRATIONS:
        _run_specify_init(repo, integration, dry_run, log)
    _link_constitution(repo, dry_run, log)


@click.command(name="init-speckit")
@click.option(
    "--repo",
    "repos",
    multiple=True,
    type=click.Path(),
    help="Repo path (repeatable).",
)
@click.option(
    "--all",
    "use_all",
    is_flag=True,
    help="Install into every repo in SCOPE_REPOS.",
)
@click.option(
    "--dry-run", is_flag=True, help="Print the plan without writing anything."
)
def init_speckit(repos: tuple, use_all: bool, dry_run: bool) -> None:
    """Install Spec Kit (4 integrations + constitution symlink) per repo.

    Args:
        repos (tuple): explicit ``--repo`` paths.
        use_all (bool): if set, install into every repo in ``SCOPE_REPOS``.
        dry_run (bool): if set, print the plan without writing anything.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("init_speckit")

    root = resolve_workspace_root()
    targets = resolve_target_repos(root, repos, use_all)
    for target in targets:
        init_speckit_one(target, dry_run, log)


if __name__ == "__main__":
    init_speckit()
