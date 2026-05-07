from memory_system.core.logger import logger
import subprocess
import os
from memory_system.models.schemas import ExecutionResult
from memory_system.services.profile_service import get_profile_config, extract_stack_trace


def execute_command(command: str, workdir: str = ".", timeout: int = 60) -> ExecutionResult:
    """
    Execute a command in a subprocess.
    """
    try:
        # Simple security check: prevent cd outside sandbox bounds
        if "cd " in command and not "cd /tmp" in command and not "cd /app" in command:
            return ExecutionResult(success=False, stdout="", stderr="", error="cd command is forbidden. Use workdir parameter instead.")

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
            exit_code=result.returncode
        )

    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out: {command}")
        return ExecutionResult(success=False, stdout="", stderr="", error=f"Command timed out after {timeout} seconds.")
    except Exception as e:
        logger.error(f"Command failed with exception: {str(e)}")
        return ExecutionResult(success=False, stdout="", stderr="", error=str(e))

import time

def execute_command_with_retry(command: str, workdir: str = ".", timeout: int = 60, retries: int = 2) -> ExecutionResult:
    attempt = 0
    while attempt <= retries:
        result = execute_command(command, workdir, timeout)
        if result.success or (result.error and "forbidden" in result.error): # Don't retry security errors
            return result
        attempt += 1
        if attempt <= retries:
            logger.warning(f"Command failed, retrying ({attempt}/{retries})...")
            time.sleep(1)
    return result

def run_in_docker(image: str, build_command: str, test_command: str, volumes: dict = None, timeout: int = 60) -> ExecutionResult:
    """
    Run a command inside a Docker container natively.
    Separates build phase from test phase.
    """
    volume_args = ""
    if volumes:
        for host_path, container_path in volumes.items():
            abs_host_path = os.path.abspath(host_path)
            volume_args += f"-v {abs_host_path}:{container_path} "

    # Extract profile from workspace if volumes are mapped to determine proper image/commands natively
    profile_name = "unknown"
    workspace_dir = "."
    if volumes:
        workspace_dir = list(volumes.keys())[0]
        config = get_profile_config(workspace_dir)
        profile_name = config["name"]

        # Override if specific overrides weren't provided manually
        if image == "python:3.11-slim" and profile_name != "unknown":
            image = config["image"]

    # 1. Execute Build Step
    if build_command:
        build_docker_cmd = f"docker run --rm {volume_args} -w /app {image} sh -c \"{build_command}\""
        build_result = execute_command_with_retry(build_docker_cmd, timeout=timeout)
        if not build_result.success:
            return ExecutionResult(
                success=False,
                stdout=build_result.stdout,
                stderr=f"Build Phase Failed: {build_result.stderr}",
                exit_code=build_result.exit_code,
                error="Build failure",
                profile_used=profile_name,
                failing_stage="build",
                stack_trace=extract_stack_trace(build_result.stderr)
            )

    # 2. Execute Test Step
    test_docker_cmd = f"docker run --rm {volume_args} -w /app {image} sh -c \"{test_command}\""
    test_result = execute_command_with_retry(test_docker_cmd, timeout=timeout)

    # Enrich result with crash envelope
    test_result.profile_used = profile_name
    if not test_result.success:
        test_result.failing_stage = "test"
        test_result.stack_trace = extract_stack_trace(test_result.stderr)
        return test_result

    # 3. Validation Gate
    validation_cmd = config.get("validation_cmd") if profile_name != "unknown" else None
    if validation_cmd:
        valid_docker_cmd = f"docker run --rm {volume_args} -w /app {image} sh -c \"{validation_cmd}\""
        valid_result = execute_command_with_retry(valid_docker_cmd, timeout=timeout)
        if not valid_result.success:
            return ExecutionResult(
                success=False,
                stdout=test_result.stdout + "\nVALIDATION OUT:\n" + valid_result.stdout,
                stderr=test_result.stderr + "\nVALIDATION ERR:\n" + valid_result.stderr,
                exit_code=valid_result.exit_code,
                error="Validation Gate failure",
                profile_used=profile_name,
                failing_stage="validation",
                stack_trace=extract_stack_trace(valid_result.stderr)
            )

    return test_result
