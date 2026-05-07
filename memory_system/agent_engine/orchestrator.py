from typing import Dict, Any, List
import os
from enum import Enum
from memory_system.services.workspace_service import get_execution_profile
from memory_system.models.schemas import GraphContext, MemoryMetadata, CandidatePlan
from memory_system.services.graph_service import get_graph_context
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.execution_service import run_in_docker
from memory_system.agent_engine.decision_engine import DecisionEngine
from rich.console import Console

console = Console()

class OrchestratorState(Enum):
    WORKSPACE_CHECK = 1
    GRAPH_LOAD = 2
    MEMORY_LOAD = 3
    PREDICT = 4
    FILTER = 5
    OPTIMIZE = 6
    GENERATE = 7
    EXECUTE = 8
    RESULT = 9
    LEARN = 10
    STOP = 11

class AgentOrchestrator:
    def __init__(self, max_iterations: int = 3):
        self.state = OrchestratorState.WORKSPACE_CHECK
        self.decision_engine = DecisionEngine()
        self.max_iterations = max_iterations

    def _record_failure(self, task_query: str, reason: str, tags: List[str]):
        """Helper to ensure memory is written on EVERY stop, exception, and failure."""
        console.print(f"[bold red]Recording Failure Memory: {reason}[/bold red]")
        try:
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
        except Exception as e:
            console.print(f"[bold red]FATAL: Memory layer unavailable during failure record: {e}[/bold red]")
            # If memory cannot be written -> STOP immediately
        self.state = OrchestratorState.STOP

    def process_task(self, task_query: str, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Executes the deterministic state machine loop.
        Predict -> Filter -> Optimize -> Generate -> Execute -> Result -> Learn
        """
        console.print(f"[bold blue]Starting Task:[/bold blue] {task_query}")

        self.state = OrchestratorState.WORKSPACE_CHECK
        if not os.path.exists(workspace_dir):
            reason = "No workspace detected"
            self._record_failure(task_query, reason, ["workspace_error"])
            return {"status": "stop", "reason": reason}

        iteration = 0
        past_memories = []

        while iteration < self.max_iterations:
            iteration += 1
            console.print(f"\n[bold magenta]=== Iteration {iteration}/{self.max_iterations} ===[/bold magenta]")

            # 1. GRAPH LOAD
            self.state = OrchestratorState.GRAPH_LOAD
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Fetching dependency graph...")
            try:
                graph_context = get_graph_context(task_query, root_dir=workspace_dir)
                if graph_context.status == "exception" or not graph_context.graph_loaded:
                    raise Exception("Graph unavailable or stale")
            except Exception as e:
                reason = "Graph unavailable or stale"
                self._record_failure(task_query, reason, ["graph_error"])
                return {"status": "stop", "reason": reason}
            console.print(f"[dim]Impacted Dependencies: {len(graph_context.impacted_dependencies or [])}[/dim]")

            # 2. MEMORY LOAD
            self.state = OrchestratorState.MEMORY_LOAD
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Checking Qdrant for past experiences...")
            try:
                past_memories = search_memory(task_query)
            except Exception:
                reason = "Memory layer unavailable"
                self._record_failure(task_query, reason, ["memory_error"])
                return {"status": "stop", "reason": reason}
            console.print(f"[dim]Found {len(past_memories)} relevant past memories.[/dim]")

            # 3. PREDICT
            self.state = OrchestratorState.PREDICT
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Predicting candidates...")
            try:
                raw_candidates = self.decision_engine.generate_candidates(task_query, graph_context, past_memories)
            except Exception:
                reason = "Tool call failed or returned malformed output"
                self._record_failure(task_query, reason, ["tool_error"])
                return {"status": "stop", "reason": reason}

            # 4. FILTER
            self.state = OrchestratorState.FILTER
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Filtering unsafe paths...")
            try:
                evaluated = []
                for cand in raw_candidates:
                    evaluated.append(self.decision_engine.apply_constraints(cand, graph_context, past_memories))
                safe_candidates = [c for c in evaluated if c.safe]
                if not safe_candidates:
                    reason = "No safe candidates found"
                    self._record_failure(task_query, reason, ["filter_rejection"])
                    return {"status": "stop", "reason": reason}
            except Exception:
                reason = "Tool call failed or returned malformed output"
                self._record_failure(task_query, reason, ["tool_error"])
                return {"status": "stop", "reason": reason}

            # 5. OPTIMIZE
            self.state = OrchestratorState.OPTIMIZE
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Optimizing selection...")
            best_candidate = max(safe_candidates, key=lambda c: c.score)

            # 6. GENERATE
            self.state = OrchestratorState.GENERATE
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Generating concrete execution steps...")

            # Fetch execution profile
            profile = get_execution_profile(workspace_dir)
            if profile.language == "unknown":
                reason = "Missing execution profile"
                self._record_failure(task_query, reason, ["profile_error"])
                return {"status": "stop", "reason": reason}

            build_command = best_candidate.commands[0] if len(best_candidate.commands) > 0 else ""
            test_command = profile.validation_command

            # 7. EXECUTE
            self.state = OrchestratorState.EXECUTE
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Testing candidate in isolated Docker sandbox...")
            abs_workspace = os.path.abspath(workspace_dir)
            volumes = {abs_workspace: "/app"}

            try:
                execution_result = run_in_docker(
                    image=profile.docker_image,
                    build_command=build_command,
                    test_command=test_command,
                    volumes=volumes,
                    timeout=30,
                    profile_used=profile.language
                )
            except Exception:
                reason = "Execution sandbox unavailable"
                self._record_failure(task_query, reason, ["sandbox_error"])
                return {"status": "stop", "reason": reason}

            # 8. RESULT
            self.state = OrchestratorState.RESULT
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Reading result...")
            outcome_status = "success" if execution_result.success else "failure"
            if execution_result.success:
                console.print(f"[green]✔ {best_candidate.id} passed execution sandbox.[/green]")
            else:
                console.print(f"[red]✘ {best_candidate.id} failed execution sandbox.[/red]")
                console.print(f"[dim]{execution_result.stderr}[/dim]")

            # 9. LEARN
            self.state = OrchestratorState.LEARN
            console.print(f"[bold yellow]State: {self.state.name}[/bold yellow] - Learning from {outcome_status}...")

            try:
                store_memory(
                    text=f"Outcome for task: {task_query} using strategy: {best_candidate.strategy}",
                    metadata=MemoryMetadata(
                        memory_type="causal",
                        decision=best_candidate.strategy,
                        outcome=outcome_status,
                        tags=["execution_feedback", f"profile_used:{execution_result.profile_used}"],
                        confidence=best_candidate.score
                    )
                )
            except Exception as e:
                console.print(f"[bold red]FATAL: Memory layer unavailable during learning: {e}[/bold red]")
                self.state = OrchestratorState.STOP
                return {"status": "stop", "reason": "Memory layer unavailable"}

            if execution_result.success:
                console.print("[bold blue]Task Complete - Success[/bold blue]")
                return {
                    "status": "success",
                    "selected_candidate": best_candidate.model_dump(),
                    "execution": execution_result.model_dump(),
                    "memories_used": len(past_memories),
                    "iterations": iteration
                }
            else:
                console.print("[bold yellow]Execution failed. Repeating loop...[/bold yellow]")

        self.state = OrchestratorState.STOP
        console.print("[bold red]Task Complete - Failure (Max iterations reached)[/bold red]")

        # Write final failure due to timeout/iteration limit
        self._record_failure(task_query, "Max iterations reached without success.", ["iteration_limit"])

        return {
            "status": "failure",
            "reason": "Max iterations reached without success.",
            "iterations": iteration,
            "memories_used": len(past_memories)
        }
