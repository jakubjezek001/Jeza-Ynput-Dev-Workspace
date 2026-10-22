#!/usr/bin/env python

"""Report workspace linkage drift across repos — ``status``.

Checks, for each repo, exactly what ``ayon-workspace link`` is supposed to
have set up: an absolute ``core.hooksPath``, the ``.zed`` symlink resolving
to the expected target, and hidden from ``git status`` via
``.git/info/exclude`` — all read-only, this subcommand never writes
anything.

Script usage:
  uv run ayon-workspace status [--repo PATH ...] [--all]
"""

import logging
import subprocess
from pathlib import Path

import click

from .workspace_common import (
    is_tracked,
    resolve_target_repos,
    resolve_workspace_root,
)

# Imported rather than duplicated, so ``link`` and ``status`` never drift.
from .workspace_link import LINKS


def _check_hooks_path(repo: Path, root: Path) -> str:
    """Return a drift message for ``core.hooksPath``, or "" if correct."""
    expected = root / ".githooks-shared"
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    )
    configured = result.stdout.strip()
    if configured != str(expected):
        return (
            f"core.hooksPath is '{configured or '(unset)'}', expected "
            f"'{expected}' (absolute)"
        )
    return ""


def _check_link(
    repo: Path, name: str, relative_target: str, log: logging.Logger
) -> str:
    """Return a drift message for one symlink, or "" if correct.

    Args:
        repo (Path): repository being checked.
        name (str): the symlink's name inside the repo, e.g. ``.zed``.
        relative_target (str): expected symlink target (from ``LINKS``).
        log (logging.Logger): logger for informational (non-drift) notes.

    Returns:
        str: a human-readable drift description, or "" if all is well.
    """
    if is_tracked(repo, name):
        log.info(
            f"{repo.name}: {name} is tracked by git, link skipped by design"
        )
        return ""

    link_path = repo / name
    expected_resolved = (link_path.parent / relative_target).resolve()

    if not link_path.is_symlink():
        return f"{name} is missing or not a symlink"
    if link_path.resolve() != expected_resolved:
        return f"{name} -> {link_path.resolve()}, expected {expected_resolved}"

    check_ignore = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-v", name],
        capture_output=True,
        text=True,
        check=False,
    )
    if check_ignore.returncode != 0:
        return f"{name} resolves but is not check-ignore'd"
    return ""


def check_repo(repo: Path, root: Path, log: logging.Logger) -> list:
    """Return the list of drift descriptions for ``repo`` (empty = clean).

    Args:
        repo (Path): repository to check.
        root (Path): resolved workspace root.
        log (logging.Logger): logger for informational notes.

    Returns:
        list[str]: human-readable drift descriptions.
    """
    problems = []

    hooks_problem = _check_hooks_path(repo, root)
    if hooks_problem:
        problems.append(hooks_problem)

    for name, relative_target in LINKS.items():
        link_problem = _check_link(repo, name, relative_target, log)
        if link_problem:
            problems.append(link_problem)

    return problems


@click.command(name="status")
@click.option(
    "--repo",
    "repos",
    multiple=True,
    type=click.Path(),
    help="Repo path (repeatable).",
)
@click.option(
    "--all", "use_all", is_flag=True, help="Check every repo in SCOPE_REPOS."
)
def status(repos: tuple, use_all: bool) -> None:
    """Print workspace linkage status for the given (or all) repos.

    Args:
        repos (tuple): explicit ``--repo`` paths to check.
        use_all (bool): if set, check every repo in ``SCOPE_REPOS``.

    Raises:
        SystemExit: with code 1 if any repo has drift; not raised (normal
            exit 0) if every repo is clean.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("status")

    root = resolve_workspace_root()
    targets = resolve_target_repos(root, repos, use_all)

    any_drift = False
    for target in targets:
        problems = check_repo(target, root, log)
        if problems:
            any_drift = True
            log.info(f"{target.name}: DRIFT")
            for problem in problems:
                log.info(f"  - {problem}")
        else:
            log.info(f"{target.name}: OK")

    if any_drift:
        raise SystemExit(1)


if __name__ == "__main__":
    status()
