#!/usr/bin/env python

"""Set up a freshly created linked worktree — Phase D1/D4 shared logic.

This is the **single implementation** invoked by both distribution paths a
worktree can be created through:

- the shared ``post-checkout`` git hook
  (``<ROOT>/.githooks-shared/post-checkout``, wired per-repo via
  ``core.hooksPath`` — D1/D2), for ``git worktree add``.
- the global Zed ``create_worktree`` task (``~/.config/zed/tasks.json`` — D4),
  for worktrees created through Zed's worktree picker.

Both call
``uv run ayon-sdd worktree-setup --worktree <new> --main <repo-main>``
instead of duplicating any of this logic (IMPLEMENTATION-PLAN.md D5: *"Do not
let post-checkout and the create_worktree task grow independent copies of the
same logic"*).

Unlike ``ayon-sdd link`` (same-directory siblings under ``<ROOT>``, so
relative symlinks work), a linked worktree can live at any depth relative to
``<ROOT>`` (e.g. ``ayon-nuke.worktrees/<branch>/``), so this module always
uses **absolute** symlink targets, resolved from ``<ROOT>`` (never a
hardcoded path — see ``sdd_common.resolve_workspace_root``).

Script usage:
  uv run ayon-sdd worktree-setup --worktree PATH --main PATH [--dry-run]
"""

import logging
import shutil
from pathlib import Path

import click

from .sdd_common import CENTRAL_REPO, resolve_workspace_root


def _relink_absolute(
    link_path: Path,
    target: Path,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Idempotently point ``link_path`` at an absolute ``target``.

    Removes a stale symlink or an empty real directory first (the
    ``ayon-nuke/.zed`` case ported to the worktree context); refuses to
    touch a non-empty real directory or file, to avoid silent data loss —
    this subcommand only ever runs against brand-new worktrees, so it never
    needs a ``--force`` escape hatch.

    Args:
        link_path (Path): path (inside the new worktree) to symlink.
        target (Path): absolute path the symlink should point to.
        dry_run (bool): if set, only log the planned change.
        log (logging.Logger): logger to report progress on.
    """
    if link_path.is_symlink():
        if link_path.resolve() == target.resolve():
            log.info(f"{link_path} already -> {target}")
            return
        if dry_run:
            log.info(f"[dry-run] would relink {link_path} -> {target}")
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
        log.info(f"[dry-run] would symlink {link_path} -> {target}")
        return
    link_path.symlink_to(target)
    log.info(f"Symlinked {link_path} -> {target}")


def _copy_env(
    main: Path,
    worktree: Path,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Copy ``.env`` from the repo's main worktree if missing here (G3).

    Args:
        main (Path): the repo's main worktree (has the real ``.env``).
        worktree (Path): the new linked worktree (never inherits it).
        dry_run (bool): if set, only log the planned change.
        log (logging.Logger): logger to report progress on.
    """
    src = main / ".env"
    dst = worktree / ".env"
    if not src.exists():
        log.info("No .env in main worktree, nothing to copy")
        return
    if dst.exists():
        log.info(".env already present in new worktree, not overwriting")
        return
    if dry_run:
        log.info(f"[dry-run] would copy {src} -> {dst}")
        return
    shutil.copy2(src, dst)
    log.info(f"Copied {src} -> {dst}")


@click.command(name="worktree-setup")
@click.option(
    "--worktree",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to the new linked worktree.",
)
@click.option(
    "--main",
    "main_worktree",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to the repo's main worktree (source of .env).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the planned changes without writing anything.",
)
def worktree_setup(worktree: str, main_worktree: str, dry_run: bool) -> None:
    """Wire a freshly created linked worktree into the L2 shared layer.

    Called only by the shared post-checkout hook and the Zed
    ``create_worktree`` task — never invoked directly by a person. Any
    unexpected problem is logged, not raised, so this command never fails a
    checkout (D1 rule 5: "never fail the checkout").

    Args:
        worktree (str): path to the new linked worktree.
        main_worktree (str): path to the repo's main worktree.
        dry_run (bool): if set, print the plan without writing any files.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("worktree_setup")

    try:
        root = resolve_workspace_root()
        worktree_path = Path(worktree).resolve()
        main_path = Path(main_worktree).resolve()

        _relink_absolute(
            worktree_path / ".agents-main", root / CENTRAL_REPO, dry_run, log
        )
        _relink_absolute(worktree_path / ".zed", root / ".zed", dry_run, log)
        _copy_env(main_path, worktree_path, dry_run, log)
    except Exception as exc:  # noqa: BLE001 - never fail the checkout (D1 rule 5)
        log.warning(f"worktree-setup hit a problem, continuing anyway: {exc}")
    else:
        log.info(
            "Dry run complete." if dry_run else "Worktree setup complete."
        )


if __name__ == "__main__":
    worktree_setup()
