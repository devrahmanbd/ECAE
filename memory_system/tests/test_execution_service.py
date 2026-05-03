from memory_system.services.execution_service import execute_command

def test_execution_sandbox():
    result = execute_command("echo hello")
    assert result["success"] is True
    assert "hello" in result["stdout"]

    result_fail = execute_command("ls non_existent_file")
    assert result_fail["success"] is False
    assert result_fail["stderr"] != ""

    result_cd = execute_command("cd /")
    assert result_cd["success"] is False
    assert "forbidden" in result_cd["error"]

def test_execution_timeout():
    result = execute_command("sleep 65")
    assert result["success"] is False
    assert "timed out" in result["error"]
