import pytest
import os
import tempfile
from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState
from memory_system.services.workspace_service import init_project
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

def test_missing_workspace_stops_safely():
    orch = AgentOrchestrator()
    res = orch.process_task("test task", workspace_dir="/path/that/absolutely/does/not/exist")
    assert res["status"] == "stop"
    assert "No workspace detected" in res["reason"]
    assert orch.state == OrchestratorState.STOP

def test_missing_graph_safely_stops():
    orch = AgentOrchestrator()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't init project -> graph build fails internally if it can't find files
        res = orch.process_task("test task", workspace_dir=tmpdir)
        assert res["status"] == "stop"
        assert "Graph unavailable or stale" in res["reason"]
        assert orch.state == OrchestratorState.STOP

def test_malformed_memory_read_stops(monkeypatch):
    # Mock external infra (Qdrant client) instead of internal agent loop logic
    import memory_system.services.memory_service as mem_svc
    def mock_query(*args, **kwargs):
        raise ValueError("Simulated Qdrant Connection Error")

    # We now lazily get the client, so we must mock get_client() to return a mock client
    class MockClient:
        def query_points(self, *args, **kwargs):
            raise ValueError("Simulated Qdrant Connection Error")

        def upsert(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mem_svc, "get_client", lambda: MockClient())

    orch = AgentOrchestrator()
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def dummy(): pass\n")
        res = orch.process_task("test task", workspace_dir=tmpdir)
        assert res["status"] == "stop"
        assert "Memory layer unavailable" in res["reason"] or "Graph unavailable or stale" in res["reason"]
        assert orch.state == OrchestratorState.STOP
