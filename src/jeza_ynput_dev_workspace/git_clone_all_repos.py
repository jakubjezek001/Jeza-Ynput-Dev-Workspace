import os
import subprocess
from pathlib import Path
from typing import List, Union


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
    # Change to the specified directory
    os.chdir(current_directory)

    # List of repositories to clone, organized by category
    repositories: List[str] = [
        # Core repositories
        "ayon-docker",
        "ayon-core",
        "ayon-launcher",
        "ayon-applications",
        "ayon-ocio",
        "ayon-python-api",
        "ayon-third-party",
        "ayon-traypublisher",
        # Integration repositories
        # comp
        "ayon-nuke",
        "ayon-aftereffects",
        "ayon-fusion",
        "ayon-silhouette",
        "ayon-mocha",
        # editorial
        "ayon-hiero",
        "ayon-resolve",
        "ayon-flame",
        # paint
        "ayon-photoshop",
        # animation
        "ayon-tvpaint",
        "ayon-harmony",
        # services
        "ayon-deadline",
        "ayon-circuit",
        # production tracking
        "ayon-ftrack",
        "ayon-syncsketch",
        "ayon-shotgrid",
        # 3d
        "ayon-unreal",
        # Tool repositories
        "ayon-dependencies-tool",
        "ayon-documentation",
        "ayon-frontend",
        "ayon-premium-pipeline",
        "ayon-batch-publisher",
        "ynput-ops-prodman",
        "ayon-premium-burnins",
        "OpenPype-premium"
    ]

    # Check each repository and clone if it doesn't exist
    for repo in repositories:
        repo_path = Path(current_directory) / repo
        if repo_path.exists():
            print(f"'{repo}' exists")
        else:
            result = subprocess.run(
                ["git", "clone", f"https://github.com/ynput/{repo}.git"]
            )
            if result.returncode == 0:
                print(f"'{repo}' cloned successfully")
            else:
                raise FileNotFoundError(f"Error cloning '{repo}' repository")

def git_clone_all_repos() -> None:
    """Entry point for cloning all YNPUT repositories.

    This function uses the current working directory as the target location
    for cloning repositories.

    Returns:
        None
    """
    current_dir = os.getcwd()
    initialize_all_clone(current_dir)
