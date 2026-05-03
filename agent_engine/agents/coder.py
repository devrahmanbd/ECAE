from agent_engine.base import BaseAgent, AgentContext, OperationMode

class CoderAgent(BaseAgent):
    """
    Executes targeted code changes.
    Supports versioned deployment for SELF_IMPROVEMENT mode.
    """
    def __init__(self):
        super().__init__("CoderAgent")

    def run(self, context: AgentContext) -> AgentContext:
        print(f"[{self.name}] Applying changes (Mode: {context.mode.value})")
        
        target_file = "dummy.py"
        if context.mode == OperationMode.SELF_IMPROVEMENT:
            versioned_file = f"v2_{target_file}"
            print(f"[{self.name}] Core system detected. Creating versioned artifact: {versioned_file}")
            context.versioned_artifacts.append(versioned_file)
            context.code_changes.append({"file": versioned_file, "action": "create_staged"})
        else:
            context.code_changes.append({"file": target_file, "action": "modify"})
            
        return context
