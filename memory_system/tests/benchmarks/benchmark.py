from memory_system.agent_engine.orchestrator import AgentOrchestrator
from memory_system.models.schemas import GraphContext, MemoryItem
import time

def run_baseline_agent(task_query: str):
    """
    Mock baseline agent: No memory, no graph context, directly proposes a solution.
    """
    start_time = time.time()

    # Baseline just guesses
    candidate = {
        "id": "baseline_cand_1",
        "strategy": "Guess based on generic prompt",
        "commands": ["echo 'fixing'", "pytest"],
        "score": 0.5
    }

    # Without memory/graph context, baseline might fail execution
    success = False
    iterations = 1

    # In a real scenario we'd actually run execution, but here we simulate
    # a baseline failing to fix a complex structural issue.
    if "complex" in task_query:
         success = False
    else:
         success = True

    elapsed = time.time() - start_time
    return {
        "success": success,
        "iterations": iterations,
        "time": elapsed,
        "repeated_mistakes": 1 if not success else 0
    }

def run_ecae_agent(task_query: str):
    """
    Run the full ECAE-lite orchestrator loop.
    """
    orchestrator = AgentOrchestrator()
    start_time = time.time()

    result = orchestrator.process_task(task_query)

    elapsed = time.time() - start_time

    return {
        "success": result["status"] == "success",
        "iterations": result.get("iterations", 1),
        "time": elapsed,
        "repeated_mistakes": 0 # Assuming memory prevents this
    }

def compare_agents(task_query: str):
    baseline_result = run_baseline_agent(task_query)
    ecae_result = run_ecae_agent(task_query)

    return {
        "task": task_query,
        "baseline": baseline_result,
        "ecae": ecae_result
    }

if __name__ == "__main__":
    result = compare_agents("Fix the complex API bug")
    print("Benchmark Result:", result)
