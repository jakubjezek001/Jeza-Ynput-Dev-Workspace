import subprocess

from .sdd_common import resolve_workspace_root


def docs_initialize():
    root_dir = resolve_workspace_root()
    website_dir = root_dir / "ayon-documentation" / "website"

    try:
        subprocess.run(["npm", "install", "-g", "yarn"], check=True)
        subprocess.run(
            ["yarn", "add", "docusaurus", "--dev"], cwd=website_dir, check=True
        )

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except FileNotFoundError:
        print(
            "Error: Either 'npm/yarn' command not found or website directory does not exist"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
