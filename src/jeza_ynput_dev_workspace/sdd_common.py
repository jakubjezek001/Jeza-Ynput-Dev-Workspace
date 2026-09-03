#!/usr/bin/env python

"""Shared tables and helpers for the ``ayon-sdd`` subcommands (Phase D+).

Centralises workspace-root resolution and the repo scope tables so that
``link``, ``unlink``, ``status`` and ``worktree-setup`` share one definition
instead of drifting copies of the same constants (see
``IMPLEMENTATION-PLAN.md`` D5: *"the hook and the Zed task must both be thin
wrappers ... do not let them grow independent copies of the same logic"* —
the same principle applies to the subcommands that back them).
"""

import os
import subprocess
from pathlib import Path

import click

# The seven repos Phase D wires with L2 linkage (IMPLEMENTATION-PLAN.md §6 D1).
SCOPE_REPOS = [
    "ayon-batch-delivery",
    "ayon-flame",
    "ayon-resolve",
    "ayon-hiero",
    "ayon-core",
    "ayon-launcher",
    "ayon-nuke",
]

# Repos this plan must never touch (IMPLEMENTATION-PLAN.md §1).
FORBIDDEN_REPOS = ["ayon-backend", "ayon-frontend", "ayon-docker"]

# The central repo linked *into* every scope repo; it is never linked itself.
CENTRAL_REPO = "ayon-agentic-instructions"


def resolve_workspace_root() -> Path:
    """Resolve ``<ROOT>``, preferring an explicit override.

    Never hardcodes a home directory: the ``AYON_WORKSPACE_ROOT`` environment
    variable always wins, otherwise the root is derived from this package's
    own location on disk (three levels up from this file), matching
    ``sdd_install_global._resolve_workspace_root``.

    Returns:
        Path: absolute path to the workspace root.
    """
    override = os.environ.get("AYON_WORKSPACE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent.parent


def assert_in_scope(repo: Path) -> None:
    """Refuse to operate on a forbidden or nonexistent repo.

    Args:
        repo (Path): repo directory being targeted.

    Raises:
        click.ClickException: if ``repo`` is one of ``FORBIDDEN_REPOS``, or
            does not exist as a directory.
    """
    if repo.name in FORBIDDEN_REPOS:
        message = (
            f"Refusing to operate on '{repo.name}' — it is permanently "
            f"out of scope (IMPLEMENTATION-PLAN.md \u00a71)."
        )
        raise click.ClickException(message)
    if not repo.is_dir():
        message = f"Not a directory: {repo}"
        raise click.ClickException(message)


def resolve_target_repos(
    root: Path,
    repos: tuple,
    use_all: bool,
) -> list:
    """Resolve the repo paths a subcommand should operate on.

    Args:
        root (Path): resolved workspace root.
        repos (tuple): explicit ``--repo`` paths (may be empty).
        use_all (bool): if set, use every repo in ``SCOPE_REPOS``.

    Returns:
        list[Path]: absolute, validated, in-scope repo paths.

    Raises:
        click.ClickException: if neither ``repos`` nor ``use_all`` is given,
            or a resolved repo is out of scope or missing.
    """
    if use_all:
        targets = [root / name for name in SCOPE_REPOS]
    elif repos:
        targets = [Path(r).expanduser().resolve() for r in repos]
    else:
        message = "Specify --repo PATH (one or more) or --all."
        raise click.ClickException(message)

    for target in targets:
        assert_in_scope(target)
    return targets


def is_tracked(repo: Path, relative_path: str) -> bool:
    """Check whether ``relative_path`` is committed in ``repo``.

    Used to refuse touching a path that is already tracked by git — Phase D
    only ever adds *untracked, gitignored-via-info/exclude* symlinks (G4);
    it must never silently convert a committed file/dir into a symlink,
    which would require an unauthorized commit.

    Args:
        repo (Path): repository to check.
        relative_path (str): path relative to the repo root.

    Returns:
        bool: True if git already tracks ``relative_path``.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--error-unmatch", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0
