from memory_system.agent_engine.orchestrator import AgentOrchestrator
from memory_system.db.qdrant_client import init_collection
import tempfile
import os

def setup_module(module):
    init_collection()

def test_orchestrator_execution_order_and_success():
    orchestrator = AgentOrchestrator()

    # We mock out execute_command so it passes without trying to pull a docker image
    import memory_system.agent_engine.orchestrator as orch_module
    original_exec = orch_module.run_in_docker

    def mock_execute(image: str, build_command: str, test_command: str, volumes: dict, timeout: int = 60):
        cmd = test_command
        from memory_system.models.schemas import ExecutionResult
        return ExecutionResult(success=True, stdout="passed mock", stderr="", exit_code=0)

    orch_module.run_in_docker = mock_execute

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = orchestrator.process_task("test valid execution", workspace_dir=tmpdir)

            assert result["status"] == "success"
            assert result["selected_candidate"] is not None
            assert result["execution"]["success"] is True
            assert result["iterations"] == 1
    finally:
        orch_module.run_in_docker = original_exec

def test_orchestrator_failure_recovery_behavior():
    # Set max iterations low to speed up test
    orchestrator = AgentOrchestrator(max_iterations=2)

    # We mock out execute_command so it fails every time
    import memory_system.agent_engine.orchestrator as orch_module
    original_exec = orch_module.run_in_docker

    attempts = 0
    def mock_execute(image: str, build_command: str, test_command: str, volumes: dict, timeout: int = 60):
        cmd = test_command
        nonlocal attempts
        from memory_system.models.schemas import ExecutionResult
        # Only count main test/build phase executions (not setup rm/cp ones)
        if "rm -rf" not in cmd:
            attempts += 1
        return ExecutionResult(success=False, stdout="", stderr="failed mock", exit_code=1)

    orch_module.run_in_docker = mock_execute

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = orchestrator.process_task("test invalid execution", workspace_dir=tmpdir)

            assert result["status"] == "failure"
            assert result["iterations"] == 2
            # Total attempts should be high because each loop does a build + test attempt,
            # but fundamentally we verify it looped.
            assert attempts >= 2
    finally:
        orch_module.run_in_docker = original_exec
