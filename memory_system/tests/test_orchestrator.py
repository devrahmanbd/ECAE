from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState
from memory_system.db.qdrant_client import init_collection
import tempfile
import os
from memory_system.services.workspace_service import init_project
import pytest

def setup_module(module):
    init_collection()

def test_orchestrator_stop_condition_workspace(monkeypatch):
    orchestrator = AgentOrchestrator()

    # Spy on search_memory to ensure it gets called by _record_failure
    import memory_system.services.memory_service as mem_svc
    mem_calls = []
    original_store = mem_svc.store_memory
    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)
    import memory_system.agent_engine.orchestrator as orch_module
    monkeypatch.setattr(orch_module, "store_memory", mock_store)

    result = orchestrator.process_task("test workspace", workspace_dir="/path/that/does/not/exist/for/test")

    assert result["status"] == "stop"
    assert result["reason"] == "No workspace detected"
    assert orchestrator.state == OrchestratorState.STOP
    assert len(mem_calls) == 1
    assert mem_calls[0]["metadata"].outcome == "failure"

def test_orchestrator_stop_condition_graph(monkeypatch):
    orchestrator = AgentOrchestrator()

    # Spy on store_memory
    import memory_system.services.memory_service as mem_svc
    mem_calls = []
    original_store = mem_svc.store_memory
    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)
    import memory_system.agent_engine.orchestrator as orch_module
    monkeypatch.setattr(orch_module, "store_memory", mock_store)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a workspace file so it passes WORKSPACE_CHECK
        with open(os.path.join(tmpdir, ".git"), "w") as f: f.write("")
        # We do NOT run init_project, so graph context should fail/be stale
        result = orchestrator.process_task("test graph fail", workspace_dir=tmpdir)

        assert result["status"] == "stop"
        assert result["reason"] == "Graph unavailable or stale"
        assert orchestrator.state == OrchestratorState.STOP
        assert len(mem_calls) == 1
        assert mem_calls[0]["metadata"].outcome == "failure"

def test_orchestrator_stop_condition_sandbox(monkeypatch):
    import memory_system.agent_engine.orchestrator as orch_module

    def mock_run_in_docker(*args, **kwargs):
        raise Exception("Docker failed")

    monkeypatch.setattr(orch_module, "run_in_docker", mock_run_in_docker)

    # Spy on store_memory
    import memory_system.services.memory_service as mem_svc
    mem_calls = []
    original_store = mem_svc.store_memory
    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)
    import memory_system.agent_engine.orchestrator as orch_module
    monkeypatch.setattr(orch_module, "store_memory", mock_store)

    orchestrator = AgentOrchestrator()
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        with open(os.path.join(tmpdir, "main.py"), "w") as f: f.write("def dummy(): pass\n")
        init_project(tmpdir)

        result = orchestrator.process_task("test sandbox fail", workspace_dir=tmpdir)

        assert result["status"] == "stop"
        assert result["reason"] == "Execution sandbox unavailable"
        assert orchestrator.state == OrchestratorState.STOP
        assert len(mem_calls) == 1
        assert mem_calls[0]["metadata"].outcome == "failure"

def test_orchestrator_real_loop_execution(monkeypatch):
    orchestrator = AgentOrchestrator(max_iterations=1)

    # Spy on store_memory to ensure it writes failure on reaching max iterations
    import memory_system.services.memory_service as mem_svc
    mem_calls = []
    original_store = mem_svc.store_memory
    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)
    import memory_system.agent_engine.orchestrator as orch_module
    monkeypatch.setattr(orch_module, "store_memory", mock_store)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def dummy(): pass\n")

        init_project(tmpdir)

        # Test full loop by querying the dummy node
        result = orchestrator.process_task("main.py", workspace_dir=tmpdir)

        # We know real pytest in an empty dir with no tests will fail execution and hit max iterations.
        # But this tests the entire state sequence runs WITHOUT hitting a stop condition.
        assert result["status"] == "failure"
        assert result["iterations"] == 1
        if "memories_used" in result:
            assert result["memories_used"] >= 0

        # It should have written memory twice:
        # Once per iteration (STORE_MEMORY state failure)
        # And once for exhausting iterations (Max iterations reached)
        assert len(mem_calls) == 2
        assert mem_calls[0]["metadata"].outcome == "failure"
        assert mem_calls[1]["metadata"].outcome == "failure"

def test_orchestrator_real_loop_success(monkeypatch):
    orchestrator = AgentOrchestrator(max_iterations=1)

    import memory_system.services.memory_service as mem_svc
    mem_calls = []
    original_store = mem_svc.store_memory
    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)

    import memory_system.agent_engine.orchestrator as orch_module
    monkeypatch.setattr(orch_module, "store_memory", mock_store)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a passing test file so pytest execution succeeds natively without mocks
        with open(os.path.join(tmpdir, "test_main.py"), "w") as f:
            f.write("def test_dummy(): assert True\n")

        init_project(tmpdir)

        # Mocking the external sandbox barrier so the test can proceed cleanly through the orchestrator success states
        def mock_run_in_docker(*args, **kwargs):
            from memory_system.models.schemas import ExecutionResult
            return ExecutionResult(success=True, stdout="passed", stderr="", exit_code=0)

        monkeypatch.setattr(orch_module, "run_in_docker", mock_run_in_docker)

        result = orchestrator.process_task("test_main.py", workspace_dir=tmpdir)

        # It should succeed entirely through the state machine.
        assert result["status"] == "success"
        assert result["iterations"] == 1
        assert "memories_used" in result

        # Should have written success memory once
        assert len(mem_calls) == 1
        assert mem_calls[0]["metadata"].outcome == "success"
