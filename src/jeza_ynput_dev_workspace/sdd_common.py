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

# The per-repo branch to commit SDD artifacts on (IMPLEMENTATION-PLAN.md §6
# D1 — binding, do not re-derive). Every writing subcommand (init-speckit,
# doctor) reads this one table instead of hardcoding branch names.
BRANCH_TABLE = {
    "ayon-batch-delivery": "agentic-sdd-dev",
    "ayon-flame": "agentic-sdd-dev",
    "ayon-resolve": "agentic-sdd-dev",
    "ayon-hiero": "agentic-sdd-dev",
    "ayon-core": "agentic-sdd-dev",
    "ayon-launcher": "agentic-sdd-dev",
    "ayon-nuke": "enhancement/developing-agentic-workflow-basic",
}

# G2/D6: the "in-scope ten" `ayon-sdd bootstrap` clones by default — the
# seven §6 D1 repos plus the three permanently out-of-scope repos (needed
# on disk as read-only local infra, e.g. to run the AYON stack, but never
# linked or written to — see FORBIDDEN_REPOS and every subcommand's
# ``assert_in_scope``). ``--all`` instead reuses the full
# ``git_clone_all_repos`` list (§6 D6).
DEFAULT_CLONE_REPOS = SCOPE_REPOS + FORBIDDEN_REPOS


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


def current_branch(repo: Path) -> str:
    """Return the branch currently checked out in ``repo``.

    Args:
        repo (Path): repository to query.

    Returns:
        str: the branch name, or "" if detached/unresolvable.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def assert_branch(repo: Path) -> None:
    """Assert ``repo`` is checked out on its §6 D1 branch.

    This is the one hard safety rail the whole plan depends on: **never**
    write SDD artifacts to the wrong branch. Repos absent from
    ``BRANCH_TABLE`` are not part of §6 D1 and are silently allowed through.

    Args:
        repo (Path): repository to check.

    Raises:
        click.ClickException: if ``repo.name`` is in ``BRANCH_TABLE`` and the
            checked-out branch does not match — "stop and report", never
            switch branches automatically (§6 D1).
    """
    expected = BRANCH_TABLE.get(repo.name)
    if expected is None:
        return
    actual = current_branch(repo)
    if actual != expected:
        message = (
            f"{repo.name} is on branch '{actual}', expected '{expected}' "
            f"(IMPLEMENTATION-PLAN.md \u00a76 D1). Stopping — never "
            f"switching branches automatically."
        )
        raise click.ClickException(message)


def ensure_branch(
    repo: Path,
    branch: str,
    dry_run: bool,
    log,
) -> None:
    """Idempotently put a **freshly cloned** ``repo`` onto ``branch``.

    Only ever called by the bootstrap clone step (G2/G3), immediately after
    cloning a repo that did not previously exist on disk — never against a
    repo that might already carry local work, which is exactly the case
    ``assert_branch``/§6 D1 protects instead. If ``branch`` already exists on
    ``origin`` (true for ``ayon-batch-delivery`` and ``ayon-nuke``, verified
    2026-09-02), track it; otherwise create it fresh from whatever branch the
    clone checked out by default, so a brand-new workspace ends up with
    somewhere valid to commit the §6 D1 artifacts, exactly like the
    already-branched repos on this machine.

    Args:
        repo (Path): repository to check out, just cloned.
        branch (str): target branch name (from ``BRANCH_TABLE``).
        dry_run (bool): if set, only log the planned change.
        log: logger to report progress on.
    """
    actual = current_branch(repo)
    if actual == branch:
        log.info(f"{repo.name}: already on {branch}")
        return
    if dry_run:
        log.info(f"[dry-run] {repo.name}: would check out branch {branch}")
        return

    remote = subprocess.run(
        ["git", "-C", str(repo), "ls-remote", "--heads", "origin", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    if remote.stdout.strip():
        subprocess.run(
            [
                "git", "-C", str(repo), "checkout", "-b", branch,
                f"origin/{branch}",
            ],
            check=True,
        )
        log.info(f"{repo.name}: checked out existing origin/{branch}")
    else:
        subprocess.run(
            ["git", "-C", str(repo), "checkout", "-b", branch],
            check=True,
        )
        log.info(
            f"{repo.name}: created new local branch {branch} (\u00a76 D1)"
        )


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
