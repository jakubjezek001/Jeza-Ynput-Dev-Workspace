import subprocess

from .sdd_common import resolve_workspace_root


def update_ayon_docker_local_dir():
    try:
        docker_dir = resolve_workspace_root() / "ayon-docker"
        if not docker_dir.is_dir():
            raise FileNotFoundError(docker_dir)

        # Execute docker compose commands
        print("Pulling server image...")
        subprocess.run(
            ["docker", "compose", "pull", "server"], cwd=docker_dir, check=True
        )

        print("Starting server container...")
        subprocess.run(
            ["docker", "compose", "up", "-d", "server", "--build"],
            cwd=docker_dir,
            check=True,
        )

        print("Server successfully started!")

    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command: {e}")
    except FileNotFoundError:
        print("Error: 'ayon-docker' directory not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
