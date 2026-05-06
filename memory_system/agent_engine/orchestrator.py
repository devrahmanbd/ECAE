from typing import Dict, Any, List
import os
from enum import Enum
from memory_system.models.schemas import GraphContext, MemoryMetadata
from memory_system.services.graph_service import get_graph_context
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.execution_service import run_in_docker
from memory_system.agent_engine.decision_engine import DecisionEngine
from rich.console import Console

console = Console()

class OrchestratorState(Enum):
    IDLE = 0
    WORKSPACE_CHECK = 1
    FETCH_GRAPH_CONTEXT = 2
    FETCH_MEMORY = 3
    PLAN_AND_BRANCH = 4
    SANDBOX_EXECUTION = 5
    STORE_MEMORY = 6
    STOP = 7

class AgentOrchestrator:
    def __init__(self, max_iterations: int = 3):
        self.state = OrchestratorState.IDLE
        self.decision_engine = DecisionEngine()
        self.max_iterations = max_iterations

    def _record_failure(self, task_query: str, reason: str, tags: List[str]):
        """Helper to ensure memory is written on EVERY stop, exception, and failure."""
        console.print(f"[bold red]Recording Failure Memory: {reason}[/bold red]")
        store_memory(
            text=f"Outcome for task: {task_query} resulted in failure: {reason}",
            metadata=MemoryMetadata(
                memory_type="causal",
                outcome="failure",
                reasoning=reason,
                tags=tags,
                confidence=1.0
            )
        )

    def process_task(self, task_query: str, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Executes the predictive engineering loop with repeat.
        """
        console.print(f"[bold blue]Starting Task:[/bold blue] {task_query}")

        self.state = OrchestratorState.WORKSPACE_CHECK
        if not os.path.exists(workspace_dir):
            reason = "No workspace detected"
            self._record_failure(task_query, reason, ["workspace_error"])
            self.state = OrchestratorState.STOP
            return {"status": "stop", "reason": reason}

        iteration = 0
        past_memories = []

        while iteration < self.max_iterations:
            iteration += 1
            console.print(f"\n[bold magenta]=== Iteration {iteration}/{self.max_iterations} ===[/bold magenta]")

            # Phase: Graph First
            self.state = OrchestratorState.FETCH_GRAPH_CONTEXT
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Fetching dependency graph...")
            try:
                graph_context = get_graph_context(task_query, root_dir=workspace_dir)
                if graph_context.status == "exception" or not graph_context.graph_loaded:
                    raise Exception("Graph unavailable or stale")
            except Exception as e:
                reason = "Graph unavailable or stale"
                self._record_failure(task_query, reason, ["graph_error"])
                self.state = OrchestratorState.STOP
                return {"status": "stop", "reason": reason}
            console.print(f"[dim]Impacted Dependencies: {len(graph_context.impacted_dependencies or [])}[/dim]")

            # Phase: Memory Second
            self.state = OrchestratorState.FETCH_MEMORY
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Checking Qdrant for past experiences...")
            try:
                past_memories = search_memory(task_query)
            except Exception:
                reason = "Memory layer unavailable"
                self._record_failure(task_query, reason, ["memory_error"])
                self.state = OrchestratorState.STOP
                return {"status": "stop", "reason": reason}
            console.print(f"[dim]Found {len(past_memories)} relevant past memories.[/dim]")

            # Phase: Planning (Predict, Filter, Optimize, Generate)
            self.state = OrchestratorState.PLAN_AND_BRANCH
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Generating candidate fixes...")

            try:
                best_candidate = self.decision_engine.evaluate_and_select(task_query, graph_context, past_memories)
                if not best_candidate:
                    console.print("[bold red]No safe candidates found. Rejecting task.[/bold red]")
                    self._record_failure(task_query, "No safe candidates.", ["planning_rejection"])
                    return {"status": "rejected", "reason": "No safe candidates.", "iterations": iteration}
            except Exception:
                reason = "Tool call failed or returned malformed output"
                self._record_failure(task_query, reason, ["tool_error"])
                self.state = OrchestratorState.STOP
                return {"status": "stop", "reason": reason}

            console.print(f"[bold green]Selected Candidate:[/bold green] {best_candidate.id} with utility score {best_candidate.score}")

            # Phase: Execution Third
            self.state = OrchestratorState.SANDBOX_EXECUTION
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Testing candidates in isolated Docker sandbox...")

            abs_workspace = os.path.abspath(workspace_dir)
            volumes = {abs_workspace: "/app"}

            build_command = best_candidate.commands[0] if len(best_candidate.commands) > 0 else ""
            test_command = "pytest"

            try:
                execution_result = run_in_docker(
                    image="python:3.11-slim",
                    build_command=build_command,
                    test_command=test_command,
                    volumes=volumes,
                    timeout=30
                )
            except Exception:
                reason = "Execution sandbox unavailable"
                self._record_failure(task_query, reason, ["sandbox_error"])
                self.state = OrchestratorState.STOP
                return {"status": "stop", "reason": reason}

            # Phase: Learn
            self.state = OrchestratorState.STORE_MEMORY
            outcome_status = "success" if execution_result.success else "failure"
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Recording experience to Causal Experience Graph (Qdrant)...")

            store_memory(
                text=f"Outcome for task: {task_query} using strategy: {best_candidate.strategy}",
                metadata=MemoryMetadata(
                    memory_type="causal",
                    decision=best_candidate.strategy,
                    outcome=outcome_status,
                    tags=["execution_feedback"],
                    confidence=best_candidate.score
                )
            )

            if execution_result.success:
                console.print(f"[green]✔ {best_candidate.id} passed execution sandbox.[/green]")
                self.state = OrchestratorState.IDLE
                console.print("[bold blue]Task Complete - Success[/bold blue]")
                return {
                    "status": "success",
                    "selected_candidate": best_candidate.model_dump(),
                    "execution": execution_result.model_dump(),
                    "memories_used": len(past_memories),
                    "iterations": iteration
                }
            else:
                console.print(f"[red]✘ {best_candidate.id} failed execution sandbox.[/red]")
                console.print(f"[dim]{execution_result.stderr}[/dim]")
                console.print("[bold yellow]Execution failed. Repeating loop...[/bold yellow]")

        self.state = OrchestratorState.IDLE
        console.print("[bold red]Task Complete - Failure (Max iterations reached)[/bold red]")

        # Write final failure due to timeout/iteration limit
        self._record_failure(task_query, "Max iterations reached without success.", ["iteration_limit"])

        return {
            "status": "failure",
            "reason": "Max iterations reached without success.",
            "iterations": iteration,
            "memories_used": len(past_memories)
        }
