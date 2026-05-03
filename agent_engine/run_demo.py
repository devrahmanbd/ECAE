from agent_engine.base import AgentContext, AgentState
from agent_engine.orchestrator import Orchestrator
from agent_engine.agents.memory_agent import MemoryAgent
from agent_engine.agents.planner import PlannerAgent
from agent_engine.agents.coder import CoderAgent
from agent_engine.agents.executor import ExecutorAgent
from agent_engine.agents.critic import CriticAgent
from agent_engine.agents.deployment_agent import DeploymentAgent

def main():
    # 1. Initialize Context
    task = "Refactor the core agent_engine orchestrator for better stability."
    context = AgentContext(task)
    
    # 2. Setup Orchestrator
    engine = Orchestrator(context)
    
    # 3. Register Agents
    engine.register_agent(AgentState.FETCHING_MEMORY, MemoryAgent)
    engine.register_agent(AgentState.FETCHING_GRAPH, PlannerAgent)
    engine.register_agent(AgentState.PLANNING, PlannerAgent)
    engine.register_agent(AgentState.CODING, CoderAgent)
    engine.register_agent(AgentState.EXECUTING, ExecutorAgent)
    engine.register_agent(AgentState.CRITIC_REVIEW, CriticAgent)
    engine.register_agent(AgentState.PROMOTING, DeploymentAgent)
    engine.register_agent(AgentState.STORING_MEMORY, MemoryAgent)
    
    # 4. Execute Loop
    print("\n🚀 BOOTING MULTI-AGENT ENGINE...")
    engine.run()

if __name__ == "__main__":
    main()
