from memory_system.tests.benchmarks.benchmark import compare_agents
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

def test_identical_task_comparison():
    # Test a complex task where the baseline should fail but ECAE should succeed or iterate to success

    # We mock execute command in execution service to ensure predictable testing
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    def mock_execute(command: str, workdir: str = ".", timeout: int = 60, profile_used: str = None):
        from memory_system.models.schemas import ExecutionResult
        # Simply intercept all commands and pretend they pass to avoid recursive pytest execution
        # which freezes the test suite when run_demo executes pytest inside the mock workspace sandbox.
        return ExecutionResult(success=True, stdout="mocked pass", stderr="", exit_code=0)

    exec_svc.execute_command = mock_execute
    try:
        # Complex task to trigger Graph Context risk
        result = compare_agents("Fix the complex API bug")

        # Baseline fails on complex task based on heuristic in compare_agents
        assert result["baseline"]["success"] is False
        assert result["baseline"]["repeated_mistakes"] > 0

        # ECAE should succeed (using graph context / memory to pick safe candidate)
        # Note: Since the test task doesn't map to actual code, blast_radius will be 0,
        # so it picks cand_1 (Standard fix) which we mocked to pass.
        assert result["ecae"]["success"] is True
        assert result["ecae"]["repeated_mistakes"] == 0

    finally:
        exec_svc.execute_command = original_exec

def test_reproducibility():
    import memory_system.services.execution_service as exec_svc
    original_exec = exec_svc.execute_command

    def mock_execute(command: str, workdir: str = ".", timeout: int = 60, profile_used: str = None):
        from memory_system.models.schemas import ExecutionResult
        # Complete mock to avoid running real tests or python scripts inside the benchmark sandbox
        return ExecutionResult(success=True, stdout="mocked pass", stderr="", exit_code=0)

    exec_svc.execute_command = mock_execute
    try:
        # Running the exact same benchmark twice should yield the exact same deterministic results for ECAE
        result1 = compare_agents("Reproducible task")
        result2 = compare_agents("Reproducible task")

        assert result1["ecae"]["success"] == result2["ecae"]["success"]
        assert result1["ecae"]["iterations"] == result2["ecae"]["iterations"]
    finally:
        exec_svc.execute_command = original_exec
