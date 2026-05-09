import time
from typing import Dict, Any, List
from memory_system.models.schemas import TelemetryReport
from memory_system.core.event_bus import EventBus, Event, EventType

class TelemetryService:
    """Phase 13: Implements a production-grade observability and telemetry bounds tracer dynamically capturing latency and trends natively."""
    def __init__(self):
        self.orchestration_latencies: List[float] = []
        self.retrieval_latencies: List[float] = []
        self.recovery_latencies: List[float] = []
        self.policy_hits = 0
        self.policy_misses = 0
        self.drift_events = 0
        self.benchmarks_synthesized = 0

        # Subscribe to Event Bus to trace behavior strictly off the main orchestrator path asynchronously
        EventBus.subscribe(EventType.RETRIEVAL_QUALITY_DROPPED, self.record_drift)
        EventBus.subscribe(EventType.POLICY_FAILED, self.record_policy_miss)
        EventBus.subscribe(EventType.BENCHMARK_REGRESSED, self.record_benchmark)

    async def record_drift(self, event: Event):
        self.drift_events += 1

    async def record_policy_miss(self, event: Event):
        self.policy_misses += 1

    async def record_benchmark(self, event: Event):
        self.benchmarks_synthesized += 1

    def record_orchestration_latency(self, latency: float):
        self.orchestration_latencies.append(latency)

    def record_retrieval_latency(self, latency: float):
        self.retrieval_latencies.append(latency)

    def record_recovery_latency(self, latency: float):
        self.recovery_latencies.append(latency)

    def generate_telemetry_report(self) -> TelemetryReport:
        o_lat = sum(self.orchestration_latencies) / len(self.orchestration_latencies) if self.orchestration_latencies else 0.0
        rt_lat = sum(self.retrieval_latencies) / len(self.retrieval_latencies) if self.retrieval_latencies else 0.0
        rc_lat = sum(self.recovery_latencies) / len(self.recovery_latencies) if self.recovery_latencies else 0.0

        hit_rate = 1.0
        total_policies = self.policy_hits + self.policy_misses
        if total_policies > 0:
            hit_rate = self.policy_hits / total_policies

        return TelemetryReport(
            orchestration_latency_avg=o_lat,
            retrieval_latency_avg=rt_lat,
            recovery_latency_avg=rc_lat,
            policy_hit_rate=hit_rate,
            drift_acceleration=float(self.drift_events)
        )

# Global telemetry instance tracing the full event span
telemetry = TelemetryService()
