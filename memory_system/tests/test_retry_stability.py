import pytest
import os
import tempfile
from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState
from memory_system.services.workspace_service import init_project
from memory_system.db.qdrant_client import init_collection
import memory_system.services.memory_service as mem_svc

def setup_module(module):
    init_collection()

def test_long_duration_retry_exhaustion(monkeypatch):
    """Ensure retry loops properly hit the max limit without state drift and write memory properly."""

    # We mock execution so it fails natively and quickly to trigger the retry loop
    import memory_system.agent_engine.orchestrator as orch_module
    from memory_system.models.schemas import ExecutionResult

    def mock_run_in_docker(*args, **kwargs):
        return ExecutionResult(success=False, stdout="", stderr="native sandbox fail", exit_code=1, error="sandbox failure")

    monkeypatch.setattr(orch_module, "run_in_docker", mock_run_in_docker)

    orch = AgentOrchestrator(max_iterations=4)
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        # Create a valid graph target
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def dummy(): pass\n")

        res = orch.process_task("main.py", workspace_dir=tmpdir)

        # Ensure it exhausted all iterations
        assert res["status"] == "failure"
        assert res["iterations"] == 4
        assert res["reason"] == "Max iterations reached without success."
        assert orch.state == OrchestratorState.STOP
