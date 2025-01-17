import os
import subprocess


def update_ayon_docker_local_dir():
    try:
        # Change directory to ayon-docker
        os.chdir('ayon-docker')

        # Execute docker compose commands
        print("Pulling server image...")
        subprocess.run(['docker', 'compose', 'pull', 'server'], check=True)

        print("Starting server container...")
        subprocess.run(['docker', 'compose', 'up', '-d', 'server', '--build'], check=True)

        print("Server successfully started!")

    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command: {e}")
    except FileNotFoundError:
        print("Error: 'ayon-docker' directory not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
