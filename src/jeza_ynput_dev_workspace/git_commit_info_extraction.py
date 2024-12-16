import os
import sys
from pathlib import Path

import click
import git

scripts_dir = Path(__file__).resolve().parent
workspace_dir = Path(__file__).resolve().parent.parent.parent


@click.command()
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    help="Relative file path to workspace root.",
)
def git_commit_info_extraction(file_path: Path):
    """
    Generate commit history for the current branch in the specified repository.

    Args:
        file_path (Path): Relative file path to workspace root.
    """
    repo_folders = os.listdir(workspace_dir.as_posix())

    # get first folder from file path and check if ayon-* is in name
    file_path = Path(file_path)
    # split path to get first folder
    first_folder = file_path.parts[0]
    if first_folder.startswith("ayon-") and first_folder in repo_folders:
        repo_abs_path = workspace_dir / first_folder
    else:
        click.echo("Error: No valid addon path found")
        sys.exit(1)

    def find_parent_branch(repo):
        """Find the parent branch"""
        possible_parents = ['main', 'develop']
        for parent in possible_parents:
            if parent in repo.refs:
                return parent
        return None

    try:
        # Initialize repository object with provided path
        repo = git.Repo(repo_abs_path)

        # Get current branch name
        current_branch = repo.active_branch.name

        parent_branch = find_parent_branch(repo)
        if not parent_branch:
            click.echo("Error: Could not determine parent branch", err=True)
            raise click.Abort()

        # Find the fork point
        fork_point = repo.git.merge_base(current_branch, parent_branch)

        # Get commits between fork point and current branch HEAD
        commits = list(repo.iter_commits(f'{fork_point}..{current_branch}'))

        # Get branch creation date
        branch_creation_date = commits[-1].committed_datetime if commits else None

        # Create markdown output
        output = f"# {current_branch}\n"
        if branch_creation_date:
            output += f"Branch created: {branch_creation_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Iterate through commits in reverse order (oldest first)
        for commit in reversed(commits):
            # Get commit title (first line of message)
            title = commit.message.split('\n')[0].strip()

            # Get commit description (rest of the message)
            description = '\n'.join(commit.message.split('\n')[1:]).strip()

            # Add commit information to output
            output += f"## {title}\n"
            if description:
                output += f"{description}\n"
            output += "\n"

        click.echo(output)

    except git.InvalidGitRepositoryError:
        click.echo("Error: Not a valid git repository", err=True)
        raise click.Abort()
    except git.NoSuchPathError:
        click.echo("Error: Repository path not found", err=True)
        raise click.Abort()
    except git.GitCommandError as e:
        click.echo(f"Error: Git command failed: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
