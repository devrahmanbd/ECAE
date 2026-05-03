from typing import Dict, Any, List
import os
from memory_system.services.graph_service import get_graph_context
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.execution_service import run_in_docker
from rich.console import Console

console = Console()

class AgentOrchestrator:
    def __init__(self):
        self.state = "IDLE"

    def process_task(self, task_query: str, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Executes the predictive engineering loop.
        """
        console.print(f"[bold blue]Starting Task:[/bold blue] {task_query}")

        # State 1: Fetch Graph Context
        self.state = "FETCH_GRAPH_CONTEXT"
        console.print(f"[bold yellow]State 1: {self.state}[/bold yellow] - Fetching dependency graph...")
        graph_context = get_graph_context(task_query)
        console.print(f"[dim]Impacted Dependencies: {len(graph_context.get('impacted_dependencies', []))}[/dim]")

        # State 2: Fetch Memory
        self.state = "FETCH_MEMORY"
        console.print(f"[bold yellow]State 2: {self.state}[/bold yellow] - Checking Qdrant for past experiences...")
        past_memories = search_memory(task_query)
        console.print(f"[dim]Found {len(past_memories)} relevant past memories.[/dim]")

        # State 3: Plan & Branch
        self.state = "PLAN_AND_BRANCH"
        console.print(f"[bold yellow]State 3: {self.state}[/bold yellow] - Generating candidate fixes...")

        # We assume pip install pytest is already in the image or available.
        # But alpine doesn't have python/pytest out of the box, so we'll use a python image.
        candidates = [
            {"id": "branch_1", "command": "pytest", "score": 0.8},
            {"id": "branch_2", "command": "sed -i 's/1 \\/ 0/1.0/g' math_api.py && pytest", "score": 0.9}
        ]

        for idx, c in enumerate(candidates):
            console.print(f"[dim]Candidate {idx+1}: {c['id']} (score: {c['score']}) -> {c['command']}[/dim]")

        # State 4: Sandbox Execution
        self.state = "SANDBOX_EXECUTION"
        console.print(f"[bold yellow]State 4: {self.state}[/bold yellow] - Testing candidates in isolated Docker sandbox...")

        abs_workspace = os.path.abspath(workspace_dir)
        volumes = {abs_workspace: "/app"}

        execution_results = []
        for candidate in candidates:
            console.print(f"[dim]Running {candidate['id']}...[/dim]")
            success, stdout, stderr = run_in_docker(
                image="python:3.11-slim",
                # We need to install pytest in the sandbox if it's not present,
                # so we will bundle it in the command just for this prototype demo.
                # Use a fresh copy of the workspace so sed doesn't persist across branches.
                command=f"cp -r /app /tmp/app && cd /tmp/app && pip install pytest > /dev/null 2>&1 && {candidate['command']}",
                volumes=volumes
            )
            execution_results.append({
                "candidate": candidate,
                "success": success,
                "stdout": stdout,
                "stderr": stderr
            })
            if success:
                console.print(f"[green]✔ {candidate['id']} passed tests.[/green]")
            else:
                console.print(f"[red]✘ {candidate['id']} failed tests.[/red]")

        # State 5: Score & Select
        self.state = "SCORE_AND_SELECT"
        console.print(f"[bold yellow]State 5: {self.state}[/bold yellow] - Scoring and selecting best candidate...")

        selected_candidate = None
        for result in sorted(execution_results, key=lambda x: x["candidate"]["score"], reverse=True):
            if result["success"]:
                selected_candidate = result
                break

        if selected_candidate:
            console.print(f"[bold green]Selected Candidate:[/bold green] {selected_candidate['candidate']['id']} with utility score {selected_candidate['candidate']['score']}")
        else:
            console.print("[bold red]No candidates passed the tests. Change rejected.[/bold red]")

        # State 6: Store Memory
        self.state = "STORE_MEMORY"
        console.print(f"[bold yellow]State 6: {self.state}[/bold yellow] - Recording experience to Causal Experience Graph (Qdrant)...")
        if selected_candidate:
            store_memory(
                text=f"Success for task: {task_query}",
                metadata={
                    "task": task_query,
                    "status": "success",
                    "branch_id": selected_candidate["candidate"]["id"],
                    "score": selected_candidate["candidate"]["score"]
                }
            )
            console.print("[dim]Memory stored: Success[/dim]")
        else:
            store_memory(
                text=f"Failure for task: {task_query}",
                metadata={
                    "task": task_query,
                    "status": "failure",
                    "reason": "All branches failed execution"
                }
            )
            console.print("[dim]Memory stored: Failure[/dim]")

        self.state = "IDLE"
        console.print("[bold blue]Task Complete[/bold blue]")
        return {
            "status": "success" if selected_candidate else "failure",
            "selected_candidate": selected_candidate,
            "graph_context": graph_context,
            "memories_used": len(past_memories)
        }
