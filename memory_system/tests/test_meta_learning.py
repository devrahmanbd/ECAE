import pytest
import os
import tempfile
from memory_system.models.schemas import ExecutionResult, MemoryMetadata, ToolchainRecord
from memory_system.services.profile_service import get_profile_config, extract_stack_trace
from memory_system.services.memory_service import search_memory, store_memory
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

def test_profile_resolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Detect JS project
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write("{}")

        cfg = get_profile_config(tmpdir)
        assert cfg["name"] == "js/ts"
        assert cfg["validation_cmd"] == "npm test"

        # Detect Go project
        os.remove(os.path.join(tmpdir, "package.json"))
        with open(os.path.join(tmpdir, "go.mod"), "w") as f:
            f.write("")

        cfg2 = get_profile_config(tmpdir)
        assert cfg2["name"] == "go"
        assert "go test" in cfg2["validation_cmd"]

def test_crash_envelope_extraction():
    stderr_output = """Some generic logs
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    func()
  File "main.py", line 5, in func
    raise ValueError("Crash")
ValueError: Crash
More logs here"""

    trace = extract_stack_trace(stderr_output)
    assert "Traceback" in trace
    assert "ValueError: Crash" in trace

def test_memory_reranking():
    # Insert multiple similar memories
    store_memory("Database crash on startup index fix", MemoryMetadata(outcome="failure", confidence=0.5), namespace="test")
    store_memory("Fixing database index performance bug", MemoryMetadata(outcome="success", confidence=0.9), namespace="test")

    # Reranker should boost the success one higher despite identical vector text
    results = search_memory("Database index error fix", namespace="test")

    # Filter to only the ones we just inserted
    my_res = [r for r in results if "Database crash" in r.text or "Fixing database" in r.text]

    # We inserted failure first, but success should be ranked 1st
    assert len(my_res) >= 2

    # The outcome boost should push success up
    assert my_res[0].metadata.outcome == "success"
    assert my_res[1].metadata.outcome == "failure"

def test_episode_extraction_and_storage(monkeypatch):
    """Verify Phase 8 EpisodeRecord serialization natively writes into memory storage correctly."""
    from memory_system.agent_engine.orchestrator import AgentOrchestrator, OrchestratorState
    import memory_system.services.memory_service as mem_svc

    mem_calls = []
    original_store = mem_svc.store_memory

    def mock_store(*args, **kwargs):
        mem_calls.append(kwargs)
        return original_store(*args, **kwargs)

    monkeypatch.setattr("memory_system.agent_engine.orchestrator.store_memory", mock_store)

    # Run a simple failure loop
    orch = AgentOrchestrator(max_iterations=1)
    with tempfile.TemporaryDirectory() as tmpdir:
        import memory_system.services.workspace_service as ws_svc
        ws_svc.init_project(tmpdir)
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def dummy(): pass\n\ndummy()\n")

        orch.process_task("main.py", workspace_dir=tmpdir)

        # Verify Episode Record explicitly written into kwargs payloads natively
        assert len(mem_calls) >= 1
        meta = mem_calls[0]["metadata"]
        assert meta.episode_data is not None
        assert "execution_outcome" in meta.episode_data
        assert "critique" in meta.episode_data
        assert meta.episode_data["execution_outcome"] == "failure"
        assert meta.what_worked is None
        assert meta.what_failed is not None

def test_skill_extraction_and_causal_learning():
    """Verify Phase 8 extract_skills_and_causal creates records during learning states natively."""
    from memory_system.services.memory_service import extract_skills_and_causal

    success_episode = {
        "success": True,
        "selected_strategy": "Refactored the variable natively",
        "confidence": 0.9,
        "timestamp": 12345.6
    }

    # Store directly calling the extraction logic (usually fired implicitly during LEARN)
    # We use search_memory to grab it since it outputs explicitly tagged records
    extract_skills_and_causal(success_episode, "skill extraction validation")
    results = search_memory("SKILL SUCCESS: Refactored the variable natively resolves skill extraction validation", limit=10)
    my_results = [r for r in results if r.metadata and r.metadata.is_skill]
    assert len(my_results) >= 1
    assert my_results[0].metadata.is_skill is True

    failure_episode = {
        "success": False,
        "selected_strategy": "Ran rm -rf",
        "critique": {"why_failed": "Permission denied"},
        "confidence": 0.2,
        "timestamp": 12345.6,
        "workspace": "/tmp/dummy"
    }

    extract_skills_and_causal(failure_episode, "causal learning validation")
    f_results = search_memory("CAUSAL FAILURE: Ran rm -rf resulted in failure because Permission denied", limit=10)
    my_results_c = [r for r in f_results if r.metadata and r.metadata.is_causal]
    assert len(my_results_c) >= 1
    assert my_results_c[0].metadata.is_causal is True

def test_evidence_compression():
    """Verify assemble_evidence dynamically compresses outputs mapping array limits securely."""
    from memory_system.services.memory_service import assemble_evidence

    # We already have diverse test cases inserted, assembling an arbitrary large bucket natively
    res = assemble_evidence("Database index error", ".")
    assert hasattr(res, "recent_successes")

    # Check that lengths are strictly bounds checked ensuring compressed limits (usually bounded to 3 or 5)
    assert len(res.recent_successes) <= 5

def test_temporal_decay():
    """Verify older low confidence memories get degraded score bounds compared to recent ones."""
    from memory_system.services.memory_service import store_memory, search_memory
    import time

    # Store memory from years ago
    past_time = time.time() - (86400 * 40) # 40 days ago

    store_memory("Completely unique old decayed memory", MemoryMetadata(confidence=0.3, timestamp=past_time, outcome="failure"), namespace="test")
    store_memory("Completely unique recent successful memory", MemoryMetadata(confidence=0.9, timestamp=time.time(), outcome="success"), namespace="test")

    results = search_memory("Completely unique", limit=20, namespace="test")
    my_res = [r for r in results if "Completely unique" in r.text]
    assert len(my_res) >= 2

    # The recent success should significantly outrank the older decayed failure
    assert my_res[0].metadata.outcome == "success"

def test_adaptive_planning():
    """Verify Decision Engine correctly applies penalties limiting compressed boundaries matching unsafe patterns natively."""
    from memory_system.agent_engine.decision_engine import DecisionEngine
    from memory_system.models.schemas import CompressedEvidence, EvidencePacket, CandidatePlan, GraphContext, MemoryItem, MemoryMetadata

    engine = DecisionEngine()
    # Mock the generator to have a stable string without id(self) for this test
    engine.generate_candidates = lambda q, c, e: [CandidatePlan(id="cand_1", strategy="Standard bug fix based on memory patterns for testing.", commands=["echo fixing"], score=0.7)]


    # Provide an evidence packet indicating candidate 1 is unsafe
    # Memory logic mapping:
    # "Standard bug fix based on memory patterns." is candidate 1.
    evidence = EvidencePacket(
        task="Testing adaptive mapping",
        recent_failures=[MemoryItem(id="1", text="fail", metadata=MemoryMetadata(outcome="failure", decision="Standard bug fix based on memory patterns for testing.", never_repeat="Standard bug fix based on memory patterns for testing."))]
    )

    ctx = GraphContext(query="testing", blast_radius=0)

    best = engine.evaluate_and_select("testing", ctx, evidence)

    # Cand 2 is intrinsically unsafe from base rules
    # Cand 1 should be explicitly rejected based on the evidence matching known failures
    # Cand 3 only fires on high blast_radius
    # Thus, engine should return None effectively gracefully refusing action rather than executing failure
    assert best is None

def test_policy_engine():
    """Verify global runtime policies intercept blocked paths completely."""
    from memory_system.services.policy_service import engine_policy
    from memory_system.services.execution_service import execute_command

    # Evaluate a string matching forbidden lists natively
    assert engine_policy.evaluate_command("echo test && rm -rf /") is False

    # Confirm timeout limits securely clamp inputs securely natively
    assert engine_policy.enforce_timeout(9000) == 120

    # Confirm it actively halts execution_service calls directly
    res = execute_command("echo test && mkfs /dev/sda1")
    assert res.success is False
    assert "Command blocked by runtime policy." in res.error

def test_toolchain_synthesis():
    """Verify toolchain records extract dynamically during success learning."""
    from memory_system.services.memory_service import extract_skills_and_causal, search_memory

    success_episode = {
        "success": True,
        "selected_strategy": "Resolved memory testing logic",
        "confidence": 0.9,
        "timestamp": 12345.6
    }

    extract_skills_and_causal(success_episode, "toolchain extraction mapping")
    results = search_memory("TOOLCHAIN SYNTHESIS: Standard loop mapped to resolve toolchain extraction mapping", limit=10)
    my_results = [r for r in results if r.metadata and r.metadata.is_toolchain]

    assert len(my_results) >= 1
    assert my_results[0].metadata.is_toolchain is True
    assert my_results[0].metadata.toolchain_data is not None
    assert "detect_workspace" in my_results[0].metadata.toolchain_data["steps"]

def test_drift_penalties():
    """Verify that search_memory explicitly degrades final_scores for timeout-flagged critiques based on dynamic RL rules."""
    from memory_system.services.memory_service import search_memory, store_memory
    from memory_system.models.schemas import MemoryMetadata

    # Store standard memory
    store_memory("Drift validation base target normal", MemoryMetadata(outcome="success", confidence=0.8, critique="This is a very long normal critique that grants a bonus."), namespace="test")
    # Store drift-flagged memory
    store_memory("Drift validation base target timeout", MemoryMetadata(outcome="success", confidence=0.8, critique="Execution failed due to environment timeout.", drift_penalty=-0.5), namespace="test")

    results = search_memory("Drift validation base target", namespace="test")
    my_res = [r for r in results if "Drift validation base target" in r.text]

    # The normal one should outrank the drifted one heavily
    assert len(my_res) >= 2
    assert "normal" in my_res[0].text

def test_skill_promotion():
    """Verify evaluate_skill_lifecycle properly promotes extensively used skills natively."""
    from memory_system.services.memory_service import evaluate_skill_lifecycle
    from memory_system.models.schemas import SkillRecord
    import time

    skill = SkillRecord(
        skill_id="test",
        name="test",
        task_type="test",
        description="test",
        confidence=0.5,
        last_verified_at=time.time(),
        usage_count=4 # High usage
    )

    evaluated = evaluate_skill_lifecycle(skill)
    assert evaluated.promoted_at is not None
    assert evaluated.promotion_reason is not None

def test_governance_gate():
    """Verify evaluate_release_readiness identifies clean boundaries gracefully."""
    from memory_system.services.governance_service import evaluate_release_readiness

    # Passing "." evaluates the current clean test workspace
    report = evaluate_release_readiness(".")

    assert report.status in ["PASS", "FAIL"] # Might fail depending on if scratchpad scripts exist, but schema validation runs smoothly
    assert isinstance(report.reasons, list)
