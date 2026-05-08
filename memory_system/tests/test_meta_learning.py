import pytest
import os
import tempfile
from memory_system.models.schemas import ExecutionResult, MemoryMetadata
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
    store_memory("Database crash on startup index fix", MemoryMetadata(outcome="failure", confidence=0.5))
    store_memory("Fixing database index performance bug", MemoryMetadata(outcome="success", confidence=0.9))

    # Reranker should boost the success one higher despite identical vector text
    results = search_memory("Database index error fix")

    # We inserted failure first, but success should be ranked 1st
    assert len(results) >= 2

    # The outcome boost should push success up
    assert results[0].metadata.outcome == "success"
    assert results[1].metadata.outcome == "failure"

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
