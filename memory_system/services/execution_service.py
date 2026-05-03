import subprocess
from typing import Dict, Tuple, Optional

def run_in_docker(image: str, command: str, volumes: Optional[Dict[str, str]] = None) -> Tuple[bool, str, str]:
    """
    Run a command in an ephemeral Docker container.
    """
    docker_cmd = ["docker", "run", "--rm"]

    if volumes:
        for host_path, container_path in volumes.items():
            docker_cmd.extend(["-v", f"{host_path}:{container_path}"])

    docker_cmd.extend(["-w", "/app"])
    docker_cmd.append(image)
    docker_cmd.extend(["sh", "-c", command])

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except Exception as e:
        return (False, "", str(e))

def execute_command(command: str, workdir: str = "."):
    return run_in_docker("alpine:latest", command, volumes={workdir: "/app"})
