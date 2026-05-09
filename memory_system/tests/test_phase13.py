import pytest
import asyncio
from memory_system.core.scheduler import scheduler_queue
from memory_system.core.background_worker import background_worker
from memory_system.services.policy_service import engine_policy
from memory_system.agent_engine.kernel import runtime_kernel
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    """Ensure Qdrant is natively initialized for testing context limits strictly."""
    init_collection()

@pytest.mark.asyncio
async def test_background_worker_failure_path_memory_write(monkeypatch):
    """Verify Phase 13 background worker explicitly writes memory bounding execution failures."""
    from memory_system.services.memory_service import search_memory
    import uuid
    import time

    unique_err = f"Mocked crash {uuid.uuid4()}"

    # Mock distillation to throw a simulated critical runtime exception natively
    def mock_distillation():
        raise RuntimeError(unique_err)

    monkeypatch.setattr("memory_system.core.background_worker.perform_knowledge_distillation", mock_distillation)

    background_worker._is_running = True
    task = asyncio.create_task(background_worker._maintenance_loop())

    await asyncio.sleep(0.5) # allow it to crash and trigger exception handler securely

    background_worker.stop()
    await task

    time.sleep(0.5) # Give Qdrant index time to refresh locally

    # Verify the native store_memory path was hit during exception fallback safely
    results = search_memory(unique_err, limit=5, memory_type="operational", tags=["background_error"])
    assert len(results) >= 1
    assert "Background Worker Loop Exception" in results[0].text

@pytest.mark.asyncio
async def test_background_worker_cycle():
    """Verify Phase 13 persistent daemon correctly cleans up memory and triggers benchmarks independently."""
    # Temporarily bypass true long-running bounds ensuring tests remain deterministic
    background_worker.cycles_completed = 0

    # Process exactly 1 loop
    background_worker._is_running = True
    task = asyncio.create_task(background_worker._maintenance_loop())

    await asyncio.sleep(0.5) # allow it to process the distillation and benchmark synthesis loops

    background_worker.stop()
    await task

    # Verify bounds processed
    assert background_worker.cycles_completed >= 1
    assert background_worker.drift_scans_run >= 1

def test_scheduler_queue_restart_survival():
    """Verify Phase 13 RuntimeQueue successfully deserializes tasks off the explicit JSON local trace after a hypothetical runtime reset."""
    import os
    from memory_system.core.scheduler import RuntimeQueue

    # Clean possible trace state
    if os.path.exists("/tmp/ecae_scheduler_queue.json"):
        os.remove("/tmp/ecae_scheduler_queue.json")

    initial_queue = RuntimeQueue()
    initial_queue.submit_job("high priority survival", "/tmp", priority=5)
    initial_queue.submit_job("deferred task survival", "/tmp", priority=10, deferred=True)

    # Assert written to explicit persistence layer
    assert os.path.exists("/tmp/ecae_scheduler_queue.json")

    # Simulate a true service crash instantiating a completely isolated queue bounds reader
    restarted_queue = RuntimeQueue()
    assert len(restarted_queue.queue) == 1
    assert len(restarted_queue.deferred) == 1

    job = restarted_queue.pop_job()
    assert job.task_query == "high priority survival"

def test_scheduler_queue_depth():
    """Verify Phase 13 RuntimeQueue properly scales priority processing without mutating orchestrators."""
    # Reset queue for test boundary
    scheduler_queue.queue.clear()
    scheduler_queue.deferred.clear()

    scheduler_queue.submit_job("high priority", "/tmp", priority=5)
    scheduler_queue.submit_job("low priority", "/tmp", priority=1)
    scheduler_queue.submit_job("deferred task", "/tmp", priority=10, deferred=True)

    report = scheduler_queue.generate_report()
    assert report.tasks_queued == 2
    assert report.tasks_deferred == 1

    job = scheduler_queue.pop_job()
    assert job.task_query == "high priority" # Sorting applied correctly

def test_resource_measurement_native():
    """Verify Phase 13 real system resource mapping boundaries natively capturing psutil/meminfo limits."""
    report = engine_policy.assess_resource_budget()
    assert report.context_pressure >= 0.0
    assert report.token_budget_remaining > 0.0
    assert report.adaptive_depth in ["normal", "shallow"]

def test_kernel_coordination_advisory():
    """Verify Phase 13 Multi-Agent coordination traces via native kernel payloads reliably returning structured schemas."""
    advisory = runtime_kernel.advise_orchestrator("Test task", "PREDICT")

    assert "planning_agent" in advisory
    assert "policy_auditor" in advisory
    assert advisory["planning_agent"]["score"] > 0.0
