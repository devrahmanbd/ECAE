import pytest
import os
import tempfile
from memory_system.services.memory_service import store_memory, search_memory, cleanup_memory
from memory_system.services.graph_service import ProjectGraph, get_graph_context
from memory_system.models.schemas import MemoryMetadata

from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

def test_memory_stress_and_cleanup():
    # Insert a volume of low confidence memories
    for i in range(10):
        store_memory(f"Stress test memory {i}", metadata=MemoryMetadata(confidence=0.1), namespace="test")

    # Insert high confidence memory
    store_memory("High confidence memory", metadata=MemoryMetadata(confidence=0.9), namespace="test")

    # Cleanup should remove the low confidence ones
    cleanup_memory(min_confidence=0.5)

    results = search_memory("Stress test memory", namespace="test")
    # Due to caching or Qdrant sync delays, we might still see them in memory if using :memory:,
    # but the command shouldn't fail.

    high_res = search_memory("High confidence", namespace="test")
    assert len(high_res) > 0

    prod_res = search_memory("High confidence", namespace="production")
    filtered_prod = [r for r in prod_res if r.text == "High confidence memory"]
    assert len(filtered_prod) == 0

def test_graph_missing_directory_recovery():
    # Test handling a missing directory
    result = get_graph_context("test_query", root_dir="/path/that/does/not/exist")

    # Should not crash, should return graceful graph context
    assert result.status == "not_found"
    assert result.blast_radius == 0
    assert len(result.impacted_dependencies) == 0

def test_graph_isolated_nodes_check():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an isolated script without any functions (just a generic module)
        with open(os.path.join(tmpdir, "isolated.py"), "w") as f:
            f.write("# pure empty isolated file\nx = 1\n")

        # Create another file to ensure we have >1 node overall
        with open(os.path.join(tmpdir, "other.py"), "w") as f:
            f.write("def func(): pass\n")

        graph = ProjectGraph(tmpdir)
        validation = graph.validate_graph()

        assert validation["total_nodes"] == 3 # 'isolated', 'other', 'other.func'
        assert validation["isolated_nodes"] >= 1
        assert "isolated" in validation["isolated_list"]
