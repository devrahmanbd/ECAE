from typing import Dict, Any, List
import os
from memory_system.models.schemas import GraphContext, MemoryMetadata
from memory_system.services.graph_service import get_graph_context
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.execution_service import run_in_docker
from memory_system.agent_engine.decision_engine import DecisionEngine
from rich.console import Console

console = Console()

class AgentOrchestrator:
    def __init__(self, max_iterations: int = 3):
        self.state = "IDLE"
        self.decision_engine = DecisionEngine()
        self.max_iterations = max_iterations

    def process_task(self, task_query: str, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Executes the predictive engineering loop (Phases 4-7) with repeat.
        """
        console.print(f"[bold blue]Starting Task:[/bold blue] {task_query}")

        iteration = 0
        past_memories = []

        while iteration < self.max_iterations:
            iteration += 1
            console.print(f"\n[bold magenta]=== Iteration {iteration}/{self.max_iterations} ===[/bold magenta]")

            # State 1: Fetch Graph Context
            self.state = "FETCH_GRAPH_CONTEXT"
            console.print(f"[bold yellow]State 1: {self.state}[/bold yellow] - Fetching dependency graph...")
            graph_context = get_graph_context(task_query, root_dir=workspace_dir)
            console.print(f"[dim]Impacted Dependencies: {len(graph_context.impacted_dependencies or [])}[/dim]")

            # State 2: Fetch Memory
            self.state = "FETCH_MEMORY"
            console.print(f"[bold yellow]State 2: {self.state}[/bold yellow] - Checking Qdrant for past experiences...")
            past_memories = search_memory(task_query)
            console.print(f"[dim]Found {len(past_memories)} relevant past memories.[/dim]")

            # State 3: Plan & Branch (Decision Engine Phase 5)
            self.state = "PLAN_AND_BRANCH"
            console.print(f"[bold yellow]State 3: {self.state}[/bold yellow] - Generating candidate fixes...")

            best_candidate = self.decision_engine.evaluate_and_select(task_query, graph_context, past_memories)

            if not best_candidate:
                console.print("[bold red]No safe candidates found. Rejecting task.[/bold red]")
                return {"status": "rejected", "reason": "No safe candidates.", "iterations": iteration}

            console.print(f"[bold green]Selected Candidate:[/bold green] {best_candidate.id} with utility score {best_candidate.score}")

            # State 4: Sandbox Execution (Execution Phase 6)
            self.state = "SANDBOX_EXECUTION"
            console.print(f"[bold yellow]State 4: {self.state}[/bold yellow] - Testing candidates in isolated Docker sandbox...")

            abs_workspace = os.path.abspath(workspace_dir)
            volumes = {abs_workspace: "/app"}

            build_command = best_candidate.commands[0] if len(best_candidate.commands) > 0 else ""
            test_command = "pytest"

            execution_result = run_in_docker(
                image="python:3.11-slim",
                build_command=build_command,
                test_command=test_command,
                volumes=volumes,
                timeout=30
            )

            if execution_result.success:
                console.print(f"[green]✔ {best_candidate.id} passed execution sandbox.[/green]")
            else:
                console.print(f"[red]✘ {best_candidate.id} failed execution sandbox.[/red]")
                console.print(f"[dim]{execution_result.stderr}[/dim]")

            # State 5: Store Memory (Phase 6 feedback)
            self.state = "STORE_MEMORY"
            console.print(f"[bold yellow]State 5: {self.state}[/bold yellow] - Recording experience to Causal Experience Graph (Qdrant)...")

            outcome_status = "success" if execution_result.success else "failure"
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
            console.print(f"[dim]Memory stored: {outcome_status}[/dim]")

            if execution_result.success:
                self.state = "IDLE"
                console.print("[bold blue]Task Complete - Success[/bold blue]")
                return {
                    "status": "success",
                    "selected_candidate": best_candidate.model_dump(),
                    "execution": execution_result.model_dump(),
                    "memories_used": len(past_memories),
                    "iterations": iteration
                }

            console.print("[bold yellow]Execution failed. Repeating loop...[/bold yellow]")

        self.state = "IDLE"
        console.print("[bold red]Task Complete - Failure (Max iterations reached)[/bold red]")
        return {
            "status": "failure",
            "reason": "Max iterations reached without success.",
            "iterations": iteration,
            "memories_used": len(past_memories)
        }
