from memory_system.agent_engine.orchestrator import AgentOrchestrator
from memory_system.db.qdrant_client import init_collection
import tempfile
import os

def setup_module(module):
    init_collection()

def test_orchestrator_execution_order_and_success():
    orchestrator = AgentOrchestrator()

    # We mock out execute_command so it passes without trying to pull a docker image
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    def mock_execute(command: str, workdir: str = ".", timeout: int = 60):
        cmd = command
        from memory_system.models.schemas import ExecutionResult
        return ExecutionResult(success=True, stdout="passed mock", stderr="", exit_code=0)

    exec_svc.execute_command = mock_execute

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = orchestrator.process_task("test valid execution", workspace_dir=tmpdir)

            assert result["status"] == "success"
            assert result["selected_candidate"] is not None
            assert result["execution"]["success"] is True
            assert result["iterations"] == 1
    finally:
        exec_svc.execute_command = original_exec

def test_orchestrator_failure_recovery_behavior():
    # Set max iterations low to speed up test
    orchestrator = AgentOrchestrator(max_iterations=2)

    # We mock out execute_command so it fails every time
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    attempts = 0
    def mock_execute(command: str, workdir: str = ".", timeout: int = 60):
        cmd = command
        nonlocal attempts
        from memory_system.models.schemas import ExecutionResult
        # Only count main test/build phase executions (not setup rm/cp ones)
        if "rm -rf" not in cmd:
            attempts += 1
        return ExecutionResult(success=False, stdout="", stderr="failed mock", exit_code=1)

    exec_svc.execute_command = mock_execute

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = orchestrator.process_task("test invalid execution", workspace_dir=tmpdir)

            assert result["status"] == "failure"
            assert result["iterations"] == 2
            # Total attempts should be high because each loop does a build + test attempt,
            # but fundamentally we verify it looped.
            assert attempts >= 2
    finally:
        exec_svc.execute_command = original_exec
