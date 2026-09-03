#!/usr/bin/env python

"""Wire (and unwire) a repo into the L2 shared-config layer — Phase D2.

Idempotently sets each in-scope repo's ``core.hooksPath`` to the shared,
absolute hooks directory (G2), symlinks ``.agents-main`` to the local
``ayon-agentic-instructions`` checkout, symlinks ``.zed`` to the shared
workspace project config (verified safe in D3), and hides both from
``git status`` via ``.git/info/exclude`` — without ever touching a repo's
committed ``.gitignore`` (G4), and without a trailing slash on the symlink
entries (G5, or the symlink itself is not recognised as ignored).

Both symlinks use a **relative** target (``../<name>``) because every repo
in scope is a direct sibling of ``<ROOT>``. Linked *worktrees* of these
repos live at a different depth, so ``ayon-sdd worktree-setup`` (D1/D4)
performs the equivalent job with **absolute** targets instead — see that
module's docstring.

Script usage:
  uv run ayon-sdd link   [--repo PATH ...] [--all] [--dry-run]
  uv run ayon-sdd unlink [--repo PATH ...] [--all] [--dry-run]
"""

import logging
import subprocess
from pathlib import Path

import click

from .sdd_common import (
    CENTRAL_REPO,
    is_tracked,
    resolve_target_repos,
    resolve_workspace_root,
)

# name -> relative symlink target, e.g. ".agents-main" -> "../<central repo>"
LINKS = {
    ".agents-main": f"../{CENTRAL_REPO}",
    ".zed": "../.zed",
}

# No trailing slash on a symlinked directory (G5).
EXCLUDE_ENTRIES = [f"/{name}" for name in LINKS]


def _get_git_config(repo: Path, key: str) -> str:
    """Return the current value of a git config key, or "" if unset.

    Args:
        repo (Path): repository to query.
        key (str): git config key, e.g. ``core.hooksPath``.

    Returns:
        str: the configured value, or an empty string if unset.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", key],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _set_hooks_path(
    repo: Path,
    hooks_path: Path,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently set ``core.hooksPath`` to an absolute path (G2/G3)."""
    current = _get_git_config(repo, "core.hooksPath")
    if current == str(hooks_path):
        log.info(f"{repo.name}: core.hooksPath already {hooks_path}")
        return
    if dry_run:
        log.info(
            f"[dry-run] {repo.name}: would set core.hooksPath={hooks_path}"
        )
        return
    subprocess.run(
        ["git", "-C", str(repo), "config", "core.hooksPath", str(hooks_path)],
        check=True,
    )
    log.info(f"{repo.name}: set core.hooksPath={hooks_path}")


def _unset_hooks_path(
    repo: Path,
    hooks_path: Path,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently unset ``core.hooksPath`` if it matches ours.

    Never touches a value we did not set ourselves, to avoid clobbering
    unrelated config.
    """
    current = _get_git_config(repo, "core.hooksPath")
    if not current:
        log.info(f"{repo.name}: core.hooksPath already unset")
        return
    if current != str(hooks_path):
        log.warning(
            f"{repo.name}: core.hooksPath is '{current}', not ours "
            f"({hooks_path}) — leaving it alone"
        )
        return
    if dry_run:
        log.info(f"[dry-run] {repo.name}: would unset core.hooksPath")
        return
    subprocess.run(
        ["git", "-C", str(repo), "config", "--unset", "core.hooksPath"],
        check=True,
    )
    log.info(f"{repo.name}: unset core.hooksPath")


def _link_one_path(
    link_path: Path,
    relative_target: str,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently point ``link_path`` at ``relative_target``.

    Removes a pre-existing empty real directory first (the
    ``ayon-nuke/.zed`` case), but refuses to touch a non-empty real
    directory or file, to avoid silent data loss.

    Args:
        link_path (Path): path (inside a repo) that should become a symlink.
        relative_target (str): symlink target, written verbatim, relative
            to ``link_path``'s parent directory.
        dry_run (bool): if set, only log the planned change.
        log (logging.Logger): logger to report progress on.
    """
    expected_resolved = (link_path.parent / relative_target).resolve()

    if link_path.is_symlink():
        if link_path.resolve() == expected_resolved:
            log.info(f"{link_path} already -> {relative_target}")
            return
        if dry_run:
            log.info(
                f"[dry-run] would relink {link_path} -> {relative_target}"
            )
            return
        link_path.unlink()
    elif link_path.is_dir():
        if any(link_path.iterdir()):
            log.warning(f"{link_path} is a non-empty real directory, skipping")
            return
        if dry_run:
            log.info(f"[dry-run] would remove empty dir {link_path}")
        else:
            link_path.rmdir()
    elif link_path.exists():
        log.warning(f"{link_path} is a real file, skipping")
        return

    if dry_run:
        log.info(f"[dry-run] would symlink {link_path} -> {relative_target}")
        return
    link_path.symlink_to(relative_target)
    log.info(f"Symlinked {link_path} -> {relative_target}")


def _unlink_one_path(
    link_path: Path,
    relative_target: str,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently remove a symlink previously created by ``link``."""
    if not link_path.is_symlink():
        log.info(f"{link_path} is not a symlink, nothing to remove")
        return
    if dry_run:
        log.info(
            f"[dry-run] would remove symlink {link_path} -> {relative_target}"
        )
        return
    link_path.unlink()
    log.info(f"Removed symlink {link_path}")


def _update_exclude(
    repo: Path,
    add: bool,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently add or remove ``EXCLUDE_ENTRIES`` in ``.git/info/exclude``.

    Only entries whose corresponding path is *not* already tracked by git are
    touched — a tracked path (e.g. a committed ``.zed/settings.json``, as in
    ``ayon-batch-delivery``) is left alone entirely by ``link``/``unlink``.
    """
    exclude_path = repo / ".git" / "info" / "exclude"
    lines = (
        exclude_path.read_text().splitlines() if exclude_path.exists() else []
    )

    wanted = [
        entry
        for entry in EXCLUDE_ENTRIES
        if not is_tracked(repo, entry.lstrip("/"))
    ]

    changed = False
    if add:
        for entry in wanted:
            if entry not in lines:
                lines.append(entry)
                changed = True
    else:
        for entry in EXCLUDE_ENTRIES:
            if entry in lines:
                lines.remove(entry)
                changed = True

    if not changed:
        log.info(f"{repo.name}: .git/info/exclude already up to date")
        return
    if dry_run:
        log.info(f"[dry-run] {repo.name}: would update .git/info/exclude")
        return
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    exclude_path.write_text("\n".join(lines) + "\n")
    log.info(f"{repo.name}: updated .git/info/exclude")


def link_one(
    repo: Path, root: Path, dry_run: bool, log: logging.Logger
) -> None:
    """Perform D2 for a single repo: hooksPath, symlinks, info/exclude.

    Args:
        repo (Path): repository to wire.
        root (Path): resolved workspace root.
        dry_run (bool): if set, only log the planned changes.
        log (logging.Logger): logger to report progress on.
    """
    hooks_path = root / ".githooks-shared"
    _set_hooks_path(repo, hooks_path, dry_run, log)

    for name, relative_target in LINKS.items():
        link_path = repo / name
        if is_tracked(repo, name):
            log.info(
                f"{repo.name}: {name} is tracked by git, "
                f"link skipped by design"
            )
            continue
        _link_one_path(link_path, relative_target, dry_run, log)

    _update_exclude(repo, add=True, dry_run=dry_run, log=log)


def unlink_one(
    repo: Path, root: Path, dry_run: bool, log: logging.Logger
) -> None:
    """Fully reverse ``link_one`` for a single repo.

    Args:
        repo (Path): repository to unwire.
        root (Path): resolved workspace root.
        dry_run (bool): if set, only log the planned changes.
        log (logging.Logger): logger to report progress on.
    """
    hooks_path = root / ".githooks-shared"
    _unset_hooks_path(repo, hooks_path, dry_run, log)

    for name, relative_target in LINKS.items():
        _unlink_one_path(repo / name, relative_target, dry_run, log)

    _update_exclude(repo, add=False, dry_run=dry_run, log=log)


@click.command(name="link")
@click.option(
    "--repo",
    "repos",
    multiple=True,
    type=click.Path(),
    help="Repo path (repeatable).",
)
@click.option(
    "--all", "use_all", is_flag=True, help="Link every repo in SCOPE_REPOS."
)
@click.option(
    "--dry-run", is_flag=True, help="Print the plan without writing anything."
)
def link(repos: tuple, use_all: bool, dry_run: bool) -> None:
    """Wire one or more repos into the L2 shared-config layer (D2).

    Args:
        repos (tuple): explicit ``--repo`` paths.
        use_all (bool): if set, link every repo in ``SCOPE_REPOS``.
        dry_run (bool): if set, print the plan without writing anything.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("link")

    root = resolve_workspace_root()
    targets = resolve_target_repos(root, repos, use_all)
    for target in targets:
        link_one(target, root, dry_run, log)


@click.command(name="unlink")
@click.option(
    "--repo",
    "repos",
    multiple=True,
    type=click.Path(),
    help="Repo path (repeatable).",
)
@click.option(
    "--all", "use_all", is_flag=True, help="Unlink every repo in SCOPE_REPOS."
)
@click.option(
    "--dry-run", is_flag=True, help="Print the plan without writing anything."
)
def unlink(repos: tuple, use_all: bool, dry_run: bool) -> None:
    """Fully reverse ``link`` for one or more repos.

    Args:
        repos (tuple): explicit ``--repo`` paths.
        use_all (bool): if set, unlink every repo in ``SCOPE_REPOS``.
        dry_run (bool): if set, print the plan without writing anything.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("unlink")

    root = resolve_workspace_root()
    targets = resolve_target_repos(root, repos, use_all)
    for target in targets:
        unlink_one(target, root, dry_run, log)


if __name__ == "__main__":
    link()
