#!/usr/bin/env python

"""Render and install the user-global Zed tasks.

Idempotently writes ``~/.config/zed/tasks.json`` — global Zed tasks,
rendered from ``templates/zed_tasks.json.tmpl`` (ported from
``<ROOT>/.zed/tasks.json``). Global tasks show up in every project opened in
Zed, so the workspace tasks stay available inside any single ``ayon-*``
repo or worktree.

This is the only supported way to produce that file — it is generated
output and must never be hand-edited; edit the template and re-run instead.

Script usage:
  uv run ayon-workspace install-global [--dry-run]
"""

import logging
import shutil
import sys
from pathlib import Path

import click

from .workspace_common import resolve_workspace_root

templates_dir = Path(__file__).resolve().parent / "templates"

WORKSPACE_ROOT_TOKEN = "__AYON_WORKSPACE_ROOT__"


def _backup_if_needed(path: Path, log: logging.Logger) -> None:
    """Back up a real file before it is overwritten.

    Args:
        path (Path): file that is about to be overwritten.
        log (logging.Logger): logger to report the backup on.
    """
    if path.exists() and not path.is_symlink():
        backup_path = path.with_name(path.name + ".bak")
        shutil.copy2(path, backup_path)
        log.info(f"Backed up existing {path} -> {backup_path}")


def _render(template_name: str, root: Path) -> str:
    """Render a template file by substituting the workspace-root token.

    Args:
        template_name (str): file name under ``templates/``.
        root (Path): resolved workspace root to substitute in.

    Returns:
        str: rendered template content.
    """
    text = (templates_dir / template_name).read_text()
    return text.replace(WORKSPACE_ROOT_TOKEN, str(root))


def _install_tasks_json(
    root: Path, dry_run: bool, log: logging.Logger
) -> None:
    """Render and write the global Zed tasks file."""
    target = Path.home() / ".config" / "zed" / "tasks.json"
    rendered = _render("zed_tasks.json.tmpl", root)

    if (
        target.exists()
        and not target.is_symlink()
        and target.read_text() == rendered
    ):
        log.info(f"{target} already up to date")
        return

    if dry_run:
        log.info(f"[dry-run] would write {target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    _backup_if_needed(target, log)
    target.write_text(rendered)
    log.info(f"Wrote {target}")


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the planned filesystem changes without writing anything.",
)
def install_global(dry_run):
    """Render and install the user-global Zed tasks.

    Writes ``~/.config/zed/tasks.json`` from the template in ``templates/``.

    Args:
        dry_run (bool): if set, print the plan without writing any files.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("install_global")

    root = resolve_workspace_root()
    if not root.exists():
        log.error(f"Resolved workspace root does not exist: {root}")
        sys.exit(1)
    log.info(f"Workspace root: {root}")

    _install_tasks_json(root, dry_run, log)

    if dry_run:
        log.info("Dry run complete — no files were changed.")
    else:
        log.info("Global Zed tasks installed.")


if __name__ == "__main__":
    install_global()
