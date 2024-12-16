import os
import subprocess
from pathlib import Path


def docs_start():
    script_path = Path(__file__).resolve()
    root_dir = script_path.parents[2]
    website_dir = root_dir / 'ayon-documentation' / 'website'

    try:
        os.chdir(website_dir)
        # Use shell=True to help Windows find yarn
        subprocess.run('yarn start', shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except FileNotFoundError:
        print("Error: Either 'yarn' command not found or website directory does not exist")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
