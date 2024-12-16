import os
import subprocess


def docs_start():
    try:
        # Change directory to ayon-documentation/website
        os.chdir('ayon-documentation/website')

        # Add docusaurus as dev dependency using yarn
        subprocess.run(['yarn', 'start'])

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except FileNotFoundError:
        print("Error: 'ayon-documentation/website' directory not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
