import pytest
import json
from memory_system.mcp_server import list_tools, list_prompts, call_tool
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

@pytest.mark.asyncio
async def test_mcp_list_tools():
    tools = await list_tools()
    assert len(tools) == 5
    tool_names = [t.name for t in tools]
    assert "ecae_cli" in tool_names
    assert "search_memory" in tool_names
    assert "get_graph_context" in tool_names
    assert "execute_command" in tool_names

@pytest.mark.asyncio
async def test_mcp_list_prompts():
    prompts = await list_prompts()
    assert len(prompts) == 1
    prompt = prompts[0]
    assert prompt.name == "agent_rules"

@pytest.mark.asyncio
async def test_mcp_call_search_memory():
    result = await call_tool("search_memory", {"query": "test query"})
    assert len(result) == 1
    assert result[0].type == "text"

@pytest.mark.asyncio
async def test_mcp_call_execute_command():
    # We mock execute command in execution service to avoid docker setup issues in tests
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    def mock_execute(command: str, workdir: str = ".", timeout: int = 60):
        cmd = command
        from memory_system.models.schemas import ExecutionResult
        return ExecutionResult(success=True, stdout="mocked pass", stderr="", exit_code=0)

    exec_svc.execute_command = mock_execute
    try:
        result = await call_tool("execute_command", {
            "test_command": "echo test",
            "build_command": "echo build"
        })
        assert len(result) == 1
        res_json = json.loads(result[0].text)
        assert res_json["success"] is True
        assert res_json["stdout"] == "mocked pass"
    finally:
        exec_svc.execute_command = original_exec

@pytest.mark.asyncio
async def test_mcp_dynamic_workspace_resolution(monkeypatch):
    import memory_system.services.workspace_service as ws_svc

    # Mock detect_workspace to return a known fake path
    def mock_detect(path="."):
        return "/fake/resolved/path"

    monkeypatch.setattr("memory_system.mcp_server.detect_workspace", mock_detect)

    # Mock execute_command to see what volume it gets
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.run_in_docker

    passed_volumes = {}

    def mock_run_in_docker(image, build_command, test_command, volumes, timeout=60):
        nonlocal passed_volumes
        passed_volumes = volumes
        from memory_system.models.schemas import ExecutionResult
        return ExecutionResult(success=True, stdout="mocked", stderr="", exit_code=0)

    monkeypatch.setattr("memory_system.mcp_server.run_in_docker", mock_run_in_docker)

    # Run the tool
    result = await call_tool("execute_command", {
        "test_command": "echo test"
    })

    # Verify the tool correctly used detect_workspace result for mounting
    import os
    expected_path = os.path.abspath("/fake/resolved/path")
    assert expected_path in passed_volumes
    assert passed_volumes[expected_path] == "/app"
