from agent_engine.base import AgentState, AgentContext, OperationMode
from agent_engine.compliance import ComplianceReport
from typing import Dict, Type
import time

class Orchestrator:
    """
    Coordinates the self-evolutionary engineering loop.
    Enforces parallel branching (ToT) and atomic promotion.
    """
    STATE_FLOW = {
        AgentState.INIT: AgentState.FETCHING_MEMORY,
        AgentState.FETCHING_MEMORY: AgentState.FETCHING_GRAPH,
        AgentState.FETCHING_GRAPH: AgentState.PLANNING,
        AgentState.PLANNING: AgentState.BRANCHING,
        AgentState.BRANCHING: AgentState.EXEC_BRANCHES,
        AgentState.EXEC_BRANCHES: AgentState.SCORING,
        AgentState.SCORING: AgentState.SELECTION,
        AgentState.SELECTION: AgentState.PROMOTING,
        AgentState.PROMOTING: AgentState.SKILL_EXTRACTION,
        AgentState.SKILL_EXTRACTION: AgentState.STORING_MEMORY,
        AgentState.STORING_MEMORY: AgentState.COMPLETED
    }

    def __init__(self, context: AgentContext):
        self.context = context
        self.agents = {}
        self.max_iterations = 30
        self.iteration = 0
        self._detect_mode()

    def _detect_mode(self):
        core_keywords = ["memory_system", "agent_engine", "mcp_server", "core", "orchestrator"]
        if any(kw in self.context.task.lower() for kw in core_keywords):
            print("🧬 MODE DETECTED: SELF_EVOLUTION (Architectural Upgrade)")
            self.context.mode = OperationMode.SELF_EVOLUTION
        else:
            print("🛠️ MODE DETECTED: TASK_EXECUTION (Standard Mission)")
            self.context.mode = OperationMode.TASK_EXECUTION

    def register_agent(self, state: AgentState, agent_class: Type):
        self.agents[state] = agent_class

    def run(self):
        print(f"[Orchestrator] Starting task: {self.context.task}")
        
        while self.context.state != AgentState.COMPLETED and self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n--- Iteration {self.iteration} ---")
            
            # 1. Health Monitor & Optimization Trigger
            if self.context.memory_calls_count > 2:
                print("🚨 WARNING: MEMORY_OVERUSE. Triggering Optimization Mode.")
                self.context.optimization_mode = True
                self.context.confidence_score = 0.5 # Degrade score
            
            if self.context.optimization_mode:
                print("🧠 OPTIMIZATION MODE: Reducing tool calls and reusing cache.")

            # 2. Execute current agent logic
            current_state = self.context.state
            if current_state in self.agents:
                agent = self.agents[current_state]()
                self.context = agent.run(self.context)
            else:
                print(f"[Orchestrator] No agent registered for state {current_state.value}")

            # 3. Compliance & Health Check
            report = ComplianceReport(self.context)
            score = report.run_checks()
            report.print_report()

            # ENFORCEMENT RULE (Memory Spam Protection)
            if self.context.memory_calls_count > 5: # Critical limit
                print("❌ CRITICAL VIOLATION: MEMORY_SPAM. Resetting state.")
                self.context.transition_to(AgentState.INIT)
                self.context.memory_calls_count = 0
                continue

            # 4. Transition logic
            if self.context.state == current_state:
                if current_state in self.STATE_FLOW:
                    self.context.transition_to(self.STATE_FLOW[current_state])
                else:
                    self.context.transition_to(AgentState.COMPLETED)
            
            time.sleep(0.5)

        if self.iteration >= self.max_iterations:
            print("[Orchestrator] Maximum iterations reached.")
        else:
            print("[Orchestrator] Task completed successfully.")
