import os
import subprocess
from pathlib import Path


def initialize_all_clone(current_directory):
    # Change to the specified directory
    os.chdir(current_directory)

    # List of repositories to clone
    repositories = [
        "ayon-applications",
        "ayon-core",
        "ayon-docker",
        "ayon-circuit",
        "ayon-deadline",
        "ayon-dependencies-tool",
        "ayon-documentation",
        "ayon-launcher",
        "ayon-nuke",
        "ayon-flame",
        "ayon-resolve",
        "ayon-syncsketch",
        "ayon-ocio",
        "ayon-python-api",
        "ayon-third-party",
        "ayon-traypublisher",
        "ayon-ftrack",
        "ayon-shotgrid",
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


def git_clone_all_repos():
    # You can call the function with the desired directory
    # For example:
    # initialize_all_clone("C:/path/to/directory")
    current_dir = os.getcwd()
    initialize_all_clone(current_dir)
