from agent_engine.base import BaseAgent, AgentContext, AgentState, OperationMode

class CriticAgent(BaseAgent):
    """
    Scoring and Winner Selection for parallel branches.
    """
    def __init__(self):
        super().__init__("CriticAgent")

    def run(self, context: AgentContext) -> AgentContext:
        state_val = context.state.value
        
        if state_val == "SCORING":
            print(f"[{self.name}] Scoring {len(context.branches)} candidate branches...")
            for b in context.branches:
                # Score components
                test_score = 1.0 if b.execution_result.get("success") else 0.0
                arch_score = 0.9 if "Architectural" in b.plan else 0.6
                perf_score = 0.8
                min_score = 1.0 if "Minimal" in b.plan else 0.4
                
                # Weighted Total
                b.total_score = (test_score * 0.5) + (arch_score * 0.2) + (perf_score * 0.1) + (min_score * 0.2)
                print(f"  ├── {b.name} Score: {b.total_score:.2f}")

        elif state_val == "SELECTION":
            print(f"[{self.name}] Selecting the best branch...")
            valid_branches = [b for b in context.branches if b.execution_result.get("success")]
            if not valid_branches:
                print(f"[{self.name}] CRITICAL: No branches passed validation!")
                context.transition_to(AgentState.INIT)
                return context
            
            context.winner = max(valid_branches, key=lambda b: b.total_score)
            print(f"[{self.name}] WINNER: {context.winner.name} (Score: {context.winner.total_score:.2f})")
            
        return context
