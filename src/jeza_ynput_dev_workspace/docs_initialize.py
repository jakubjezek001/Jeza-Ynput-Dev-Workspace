import os
import subprocess
from pathlib import Path


def docs_initialize():
    script_path = Path(__file__).resolve()
    root_dir = script_path.parents[2]
    website_dir = root_dir / 'ayon-documentation' / 'website'

    try:
        # Change directory to ayon-documentation/website
        os.chdir(website_dir)

        # Install yarn globally via npm
        subprocess.run('npm install -g yarn', shell=True, check=True)

        # Add docusaurus as dev dependency using yarn
        subprocess.run('yarn add docusaurus --dev', shell=True, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except FileNotFoundError:
        print("Error: Either 'npm/yarn' command not found or website directory does not exist")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
