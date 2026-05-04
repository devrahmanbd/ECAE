from memory_system.services.execution_service import execute_command, run_in_docker

def test_execution_sandbox():
    result = execute_command("echo hello")
    assert result.success is True
    assert "hello" in result.stdout

    result_fail = execute_command("ls non_existent_file")
    assert result_fail.success is False
    assert result_fail.stderr != ""

def test_execution_timeout():
    # Use a small timeout for testing
    result = execute_command("sleep 2", timeout=1)
    assert result.success is False
    assert "timed out" in result.error

def test_separated_build_and_test():
    # Since we can't reliably pull docker images in the sandbox, we mock the subprocess command
    # for Docker tests by replacing `docker run` natively if needed, but we will test the logic
    # of the `run_in_docker` wrapper separating build and test outputs.

    # Provide a failing build command via our wrapper
    # We use alpine:latest but command won't run natively due to pull limits so we patch it dynamically for test
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    def mock_execute(command: str, workdir: str = ".", timeout: int = 60):
        cmd = command
        from memory_system.models.schemas import ExecutionResult
        if "false" in cmd:
            return ExecutionResult(success=False, stdout="", stderr="command failed", exit_code=1)
        if "true" in cmd:
            return ExecutionResult(success=True, stdout="passed", stderr="", exit_code=0)
        return original_exec(cmd, **kwargs)

    exec_svc.execute_command = mock_execute

    try:
        build_fail_result = run_in_docker(
            image="alpine:latest",
            build_command="false",
            test_command="true"
        )
        assert build_fail_result.success is False
        assert "Build Phase Failed" in build_fail_result.stderr

        success_result = run_in_docker(
            image="alpine:latest",
            build_command="true",
            test_command="true"
        )
        assert success_result.success is True
        assert "passed" in success_result.stdout
    finally:
        exec_svc.execute_command = original_exec
