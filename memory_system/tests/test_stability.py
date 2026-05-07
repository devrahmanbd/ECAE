import pytest
import os
import tempfile
import json
from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState
from memory_system.services.workspace_service import init_project
from memory_system.models.schemas import ExecutionResult
from memory_system.db.qdrant_client import init_collection
import memory_system.services.memory_service as mem_svc

def setup_module(module):
    init_collection()

def test_graph_refresh_after_changes():
    from memory_system.services.graph_service import get_graph_context
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        # Create a script with a dependency so it has a blast radius
        with open(os.path.join(tmpdir, "script1.py"), "w") as f:
            f.write("def func_a(): pass\n")
        with open(os.path.join(tmpdir, "script_dep.py"), "w") as f:
            f.write("from script1 import func_a\n\ndef func_dep():\n    func_a()\n")

        ctx1 = get_graph_context("script1.py", root_dir=tmpdir)
        assert ctx1.blast_radius > 0
        assert ctx1.status == "success"

        # Now simulate adding a new file that depends on script1
        with open(os.path.join(tmpdir, "script_dep2.py"), "w") as f:
            f.write("from script1 import func_a\n\ndef func_dep2():\n    func_a()\n")

        # Graph service actively walks ast on creation, so it should dynamically pick this up natively
        ctx2 = get_graph_context("script1.py", root_dir=tmpdir)
        assert ctx2.blast_radius > ctx1.blast_radius

def test_orchestrator_real_failure_state():
    """Verify orchestrator hits STOP state and writes memory on completely empty repo (no graph.json mocked)."""
    orchestrator = AgentOrchestrator()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't init project to ensure graph fails natively
        result = orchestrator.process_task("test natively", workspace_dir=tmpdir)

        assert result["status"] == "stop"
        assert result["reason"] == "Graph unavailable or stale"
        assert orchestrator.state == OrchestratorState.STOP

        # Verify failure memory was actually written to DB
        res = mem_svc.search_memory("No workspace detected")
        assert len(res) > 0
        assert res[0].metadata.outcome == "failure"

def test_sandbox_native_failure():
    """Verify that a native invalid command fails execution and produces structured results, not guesses."""
    from memory_system.services.execution_service import run_in_docker
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_in_docker(
            image="python:3.11-slim",
            build_command="echo 'building'",
            test_command="some_nonexistent_command_that_should_fail",
            volumes={tmpdir: "/app"},
            timeout=10
        )
        assert res.success is False
        assert res.exit_code != 0
        assert res.exit_code != 0 and len(res.stderr) > 0

def test_memory_duplicate_write_safety():
    """Verify memory layer safely handles identical massive string insertions without breaking integrity."""
    import uuid
    from memory_system.models.schemas import MemoryMetadata

    unique_str = f"massive collision string {uuid.uuid4()}"

    # First insert
    res1 = mem_svc.store_memory(unique_str, MemoryMetadata(outcome="success", confidence=1.0))
    assert res1 is not None

    # Concurrent/Duplicate insert attempt
    res2 = mem_svc.store_memory(unique_str, MemoryMetadata(outcome="success", confidence=1.0))

    # Duplicate insertion logic returns None and doesn't crash
    assert res2 is None

    # Ensure integrity remains (only 1 retrieved)
    hits = mem_svc.search_memory(unique_str)
    # The search matches by semantic distance, but exact duplicates shouldn't multiply
    assert len([h for h in hits if h.text == unique_str]) == 1

def test_graph_recovery_missing_target():
    """Verify graph layer correctly fails back to status not_found instead of crashing or stopping abruptly."""
    from memory_system.services.graph_service import get_graph_context
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        ctx = get_graph_context("completely_non_existent_function", root_dir=tmpdir)

        assert ctx.blast_radius == 0
        assert ctx.status == "not_found"
        assert len(ctx.impacted_dependencies) == 0
        assert ctx.graph_loaded is False # Graph is empty so graph_loaded resolves false

@pytest.mark.asyncio
async def test_mcp_dynamic_resolution_real():
    """Test dynamic workspace resolution actually triggers project init and doesn't rely on mock."""
    from memory_system.mcp_server import call_tool
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a marker that workspace service detects
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("pytest")

        with open(os.path.join(tmpdir, "script.py"), "w") as f:
            f.write("def dummy(): pass\n")

        # Natively invoke MCP tool
        res = await call_tool("get_graph_context", {
            "query": "script.py",
            "root_dir": tmpdir
        })

        assert len(res) == 1
        output = json.loads(res[0].text)

        # Ensure MCP tool resolved graph natively without manual init_project
        assert output["status"] == "not_found" # Blast radius is 0 for isolated dummy
        assert output["graph_loaded"] is True

def test_orchestrator_concurrency_state_isolation():
    """Verify multiple orchestrator instances do not share state."""
    orch1 = AgentOrchestrator()
    orch2 = AgentOrchestrator()

    assert orch1.state == OrchestratorState.WORKSPACE_CHECK

    with tempfile.TemporaryDirectory() as tmpdir:
        # Stop orch1
        orch1.process_task("fail task", "/path/invalid")
        assert orch1.state == OrchestratorState.STOP

        # orch2 should remain unaffected
        assert orch2.state == OrchestratorState.WORKSPACE_CHECK
