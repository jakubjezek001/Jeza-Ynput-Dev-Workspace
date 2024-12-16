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
        "ayon-nuke",
        "ayon-hiero",
        "ayon-resolve",
        "ayon-flame",
        "ayon-circuit",
        "ayon-ftrack",
        "ayon-syncsketch",
        "ayon-shotgrid",
        "ayon-deadline",
        # Tool repositories
        "ayon-dependencies-tool",
        "ayon-documentation",
    ]

    # Check each repository and clone if it doesn't exist
    for repo in repositories:
        repo_path = Path(current_directory) / repo
        if repo_path.exists():
            print(f"{repo_path} exists")
        else:
            subprocess.run(
                ["git", "clone", f"https://github.com/ynput/{repo}.git"]
            )


def git_clone_all_repos() -> None:
    """Entry point for cloning all YNPUT repositories.

    This function uses the current working directory as the target location
    for cloning repositories.

    Returns:
        None
    """
    current_dir = os.getcwd()
    initialize_all_clone(current_dir)
