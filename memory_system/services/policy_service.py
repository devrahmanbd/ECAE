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

# Global policy singleton instance mapped across the engine
engine_policy = RuntimePolicy()
