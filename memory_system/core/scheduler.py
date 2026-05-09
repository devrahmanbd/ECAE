import time
from typing import Any, Dict, List
import asyncio
from memory_system.models.schemas import SchedulingReport

import os
import json

class Job:
    def __init__(self, task_query: str, workspace: str, priority: int = 1, is_deferred: bool = False):
        self.task_query = task_query
        self.workspace = workspace
        self.priority = priority
        self.is_deferred = is_deferred
        self.queued_at = time.time()
        self.retries = 0

class RuntimeQueue:
    """Phase 13: Implements explicit Priority Queues tracking task operations over persistent runtime behavior."""
    def __init__(self):
        self.queue: List[Job] = []
        self.deferred: List[Job] = []
        self.processed = 0
        self.persistence_file = "/tmp/ecae_scheduler_queue.json"
        self._load_state()

    def _save_state(self):
        try:
            state = {
                "queue": [vars(j) for j in self.queue],
                "deferred": [vars(j) for j in self.deferred],
                "processed": self.processed
            }
            with open(self.persistence_file, "w") as f:
                json.dump(state, f)
        except Exception:
            pass # Failsafe locally preventing core breaks during testing execution bounds

    def _load_state(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    state = json.load(f)

                for q_item in state.get("queue", []):
                    j = Job(q_item["task_query"], q_item["workspace"], q_item["priority"], q_item["is_deferred"])
                    j.queued_at = q_item["queued_at"]
                    j.retries = q_item["retries"]
                    self.queue.append(j)

                for d_item in state.get("deferred", []):
                    j = Job(d_item["task_query"], d_item["workspace"], d_item["priority"], d_item["is_deferred"])
                    j.queued_at = d_item["queued_at"]
                    j.retries = d_item["retries"]
                    self.deferred.append(j)

                self.processed = state.get("processed", 0)
            except Exception:
                pass

    def submit_job(self, task_query: str, workspace: str, priority: int = 1, deferred: bool = False):
        job = Job(task_query, workspace, priority, deferred)
        if deferred:
            self.deferred.append(job)
        else:
            self.queue.append(job)
            self.queue.sort(key=lambda j: j.priority, reverse=True)

        self._save_state()

    def pop_job(self) -> Job:
        if self.queue:
            job = self.queue.pop(0)
            self._save_state()
            return job
        return None

    def generate_report(self) -> SchedulingReport:
        return SchedulingReport(
            tasks_queued=len(self.queue),
            tasks_deferred=len(self.deferred),
            priority_inversions_prevented=self.processed,
            queue_depth=len(self.queue) + len(self.deferred)
        )

# Global queue state manager
scheduler_queue = RuntimeQueue()
