#!/usr/bin/env python

"""Render and install the L0 (user-global) SDD layer — Phase A.

Idempotently writes the files that make Zed and goose agent-aware from
*any* project, not just this workspace root:

- ``~/.config/zed/tasks.json``  — global Zed tasks, rendered from
  ``templates/zed_tasks.json.tmpl`` (ported from ``<ROOT>/.zed/tasks.json``).
- ``~/.config/zed/AGENTS.md``   — global Zed personal agent instructions,
  rendered from ``templates/zed_agents.md.tmpl``.
- ``~/.config/goose/AGENTS.md`` — symlinked to the file above, so goose picks
  up the same content with zero drift.
- ``~/.agents/skills/<name>``   — the shared workspace skills, moved here
  (visible to goose and Zed from any directory) with a symlink back into
  ``<ROOT>/.agents/skills/<name>`` so the workspace keeps working too.

It also *verifies* (never modifies) ``GOOSE_MODE`` in the user's
``~/.config/goose/config.yaml``.

This is the only supported way to produce the L0 layer — the files above are
generated output and must never be hand-edited once this command exists.

Script usage:
  uv run ayon-sdd install-global [--dry-run]
  uv run ayon-sdd-install-global [--dry-run]
"""

import logging
import os
import shutil
import sys
from pathlib import Path

import click

scripts_dir = Path(__file__).resolve().parent
templates_dir = scripts_dir / "templates"
package_workspace_dir = scripts_dir.parent.parent

# Shared skills currently under <ROOT>/.agents/skills that must become
# globally visible (goose's per-repo skill visibility limitation, N1).
SHARED_SKILLS = ["harsh-code-review", "yn-pr-description", "yn-pr-update"]

WORKSPACE_ROOT_TOKEN = "__AYON_WORKSPACE_ROOT__"


def _resolve_workspace_root() -> Path:
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
    return package_workspace_dir


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
    """Render and write the global Zed tasks file (A1)."""
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


def _install_agents_md(root: Path, dry_run: bool, log: logging.Logger) -> None:
    """Render the global Zed AGENTS.md and symlink goose's to it (A2, A3)."""
    zed_target = Path.home() / ".config" / "zed" / "AGENTS.md"
    goose_target = Path.home() / ".config" / "goose" / "AGENTS.md"
    rendered = _render("zed_agents.md.tmpl", root)

    zed_up_to_date = (
        zed_target.exists()
        and not zed_target.is_symlink()
        and zed_target.read_text() == rendered
    )

    if dry_run:
        if not zed_up_to_date:
            log.info(f"[dry-run] would write {zed_target}")
        goose_linked = (
            goose_target.is_symlink()
            and goose_target.resolve() == zed_target.resolve()
        )
        if not goose_linked:
            log.info(f"[dry-run] would symlink {goose_target} -> {zed_target}")
        return

    if zed_up_to_date:
        log.info(f"{zed_target} already up to date")
    else:
        zed_target.parent.mkdir(parents=True, exist_ok=True)
        _backup_if_needed(zed_target, log)
        zed_target.write_text(rendered)
        log.info(f"Wrote {zed_target}")

    goose_target.parent.mkdir(parents=True, exist_ok=True)
    if (
        goose_target.is_symlink()
        and goose_target.resolve() == zed_target.resolve()
    ):
        log.info(f"{goose_target} already symlinked to {zed_target}")
        return
    if goose_target.exists() or goose_target.is_symlink():
        _backup_if_needed(goose_target, log)
        goose_target.unlink()
    goose_target.symlink_to(zed_target)
    log.info(f"Symlinked {goose_target} -> {zed_target}")


def _install_shared_skills(
    root: Path, dry_run: bool, log: logging.Logger
) -> None:
    """Move the shared skills to ``~/.agents/skills`` and link back (A4)."""
    global_skills_dir = Path.home() / ".agents" / "skills"
    local_skills_dir = root / ".agents" / "skills"

    for name in SHARED_SKILLS:
        global_path = global_skills_dir / name
        local_path = local_skills_dir / name

        already_linked = (
            local_path.is_symlink()
            and global_path.exists()
            and local_path.resolve() == global_path.resolve()
        )
        if already_linked:
            log.info(f"{name}: already migrated and linked")
            continue

        if dry_run:
            log.info(
                f"[dry-run] would move {local_path} -> {global_path} "
                f"and symlink it back"
            )
            continue

        global_skills_dir.mkdir(parents=True, exist_ok=True)
        local_skills_dir.mkdir(parents=True, exist_ok=True)

        if local_path.is_dir() and not local_path.is_symlink():
            if global_path.exists():
                log.info(
                    f"{global_path} already exists; removing local "
                    f"duplicate {local_path}"
                )
                shutil.rmtree(local_path)
            else:
                shutil.move(str(local_path), str(global_path))
                log.info(f"Moved {local_path} -> {global_path}")
        elif not global_path.exists():
            log.warning(
                f"Skill '{name}' not found locally or globally, skipping"
            )
            continue

        if local_path.is_symlink() or local_path.exists():
            if local_path.is_symlink():
                local_path.unlink()
        local_path.symlink_to(global_path)
        log.info(f"Symlinked {local_path} -> {global_path}")


def _verify_goose_mode(log: logging.Logger) -> None:
    """Verify (never modify) ``GOOSE_MODE`` in the user's goose config (A5)."""
    config_path = Path.home() / ".config" / "goose" / "config.yaml"
    if not config_path.exists():
        log.warning(f"{config_path} not found; cannot verify GOOSE_MODE")
        return

    for line in config_path.read_text().splitlines():
        if line.strip().startswith("GOOSE_MODE"):
            value = line.split(":", 1)[1].strip()
            if value == "auto":
                log.info(
                    f"Verified: GOOSE_MODE: {value} (subagents enabled, N10)"
                )
            else:
                log.warning(
                    f"GOOSE_MODE is '{value}', not 'auto' — subagent "
                    f"delegation is disabled (N10). Not modifying the "
                    f"user's config; set it manually if needed."
                )
            return

    log.warning(
        "GOOSE_MODE not found in goose config.yaml; subagent delegation is "
        "disabled by default (N10)."
    )


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the planned filesystem changes without writing anything.",
)
def install_global(dry_run):
    """Render and install the L0 user-global SDD layer.

    Writes ``~/.config/zed/tasks.json`` and ``~/.config/zed/AGENTS.md`` from
    the templates in ``templates/``, symlinks ``~/.config/goose/AGENTS.md``
    to the latter, migrates the shared workspace skills to
    ``~/.agents/skills/`` with a symlink back for the workspace root, and
    verifies (without modifying) ``GOOSE_MODE`` in the goose config.

    Args:
        dry_run (bool): if set, print the plan without writing any files.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("install_global")

    root = _resolve_workspace_root()
    if not root.exists():
        log.error(f"Resolved workspace root does not exist: {root}")
        sys.exit(1)
    log.info(f"Workspace root: {root}")

    _install_tasks_json(root, dry_run, log)
    _install_agents_md(root, dry_run, log)
    _install_shared_skills(root, dry_run, log)
    _verify_goose_mode(log)

    if dry_run:
        log.info("Dry run complete — no files were changed.")
    else:
        log.info("Global (L0) SDD layer installed.")


if __name__ == "__main__":
    install_global()
