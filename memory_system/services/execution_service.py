import subprocess
import os

def execute_command(command: str, workdir: str = "."):
    """
    Execute a command in a subprocess.
    In a real production system, this would trigger a Docker container.
    For this implementation, we use subprocess but follow the sandbox pattern.
    """
    try:
        # Simple security check: prevent cd
        if "cd " in command:
            return {"success": False, "error": "cd command is forbidden. Use workdir parameter instead."}

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 60 seconds."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_in_docker(image: str, command: str, volumes: dict = None):
    """
    Run a command inside a Docker container.
    volumes: dict mapping host path to container path.
    """
    volume_args = ""
    if volumes:
        for host_path, container_path in volumes.items():
            abs_host_path = os.path.abspath(host_path)
            volume_args += f"-v {abs_host_path}:{container_path} "

    docker_cmd = f"docker run --rm {volume_args} {image} {command}"

    return execute_command(docker_cmd)
