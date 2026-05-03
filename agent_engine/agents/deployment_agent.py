class DeploymentAgent(BaseAgent):
    """
    Handles Atomic Promotion of the winning branch.
    """
    def __init__(self):
        super().__init__("DeploymentAgent")

    def run(self, context: AgentContext) -> AgentContext:
        if context.mode != OperationMode.SELF_EVOLUTION:
            return context

        if not context.winner:
            print(f"[{self.name}] No winner selected. Promotion aborted.")
            return context

        print(f"[{self.name}] ATOMIC PROMOTION: Switching runtime to {context.winner.name}")
        # Logic: ln -sfn winner_path runtime/current
        context.code_changes.append({
            "branch": context.winner.name,
            "action": "atomic_promotion",
            "plan": context.winner.plan
        })
        print(f"[{self.name}] Deployment complete. Runtime is now operational on new version.")
        return context
