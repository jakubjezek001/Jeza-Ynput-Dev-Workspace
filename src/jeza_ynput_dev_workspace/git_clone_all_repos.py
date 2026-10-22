import os
import subprocess
from pathlib import Path
from typing import List, Union

from .workspace_common import resolve_workspace_root

# List of repositories to clone, organized by category. A module constant
# so ``ayon-workspace bootstrap --all`` and the ``git_clone_all_repos()``
# entry point share one definition instead of drifting copies.
ALL_REPOS: List[str] = [
    # Core repositories
    "ayon-docker",
    "ayon-core",
    "ayon-launcher",
    "ayon-applications",
    "ayon-ocio",
    "ayon-python-api",
    "ayon-third-party",
    "ayon-traypublisher",
    "ayon-review",
    # Integration repositories
    # comp
    "ayon-nuke",
    "ayon-maya",
    "ayon-aftereffects",
    "ayon-fusion",
    "ayon-silhouette",
    "ayon-mocha",
    "ayon-openrv",
    "ayon-xstudio",
    # editorial
    "ayon-hiero",
    "ayon-resolve",
    "ayon-flame",
    "ayon-premiere",
    # paint
    "ayon-photoshop",
    # animation
    "ayon-tvpaint",
    "ayon-harmony",
    # services
    "ayon-deadline",
    "ayon-batch-delivery",
    # production tracking
    "ayon-ftrack",
    "ayon-syncsketch",
    "ayon-shotgrid",
    # 3d
    # "ayon-unreal",
    # Tool repositories
    "pytest-ayon",
    "ayon-dependencies-tool",
    "ayon-documentation",
    "ayon-backend",
    "ayon-premium-pipeline",
    "ayon-batch-ingest",
    "ayon-premium-burnins",
    "ayon-slater",
    "OpenPype-premium",
    # "ayon-server-production-planner",
    # "ayon-review-desktop",
    "ayon-sn4",
    "ayon-ui-qt",
    "ayon-webpublisher",
    "ayon-mcp",
]


def clone_repos(
    target_dir: Union[str, Path],
    repos: List[str],
    dry_run: bool = False,
) -> List[str]:
    """Clone ``repos`` into ``target_dir`` without changing directory.

    This is the reusable primitive behind both ``git_clone_all_repos()``
    (full ``ALL_REPOS`` list) and ``ayon-workspace bootstrap``, which needs
    an explicit repo list and target path and must never call ``os.chdir``
    globally. Always clones the default branch.

    Args:
        target_dir (Union[str, Path]): directory repos are cloned into;
            created if missing.
        repos (List[str]): repo names (under ``github.com/ynput/``) to
            clone.
        dry_run (bool): if set, only print the plan, clone nothing.

    Returns:
        List[str]: names of repos that were newly cloned in this call
            (excludes repos that already existed on disk).

    Raises:
        FileNotFoundError: if a ``git clone`` invocation fails.
    """
    target = Path(target_dir)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    newly_cloned: List[str] = []
    for repo in repos:
        repo_path = target / repo
        if repo_path.exists():
            print(f"'{repo}' exists", flush=True)
            continue

        if dry_run:
            print(
                f"[dry-run] would clone '{repo}' into {target}",
                flush=True,
            )
            newly_cloned.append(repo)
            continue

        command = ["git", "clone", f"https://github.com/ynput/{repo}.git"]
        result = subprocess.run(command, cwd=str(target))
        if result.returncode == 0:
            print(f"'{repo}' cloned successfully", flush=True)
            newly_cloned.append(repo)
        else:
            raise FileNotFoundError(f"Error cloning '{repo}' repository")

    return newly_cloned


def initialize_all_clone(current_directory: Union[str, Path]) -> None:
    """Initialize and clone all YNPUT repositories if they don't exist.

    Args:
        current_directory (Union[str, Path]): The target directory where
            repositories should be cloned.

    Returns:
        None

    Example:
        >>> initialize_all_clone("/path/to/workspace")
    """
    # Change to the specified directory — preserved for backward
    # compatibility with the existing ``git_clone_all_repos()`` entry point.
    os.chdir(current_directory)
    clone_repos(current_directory, ALL_REPOS)


def git_clone_all_repos() -> None:
    """Entry point for cloning all YNPUT repositories.

    Repositories are cloned into the workspace root (``$AYON_WORKSPACE_ROOT``
    if set, otherwise derived from this package's location). The current
    working directory is deliberately not used: Zed falls back to ``/`` when
    a task's ``cwd`` (``${AYON_WORKSPACE_ROOT}``) is unset, which made every
    repo look missing and ``git clone`` fail on the read-only system root.

    Returns:
        None
    """
    initialize_all_clone(resolve_workspace_root())
