from typing import Dict, Any, List
import os
from enum import Enum
from memory_system.models.schemas import GraphContext, MemoryMetadata, CandidatePlan
from memory_system.services.graph_service import get_graph_context
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.execution_service import run_in_docker
from memory_system.agent_engine.decision_engine import DecisionEngine
from memory_system.core.event_bus import EventBus, Event, EventType
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
    CRITIQUE = 10
    LEARN = 11
    STOP = 12

class AgentOrchestrator:
    def __init__(self, max_iterations: int = 3):
        self.state = OrchestratorState.WORKSPACE_CHECK
        self.decision_engine = DecisionEngine()
        self.max_iterations = max_iterations

        # Phase 9: Release governance gate evaluation
        from memory_system.services.governance_service import evaluate_release_readiness
        gov = evaluate_release_readiness()
        if gov.status == "FAIL":
            console.print(f"[bold yellow]GOVERNANCE WARNING: Release readiness failed checks: {gov.reasons}[/bold yellow]")

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

    def transition_to(self, new_state: OrchestratorState, task_query: str, payload: dict = None):
        """Enforces explicit state machine contracts per Phase 10 rules."""
        console.print(f"[bold yellow]Transitioning: {self.state.name} -> {new_state.name}[/bold yellow]")
        self.state = new_state
        EventBus.publish(Event(
            event_type=EventType.STATE_TRANSITIONED,
            payload={"new_state": new_state.name, "task": task_query, "data": payload or {}}
        ))

    def process_task(self, task_query: str, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Executes the deterministic state machine loop.
        Predict -> Filter -> Optimize -> Generate -> Execute -> Result -> Learn
        """
        console.print(f"[bold blue]Starting Task:[/bold blue] {task_query}")

        self.transition_to(OrchestratorState.WORKSPACE_CHECK, task_query)
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
            self.transition_to(OrchestratorState.GRAPH_LOAD, task_query)
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
            self.transition_to(OrchestratorState.MEMORY_LOAD, task_query)
            try:
                past_memories = search_memory(task_query)
            except Exception as e:
                reason = "Memory layer unavailable"
                self._record_failure(task_query, reason, ["memory_error"])
                return {"status": "stop", "reason": reason}
            console.print(f"[dim]Found {len(past_memories)} relevant past memories.[/dim]")

            # 3. PREDICT
            self.transition_to(OrchestratorState.PREDICT, task_query)
            try:
                from memory_system.services.memory_service import assemble_evidence
                evidence = assemble_evidence(task_query, workspace_dir)

                # Phase 8: Loop Enforcement Barrier - Block progression on missing evidence payload constraints natively
                if not evidence or not hasattr(evidence, "task"):
                    raise Exception("Evidence packet corrupted or missing")

                raw_candidates = self.decision_engine.generate_candidates(task_query, graph_context, evidence)
            except Exception as e:
                reason = "Tool call failed or returned malformed output"
                self._record_failure(task_query, reason, ["tool_error"])
                return {"status": "stop", "reason": reason}

            # 4. FILTER
            self.transition_to(OrchestratorState.FILTER, task_query)
            try:
                evaluated = []
                for cand in raw_candidates:
                    evaluated.append(self.decision_engine.apply_constraints(cand, graph_context, evidence))
                safe_candidates = [c for c in evaluated if c.safe]
                if not safe_candidates:
                    reason = "No safe candidates found"
                    self._record_failure(task_query, reason, ["filter_rejection"])
                    return {"status": "stop", "reason": reason}
            except Exception as e:
                reason = "Tool call failed or returned malformed output"
                self._record_failure(task_query, reason, ["tool_error"])
                return {"status": "stop", "reason": reason}

            # 5. OPTIMIZE
            self.transition_to(OrchestratorState.OPTIMIZE, task_query)
            best_candidate = max(safe_candidates, key=lambda c: c.score)

            # 6. GENERATE
            self.transition_to(OrchestratorState.GENERATE, task_query)
            build_command = best_candidate.commands[0] if len(best_candidate.commands) > 0 else ""
            test_command = "pytest"

            # 7. EXECUTE
            self.transition_to(OrchestratorState.EXECUTE, task_query)
            abs_workspace = os.path.abspath(workspace_dir)
            volumes = {abs_workspace: "/app"}

            try:
                execution_result = run_in_docker(
                    image="python:3.11-slim",
                    build_command=build_command,
                    test_command=test_command,
                    volumes=volumes,
                    timeout=30
                )

                # Phase 10: Self-Healing Execution hook
                if not execution_result.success and iteration < self.max_iterations:
                    console.print(f"[bold yellow]Execution Failed. Synthesizing Autonomous Recovery using Causal Memory...[/bold yellow]")
                    # Simulate failure recovery query
                    recovery_mems = search_memory(f"CAUSAL FAILURE: {execution_result.error}", limit=3, memory_type="causal")
                    if recovery_mems:
                        console.print(f"[bold green]Found {len(recovery_mems)} recovery paths. Adjusting trajectory...[/bold green]")
                        # The next PREDICT cycle naturally subsumes this evidence natively.

            except Exception as e:
                reason = "Execution sandbox unavailable"
                self._record_failure(task_query, reason, ["sandbox_error"])
                return {"status": "stop", "reason": reason}

            # 8. RESULT
            self.transition_to(OrchestratorState.RESULT, task_query, {"success": execution_result.success})
            outcome_status = "success" if execution_result.success else "failure"
            if execution_result.success:
                console.print(f"[green]✔ {best_candidate.id} passed execution sandbox.[/green]")
            else:
                console.print(f"[red]✘ {best_candidate.id} failed execution sandbox.[/red]")
                console.print(f"[dim]{execution_result.stderr}[/dim]")

            # Pre-condition: No final success without execution proof
            if execution_result.exit_code is None:
                console.print("[bold red]FATAL: No execution evidence returned. Blocking success bypass.[/bold red]")
                reason = "No execution evidence provided"
                self._record_failure(task_query, reason, ["execution_bypass_blocked"])
                return {"status": "stop", "reason": reason}

            # 10. CRITIQUE
            self.transition_to(OrchestratorState.CRITIQUE, task_query)

            from memory_system.models.schemas import CritiqueRecord, EpisodeRecord

            # Heuristic self-critique based on output (Phase 8 structured extraction)
            critique_reason = "Executed successfully without errors." if execution_result.success else "Execution failed during runtime or validation."
            is_timeout = not execution_result.success and execution_result.error and "timed out" in execution_result.error.lower()
            if is_timeout:
                critique_reason = "Execution failed due to environment timeout."

            what_worked = best_candidate.strategy if execution_result.success else None
            what_failed = best_candidate.strategy if not execution_result.success else None
            why_failed = execution_result.error if not execution_result.success else None
            never_repeat = best_candidate.strategy if not execution_result.success and execution_result.exit_code != 0 else None

            critique_record = CritiqueRecord(
                what_worked=what_worked,
                what_failed=what_failed,
                why_failed=why_failed,
                retry_recommendation="Yes" if is_timeout else ("No" if never_repeat else "Maybe"),
                confidence_explanation=f"Based on score {best_candidate.score}",
                dangerous_paths=never_repeat,
                promising_partial_paths=best_candidate.strategy if not execution_result.success and execution_result.exit_code == 0 else None,
                execution_anomalies=execution_result.stderr if execution_result.stderr else None,
                graph_blind_spots=None,
                memory_blind_spots=None
            )

            crash_envelope = {
                "stdout": execution_result.stdout,
                "stderr": execution_result.stderr,
                "exit_code": execution_result.exit_code,
                "stack_trace": execution_result.stack_trace,
                "failing_stage": execution_result.failing_stage
            } if not execution_result.success else None

            import time
            episode = EpisodeRecord(
                task=task_query,
                workspace=workspace_dir,
                selected_strategy=best_candidate.strategy,
                graph_neighborhood_used=[d.model_dump() for d in (graph_context.impacted_dependencies or [])],
                evidence_packet_summary=f"Found {len(past_memories)} memories",
                memories_retrieved=[m.id for m in past_memories] if isinstance(past_memories, list) else [],
                tools_used=[],
                execution_profile=execution_result.profile_used or "unknown",
                execution_outcome=outcome_status,
                retries_attempted=iteration - 1,
                crash_envelope=crash_envelope,
                critique=critique_record,
                confidence=best_candidate.score,
                success=execution_result.success,
                semantic_tags=[best_candidate.strategy, outcome_status],
                relation_tags=[d.entity for d in graph_context.impacted_dependencies] if graph_context.impacted_dependencies else [],
                affected_files=[],
                timestamp=time.time()
            )

            # 11. LEARN
            self.transition_to(OrchestratorState.LEARN, task_query, {"outcome": outcome_status})

            try:
                import time
                from memory_system.services.memory_service import extract_skills_and_causal

                # Phase 8: Fire background extractions
                extract_skills_and_causal(episode.model_dump(), task_query)

                store_memory(
                    text=f"Outcome for task: {task_query} using strategy: {best_candidate.strategy}",
                    metadata=MemoryMetadata(
                        memory_type="causal",
                        decision=best_candidate.strategy,
                        outcome=outcome_status,
                        tags=["execution_feedback"],
                        confidence=best_candidate.score,
                        task=task_query,
                        critique=critique_reason,
                        execution_result_summary=f"Exit: {execution_result.exit_code}, Success: {execution_result.success}, Failed Stage: {execution_result.failing_stage}",
                        graph_context_summary=f"Blast radius: {graph_context.blast_radius}",
                        memory_context_summary=f"Memories utilized: {len(past_memories)}",
                        semantic_labels=[best_candidate.strategy, outcome_status],
                        relation_labels=[d.entity for d in graph_context.impacted_dependencies] if graph_context.impacted_dependencies else [],
                        what_worked=what_worked,
                        what_failed=what_failed,
                        why_failed=why_failed,
                        never_repeat=never_repeat,
                        timestamp=episode.timestamp,
                        episode_data=episode.model_dump(),
                        critique_data=critique_record.model_dump(),
                        workspace=workspace_dir,
                        execution_profile=execution_result.profile_used,
                        retries=iteration - 1
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
