import os
import subprocess
from pathlib import Path
from typing import List, Union

# List of repositories to clone, organized by category. Moved to a module
# constant (Phase G, G2) so ``--all`` (the full ~40-repo set, §6 D6) and the
# existing ``git_clone_all_repos()`` entry point share one definition instead
# of drifting copies.
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
]


def clone_repos(
    target_dir: Union[str, Path],
    repos: List[str],
    dry_run: bool = False,
) -> List[str]:
    """Clone ``repos`` into ``target_dir`` without changing directory.

    This is the reusable primitive behind both ``git_clone_all_repos()``
    (unchanged behaviour, full ``ALL_REPOS`` list) and
    ``ayon-sdd bootstrap`` (Phase G, G2), which needs an explicit repo list
    and target path and must never call ``os.chdir`` globally.

    Always clones the default branch — a §6 D1 repo's target branch does
    not necessarily exist on ``origin`` yet (verified true for 5 of the 7
    repos, 2026-09-03), so ``git clone -b <branch>`` would fail outright.
    ``ayon-sdd bootstrap`` instead calls ``sdd_common.ensure_branch`` after
    cloning, which correctly handles both cases (track the branch if it
    exists on ``origin``, otherwise create it fresh).

    Args:
        target_dir (Union[str, Path]): directory repos are cloned into;
            created if missing.
        repos (List[str]): repo names (under ``github.com/ynput/``) to
            clone.
        dry_run (bool): if set, only print the plan, clone nothing.

    Returns:
        List[str]: names of repos that were newly cloned in this call
            (excludes repos that already existed on disk) — used by
            ``bootstrap`` to know which repos it may safely put on a
            specific branch (G2/§6 D1).

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

    This function uses the current working directory as the target location
    for cloning repositories.

    Returns:
        None
    """
    current_dir = os.getcwd()
    initialize_all_clone(current_dir)
