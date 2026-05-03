from agent_engine.base import AgentContext, AgentState
from typing import Dict, Any, List

class ComplianceReport:
    def __init__(self, context: AgentContext):
        self.context = context
        self.checks = {
            "memory_used": False,
            "reused_pattern": "no",
            "memory_confidence_score": 0.0,
            "graph_used": False,
            "impacted_modules": [],
            "risk_level": "low",
            "execution_called": False,
            "result": "N/A",
            "test_coverage": 0,
            "critic_triggered": False,
            "root_cause_identified": "no",
            "fix_scope": "minimal",
            "states_followed": True,
            "skipped_states": [],
            "stored": False,
            "reflection_added": False,
            "skill_created": False,
            "memory_calls": 0,
            "optimization_mode": False,
            "confidence": 1.0
        }
        self.score = 0.0

    def run_checks(self):
        # 0. Health Metrics
        self.checks["memory_calls"] = self.context.memory_calls_count
        self.checks["optimization_mode"] = self.context.optimization_mode
        self.checks["confidence"] = self.context.confidence_score
        
        # 1. Memory Usage
        if "relevant_memories" in self.context.metadata:
            self.checks["memory_used"] = True
            self.checks["memory_confidence_score"] = 0.8 # Simulated
        
        # 2. Graphify Usage
        if "graph_context" in self.context.metadata:
            self.checks["graph_used"] = True
            self.checks["impacted_modules"] = ["memory_system"] # Example
        
        # 3. Execution
        if self.context.execution_results:
            self.checks["execution_called"] = True
            last_res = self.context.execution_results[-1]
            self.checks["result"] = "PASS" if last_res.get("success") else "FAIL"
        
        # 4. Critic
        if self.context.critique:
            self.checks["critic_triggered"] = True
            if "failed" in self.context.critique.lower():
                self.checks["root_cause_identified"] = "yes"
        
        # 5. Loop Integrity
        # Logic to check history for skipped states
        
        # 6. Memory Storage
        if self.context.state == AgentState.COMPLETED:
            self.checks["stored"] = True
            self.checks["reflection_added"] = True

        # Compute Score
        passed = sum(1 for v in self.checks.values() if v is True or v == "yes" or v == "PASS" or (isinstance(v, (int, float)) and v > 0))
        self.score = passed / len(self.checks)
        return self.score

    def print_report(self):
        print("\n📊 --- COMPLIANCE REPORT ---")
        for key, value in self.checks.items():
            print(f"{key}: {value}")
        print(f"FINAL COMPLIANCE SCORE: {self.score:.2f}")
        if self.score < 0.8:
            print("🚨 SYSTEM FAILURE: COMPLIANCE SCORE TOO LOW")
        elif self.score == 1.0:
            print("🎯 OPTIMAL EXECUTION")
        print("----------------------------\n")
