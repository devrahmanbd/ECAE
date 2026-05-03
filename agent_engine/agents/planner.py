from agent_engine.base import BaseAgent, AgentContext, BranchContext
import requests

class PlannerAgent(BaseAgent):
    """
    Creates candidate branches (Tree-of-Thought).
    """
    def __init__(self):
        super().__init__("PlannerAgent")
        self.api_url = "http://localhost:8000"

    def run(self, context: AgentContext) -> AgentContext:
        state_val = context.state.value
        
        if state_val == "FETCHING_GRAPH":
            print(f"[{self.name}] Analyzing dependencies via Graphify...")
            try:
                resp = requests.get(f"{self.api_url}/graph/context", params={"query": context.task})
                context.metadata["graph_context"] = resp.json()
            except Exception as e:
                print(f"[{self.name}] Error fetching graph: {e}")
        
        elif state_val == "PLANNING":
            print(f"[{self.name}] Designing base architecture...")
            context.plan = f"Strategic direction for: {context.task}"
        
        elif state_val == "BRANCHING":
            print(f"[{self.name}] Tree-of-Thought: Generating 3 candidate branches...")
            context.branches = [
                BranchContext("Branch A", "Minimal patch (Direct fix)"),
                BranchContext("Branch B", "Architectural refactor (Robust fix)"),
                BranchContext("Branch C", "Alternative design (Scalable fix)")
            ]
            for b in context.branches:
                print(f"  ├── {b.name}: {b.plan}")
            
        return context
