#!/usr/bin/env python

"""Resolve a selected file to its actual AYON Git checkout.

Zed can pass files from the main checkout or from worktrees with arbitrary
parent directories.  The filesystem path is therefore not a reliable addon
identifier.  Git is the source of truth for both the checkout root and the
common repository identity.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckoutContext:
    """The repository identity and checkout containing a selected file."""

    addon_name: str
    checkout_root: Path
    common_git_dir: Path


def _git_value(search_dir: Path, *args: str) -> str | None:
    """Return one Git value from ``search_dir``, or ``None`` on failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(search_dir), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    value = result.stdout.strip()
    return value or None


def resolve_checkout(
    file_path: str | Path,
    workspace_root: Path | None = None,
) -> CheckoutContext | None:
    """Resolve ``file_path`` to its AYON checkout using Git.

    This works for a direct checkout, a normal ``git worktree`` and Zed's
    nested worktree layout.  A path outside Git receives a conservative
    workspace-relative fallback for backwards compatibility.
    """
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    search_dir = path if path.is_dir() else path.parent

    toplevel = _git_value(search_dir, "rev-parse", "--show-toplevel")
    common_dir = _git_value(
        search_dir,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
    )
    if toplevel and common_dir:
        common_path = Path(common_dir).resolve()
        addon_name = common_path.parent.name
        if addon_name.startswith("ayon-"):
            return CheckoutContext(
                addon_name=addon_name,
                checkout_root=Path(toplevel).resolve(),
                common_git_dir=common_path,
            )

    if workspace_root is None:
        return None
    root = workspace_root.expanduser().resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
    if not relative.parts or not relative.parts[0].startswith("ayon-"):
        return None
    addon_name = relative.parts[0]
    checkout = root / addon_name
    if not checkout.is_dir():
        return None
    return CheckoutContext(
        addon_name=addon_name,
        checkout_root=checkout,
        common_git_dir=checkout / ".git",
    )
