import pytest
from pydantic import ValidationError
from memory_system.models.schemas import MemoryMetadata, MemoryItem, GraphContext, ExecutionResult, GraphDependency

def test_memory_metadata_schema():
    # Valid
    meta = MemoryMetadata(decision="Fix bug", confidence=0.9, extra_field="backward compat test")
    assert meta.decision == "Fix bug"
    assert meta.confidence == 0.9
    assert meta.model_extra["extra_field"] == "backward compat test"

    # Invalid confidence
    with pytest.raises(ValidationError):
        MemoryMetadata(confidence=1.5)

def test_memory_item_schema():
    item = MemoryItem(id="123", text="test text", score=0.85, metadata=MemoryMetadata(decision="test"))
    assert item.id == "123"
    assert item.text == "test text"

    # Invalid (missing required)
    with pytest.raises(ValidationError):
        MemoryItem(id="123")

def test_graph_context_schema():
    ctx = GraphContext(query="test", blast_radius=5)
    assert ctx.query == "test"
    assert ctx.status == "success"

    # Test GraphDependency
    dep = GraphDependency(entity="test_ent", type="module", risk_level="high", path="src/test.py")
    ctx.impacted_dependencies = [dep]
    assert len(ctx.impacted_dependencies) == 1

def test_execution_result_schema():
    res = ExecutionResult(success=True, stdout="output", stderr="", exit_code=0)
    assert res.success is True

    with pytest.raises(ValidationError):
        ExecutionResult(success=True) # missing stdout/stderr
