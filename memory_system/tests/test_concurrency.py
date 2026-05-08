import pytest
import os
import tempfile
from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState

def test_multiple_workspaces_sequential():
    orch = AgentOrchestrator()
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        # Task 1 fails gracefully
        res1 = orch.process_task("task1", workspace_dir=tmp1)
        assert orch.state == OrchestratorState.STOP

        # We need to ensure state is reset when processing new task
        res2 = orch.process_task("task2", workspace_dir=tmp2)
        assert orch.state == OrchestratorState.STOP
        assert res1["reason"] == "Graph unavailable or stale" # Ensure we didn't return cached garbage

def test_rapid_orchestrator_initialization():
    orch1 = AgentOrchestrator()
    orch2 = AgentOrchestrator()
    orch3 = AgentOrchestrator()

    assert orch1.state == OrchestratorState.WORKSPACE_CHECK
    assert orch2.state == OrchestratorState.WORKSPACE_CHECK
    assert orch3.state == OrchestratorState.WORKSPACE_CHECK

    # Mutating one doesn't affect others
    orch1.state = OrchestratorState.STOP
    assert orch2.state == OrchestratorState.WORKSPACE_CHECK
    assert orch3.state == OrchestratorState.WORKSPACE_CHECK
