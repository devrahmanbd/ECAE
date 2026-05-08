from typing import Dict, Any, List
import time
import uuid
from memory_system.models.schemas import MemoryMetadata, MemoryItem
from memory_system.services.memory_service import search_memory, store_memory

def run_learning_evaluation() -> Dict[str, Any]:
    """Phase 9: Pull recent episodes to calculate learning evaluation metrics."""

    # We pull generic episode records via high limit searches assuming text match "Outcome for task" or similar
    # In a full vector DB we'd filter directly on `hasattr(metadata, "episode_data")` natively using scroll.
    raw_results = search_memory("Outcome for task", limit=50)

    episodes = []
    for r in raw_results:
        if r.metadata and r.metadata.episode_data:
            episodes.append(r.metadata.episode_data)

    total = len(episodes)
    if total == 0:
        return {"status": "no_data"}

    success_count = sum(1 for e in episodes if e.get("execution_outcome") == "success")
    exhaustion_count = sum(1 for e in episodes if e.get("execution_outcome") == "failure" and e.get("retries_attempted", 0) > 0)

    success_rate = success_count / total
    exhaustion_rate = exhaustion_count / total

    metrics = {
        "status": "evaluated",
        "total_episodes": total,
        "success_rate": success_rate,
        "retry_exhaustion_rate": exhaustion_rate,
        "timestamp": time.time()
    }

    # Persist the evaluation metric snapshot into memory for historical charting
    store_memory(
        text=f"ECAE Learning Evaluation: SR={success_rate:.2f} ER={exhaustion_rate:.2f}",
        metadata=MemoryMetadata(
            memory_type="semantic",
            outcome="success" if success_rate > 0.5 else "failure",
            tags=["evaluation_metrics"],
            confidence=success_rate,
            timestamp=time.time()
        )
    )

    return metrics
