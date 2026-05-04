from memory_system.agent_engine.decision_engine import DecisionEngine
from memory_system.models.schemas import GraphContext, MemoryItem, MemoryMetadata

def test_unsafe_path_rejection():
    engine = DecisionEngine()
    ctx = GraphContext(query="test", blast_radius=0)

    # generate_candidates creates cand_2 with "rm -rf /"
    candidates = engine.generate_candidates("test", ctx, [])
    unsafe_cand = next(c for c in candidates if c.id == "cand_2")

    evaluated = engine.apply_constraints(unsafe_cand, ctx, [])
    assert evaluated.safe is False
    assert evaluated.score == 0.0
    assert "Violated safety rule" in evaluated.rejection_reason

def test_stable_ranking():
    engine = DecisionEngine()
    ctx = GraphContext(query="test", blast_radius=10) # High blast radius

    # In generate_candidates with blast_radius > 0, cand_3 (Cautious refactor, score 0.85) is created.
    # cand_1 (Standard fix, score 0.7) is also created.
    # cand_2 is unsafe.
    # Because blast_radius > 5, cand_1 should be penalized (score 0.7 * 0.5 = 0.35)
    best = engine.evaluate_and_select("test", ctx, [])

    assert best is not None
    assert best.id == "cand_3"
    assert best.score == 0.85

def test_constraint_override():
    engine = DecisionEngine()
    ctx = GraphContext(query="test", blast_radius=0)

    # We create a memory indicating the standard fix fails
    bad_memory = MemoryItem(
        id="123",
        text="Standard fix failed previously.",
        metadata=MemoryMetadata(outcome="failure", decision="Standard bug fix")
    )

    candidates = engine.generate_candidates("test", ctx, [bad_memory])
    cand_1 = next(c for c in candidates if c.id == "cand_1")

    # Apply constraints should override cand_1 score (0.7 -> 0.07)
    evaluated = engine.apply_constraints(cand_1, ctx, [bad_memory])
    assert evaluated.score < 0.1
    assert "Past memory indicates strategy failure" in evaluated.rejection_reason

    # End-to-end selection should now reject cand_1 (due to low score compared to others if others existed,
    # but cand_2 is unsafe, and cand_3 isn't generated if blast radius is 0, so cand_1 is actually the only safe one,
    # but its score is gutted).
    best = engine.evaluate_and_select("test", ctx, [bad_memory])
    assert best.id == "cand_1"
    assert abs(best.score - 0.07) < 0.001
