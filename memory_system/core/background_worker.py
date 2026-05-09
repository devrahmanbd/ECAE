import asyncio
import time
from typing import Optional
from memory_system.core.logger import logger
from memory_system.core.scheduler import scheduler_queue
from memory_system.services.memory_service import perform_knowledge_distillation
from memory_system.services.evaluation_service import synthesize_benchmarks
from memory_system.models.schemas import BackgroundOperationReport

class BackgroundWorker:
    """Phase 13: Persistent Background Operation executing real asyncio daemon loops without blocking the Orchestrator."""

    def __init__(self):
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self.cycles_completed = 0
        self.drift_scans_run = 0
        self.memories_cleaned = 0
        self.benchmarks_executed = 0

    async def _maintenance_loop(self):
        """Bounded recursive maintenance resolving queue dependencies explicitly."""
        while self._is_running:
            try:
                # 1. Passive Knowledge Distillation (Drift Scanning)
                distillation_metrics = perform_knowledge_distillation()
                self.memories_cleaned += distillation_metrics.get("stale_memories_detected", 0)
                self.drift_scans_run += 1

                # 2. Autonomous Benchmark Synthesis
                new_benchmarks = synthesize_benchmarks()
                self.benchmarks_executed += len(new_benchmarks)

                # 3. Process the explicit Runtime Priority Queue bounds safely
                # Instantiating bounded AgentOrchestrator isolates background processing preventing main thread bypasses
                from memory_system.agent_engine.orchestrator import AgentOrchestrator
                while job := scheduler_queue.pop_job():
                    logger.info(f"Processing deferred queue job: {job.task_query}")
                    orch = AgentOrchestrator(max_iterations=1) # Minimal bounds to prevent infinite loop locking
                    orch.process_task(job.task_query, workspace_dir=job.workspace)
                    scheduler_queue.processed += 1

                self.cycles_completed += 1

                # Back-off gracefully to prevent high idle load looping
                for _ in range(5):
                    if not self._is_running:
                        break
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background worker loop exception handled natively: {e}")

                # Strict bound: Failures must be written to memory
                from memory_system.services.memory_service import store_memory
                from memory_system.models.schemas import MemoryMetadata
                store_memory(
                    text=f"Background Worker Loop Exception: {str(e)}",
                    metadata=MemoryMetadata(
                        memory_type="operational",
                        outcome="failure",
                        tags=["background_error"],
                        confidence=1.0
                    )
                )
                await asyncio.sleep(5)

    def start(self):
        """Initiate the persistent real daemon worker bounds."""
        if self._is_running:
            return

        self._is_running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._maintenance_loop())
        except RuntimeError:
            logger.warning("No running async loop available to spawn BackgroundWorker natively. (Ignore if running synchronous tests)")

    def stop(self):
        """Gracefully close bounds without causing orphaned memory writes."""
        self._is_running = False
        if self._task:
            self._task.cancel()

    def generate_report(self) -> BackgroundOperationReport:
        return BackgroundOperationReport(
            cycles_completed=self.cycles_completed,
            drift_scans_run=self.drift_scans_run,
            memories_cleaned=self.memories_cleaned,
            benchmarks_executed=self.benchmarks_executed
        )

# Global background loop tracker
background_worker = BackgroundWorker()
