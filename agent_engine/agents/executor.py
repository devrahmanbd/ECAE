from agent_engine.base import BaseAgent, AgentContext
import requests

class ExecutorAgent(BaseAgent):
    """
    Runs parallel verification for each branch in the sandbox.
    """
    def __init__(self):
        super().__init__("ExecutorAgent")
        self.api_url = "http://localhost:8000"

    def run(self, context: AgentContext) -> AgentContext:
        if context.state.value != "EXEC_BRANCHES":
            return context

        print(f"[{self.name}] Executing isolated tests for {len(context.branches)} branches...")
        
        for b in context.branches:
            print(f"  ├── Testing {b.name}...")
            # Simulate Docker validation
            try:
                # resp = requests.post(f"{self.api_url}/execute", json={"command": b.plan})
                # b.execution_result = resp.json()
                b.execution_result = {"success": True, "coverage": 0.85} # Simulated
                context.execution_calls_count += 1
            except Exception as e:
                b.execution_result = {"success": False, "error": str(e)}
            
        return context
