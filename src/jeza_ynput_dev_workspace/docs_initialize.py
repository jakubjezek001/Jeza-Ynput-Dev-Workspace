import os
import subprocess


def docs_initialize():
    # Change directory to ayon-documentation/website
    os.chdir('ayon-documentation/website')

    try:
        # Change directory to ayon-documentation/website
        os.chdir('ayon-documentation/website')

        # Install yarn globally via npm
        subprocess.run(['npm', 'install', '-g', 'yarn'])

        # Add docusaurus as dev dependency using yarn
        subprocess.run(['yarn', 'add', 'docusaurus', '--dev'])

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except FileNotFoundError:
        print("Error: 'ayon-documentation/website' directory not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
