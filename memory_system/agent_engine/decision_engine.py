from typing import List, Dict, Any, Optional, Union
from memory_system.models.schemas import CandidatePlan, GraphContext, MemoryItem, EvidencePacket

class DecisionEngine:
    def __init__(self, safety_rules: Optional[List[str]] = None):
        self.safety_rules = safety_rules or ["rm -rf", "mkfs", "dd ", "> /dev/sda"]

    def generate_candidates(self, query: str, context: GraphContext, evidence: Union[List[MemoryItem], EvidencePacket]) -> List[CandidatePlan]:
        """
        Mock generation of multiple candidate solutions.
        In a full system, this would call an LLM.
        Here we generate a mix of safe and unsafe candidates for deterministic testing.
        """
        candidates = []

        # Candidate 1: standard fix
        candidates.append(CandidatePlan(
            id="cand_1",
            strategy="Standard bug fix based on memory patterns.",
            commands=[f"echo 'fixing {query}'"],
            score=0.7
        ))

        # Candidate 2: unsafe command
        candidates.append(CandidatePlan(
            id="cand_2",
            strategy="Aggressive cleanup and rebuild.",
            commands=["rm -rf /", "echo 'done'"],
            score=0.9  # High initial score to test override
        ))

        # Candidate 3: high structural risk adjustment
        # If blast radius is high, we might propose a more cautious strategy
        if context.blast_radius > 0:
            candidates.append(CandidatePlan(
                id="cand_3",
                strategy="Cautious refactor using deprecation.",
                commands=["echo 'deprecating old logic'"],
                score=0.85
            ))

        return candidates

    def apply_constraints(self, candidate: CandidatePlan, context: GraphContext, evidence: Union[List[MemoryItem], EvidencePacket]) -> CandidatePlan:
        """
        Apply hard constraints and adjust scores.
        """
        # 1. Safety Rules (Hard Constraint)
        for cmd in candidate.commands:
            for rule in self.safety_rules:
                if rule in cmd:
                    candidate.safe = False
                    candidate.score = 0.0
                    candidate.rejection_reason = f"Violated safety rule: contains '{rule}'"
                    return candidate

        # 2. Graph Risk Constraint (Score Adjustment)
        if context.blast_radius > 5:
            # Penalize candidates that don't have "cautious" or "deprecation" strategies if risk is high
            if "cautious" not in candidate.strategy.lower() and "deprecat" not in candidate.strategy.lower():
                candidate.score *= 0.5
                candidate.rejection_reason = "High graph risk without cautious strategy"

        # 3. Memory Insights Constraint
        mem_list = evidence.recent_failures + evidence.recent_successes if isinstance(evidence, EvidencePacket) else evidence
        for mem in mem_list:
            # If a past memory explicitly marks this strategy as a failure, penalize it
            if mem.metadata and mem.metadata.outcome == "failure":
                if mem.metadata.decision and mem.metadata.decision in candidate.strategy:
                    candidate.score *= 0.1
                    candidate.rejection_reason = "Past memory indicates strategy failure"

        return candidate

    def evaluate_and_select(self, query: str, context: GraphContext, evidence: Union[List[MemoryItem], EvidencePacket]) -> Optional[CandidatePlan]:
        """
        Main decision loop: generate -> score -> constrain -> select.
        """
        raw_candidates = self.generate_candidates(query, context, evidence)

        evaluated = []
        for cand in raw_candidates:
            evaluated.append(self.apply_constraints(cand, context, evidence))

        # Filter safe
        safe_candidates = [c for c in evaluated if c.safe]

        if not safe_candidates:
            return None

        # Select best score
        best_candidate = max(safe_candidates, key=lambda c: c.score)
        return best_candidate
