#!/usr/bin/env python

"""Shared tables and helpers for the ``ayon-workspace`` subcommands.

Centralises workspace-root resolution and the repo scope tables so that
``link``, ``unlink``, ``status``, ``doctor`` and ``worktree-setup`` share one
definition instead of drifting copies of the same constants.
"""

import os
import subprocess
from pathlib import Path

import click

# The repos ``--all`` wires with the workspace linkage (``.zed/tasks.json``
# symlink and the shared ``post-checkout`` hook). Any other repo can still be
# linked explicitly with ``--repo PATH``.
SCOPE_REPOS = [
    "ayon-core",
    "ayon-launcher",
    "ayon-traypublisher",
    "ayon-batch-delivery",
    "ayon-batch-ingest",
    "ayon-hiero",
    "ayon-resolve",
    "ayon-flame",
    "ayon-editorial",
    "ayon-nuke",
    "ayon-maya",
    "ayon-deadline",
    "ayon-slater",
    "ayon-tvpaint",
    "ayon-harmony",
    "ayon-photoshop",
    "ayon-ftrack",
    "ayon-shotgrid",
    "ayon-openrv",
]

# Server repos that are needed on disk as read-only local infra but must
# never be linked or written to (see docs/workspace.md).
FORBIDDEN_REPOS = ["ayon-backend", "ayon-frontend", "ayon-docker"]

# What ``ayon-workspace bootstrap`` clones by default: the linked repos plus
# the read-only server repos. ``--all`` instead reuses the full
# ``git_clone_all_repos`` list.
DEFAULT_CLONE_REPOS = SCOPE_REPOS + FORBIDDEN_REPOS


def resolve_workspace_root() -> Path:
    """Resolve ``<ROOT>``, preferring an explicit override.

    Never hardcodes a home directory: the ``AYON_WORKSPACE_ROOT`` environment
    variable always wins, otherwise the root is derived from this package's
    own location on disk (three levels up from this file).

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
            f"Refusing to operate on '{repo.name}' — it is a read-only "
            f"server repo (docs/workspace.md)."
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

    Used to refuse touching a path that is already tracked by git — the
    linkage only ever adds *untracked, gitignored-via-info/exclude*
    symlinks; it must never silently convert a committed file/dir into a
    symlink, which would require an unauthorized commit.

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
