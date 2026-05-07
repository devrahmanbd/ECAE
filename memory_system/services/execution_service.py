from memory_system.core.logger import logger
import subprocess
import os
from memory_system.models.schemas import ExecutionResult

def execute_command(command: str, workdir: str = ".", timeout: int = 60, profile_used: str = None) -> ExecutionResult:
    """
    Execute a command in a subprocess.
    """
    try:
        # Simple security check: prevent cd outside sandbox bounds
        if "cd " in command and not "cd /tmp" in command and not "cd /app" in command:
            return ExecutionResult(success=False, stdout="", stderr="", error="cd command is forbidden. Use workdir parameter instead.", profile_used=profile_used)

        logger.info(f"Executing command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=timeout
        )

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            profile_used=profile_used
        )

    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out: {command}")
        return ExecutionResult(success=False, stdout="", stderr="", error=f"Command timed out after {timeout} seconds.", profile_used=profile_used)
    except Exception as e:
        logger.error(f"Command failed with exception: {str(e)}")
        return ExecutionResult(success=False, stdout="", stderr="", error=str(e), profile_used=profile_used)

import time

def execute_command_with_retry(command: str, workdir: str = ".", timeout: int = 60, retries: int = 2, profile_used: str = None) -> ExecutionResult:
    attempt = 0
    while attempt <= retries:
        result = execute_command(command, workdir, timeout, profile_used=profile_used)
        if result.success or (result.error and "forbidden" in result.error): # Don't retry security errors
            return result
        attempt += 1
        if attempt <= retries:
            logger.warning(f"Command failed, retrying ({attempt}/{retries})...")
            time.sleep(1)
    return result

def run_in_docker(image: str, build_command: str, test_command: str, volumes: dict = None, timeout: int = 60, profile_used: str = None) -> ExecutionResult:
    """
    Run a command inside a Docker container natively.
    Separates build phase from test phase.
    """
    volume_args = ""
    if volumes:
        for host_path, container_path in volumes.items():
            abs_host_path = os.path.abspath(host_path)
            volume_args += f"-v {abs_host_path}:{container_path} "

    # 1. Execute Build Step
    if build_command:
        build_docker_cmd = f"docker run --rm {volume_args} -w /app {image} sh -c \"{build_command}\""
        build_result = execute_command_with_retry(build_docker_cmd, timeout=timeout, profile_used=profile_used)
        if not build_result.success:
            return ExecutionResult(
                success=False,
                stdout=build_result.stdout,
                stderr=f"Build Phase Failed: {build_result.stderr}",
                exit_code=build_result.exit_code,
                error="Build failure",
                profile_used=profile_used
            )

    # 2. Execute Test Step
    test_docker_cmd = f"docker run --rm {volume_args} -w /app {image} sh -c \"{test_command}\""
    return execute_command_with_retry(test_docker_cmd, timeout=timeout, profile_used=profile_used)
