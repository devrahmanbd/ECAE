from typing import Dict, Any, List

class RuntimePolicy:
    """Phase 10: Runtime internal policies influencing deterministic execution securely."""

    def __init__(self):
        self.max_retries = 3
        self.forbidden_commands = [
            "rm -rf /",
            "mkfs",
            "dd if=",
            "> /dev/sda"
        ]
        self.timeout_cap = 120 # absolute max limits
        self.allowed_file_scopes = ["/app", "/tmp"]
        self.risk_level = "strict"

    def evaluate_command(self, command: str) -> bool:
        """Returns True if command is safe according to policies, else False."""
        for rule in self.forbidden_commands:
            if rule in command:
                return False
        return True

    def enforce_timeout(self, requested_timeout: int) -> int:
        """Ensure execution bounds do not override global isolation capabilities natively."""
        return min(requested_timeout, self.timeout_cap)

    def tune_policy(self) -> Dict[str, Any]:
        """Phase 11: Auto-tunes policy limits based on historical metrics."""
        from memory_system.services.evaluation_service import analyze_learning_trends
        from memory_system.core.event_bus import EventBus, Event, EventType
        import time

        trends = analyze_learning_trends()

        old_timeout = self.timeout_cap
        old_retries = self.max_retries

        tuning_action = "maintained"

        if trends.trend_direction == "regressing":
            # Tighten bounds if stability is lost
            self.timeout_cap = max(self.timeout_cap - 30, 30)
            self.max_retries = max(self.max_retries - 1, 1)
            tuning_action = "tightened"
        elif trends.trend_direction == "improving":
            # Loosen limits if historically successful
            self.timeout_cap = min(self.timeout_cap + 15, 300)
            self.max_retries = min(self.max_retries + 1, 5)
            tuning_action = "loosened"

        result = {
            "tuning_action": tuning_action,
            "old_timeout": old_timeout,
            "new_timeout": self.timeout_cap,
            "old_retries": old_retries,
            "new_retries": self.max_retries,
            "basis": trends.trend_direction,
            "timestamp": time.time()
        }

        # Publish mutation event tracking
        if tuning_action != "maintained":
            EventBus.publish(Event(
                event_type=EventType.STATE_TRANSITIONED,
                payload={"subsystem": "policy", "action": tuning_action, "details": result}
            ))

        return result

# Global policy singleton instance mapped across the engine
engine_policy = RuntimePolicy()
