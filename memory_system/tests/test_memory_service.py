from memory_system.services.memory_service import store_memory, search_memory
from memory_system.db.qdrant_client import init_collection
from memory_system.models.schemas import MemoryMetadata

def setup_module(module):
    init_collection()

def test_memory_store_and_search():
    text = "pytest memory store test"
    metadata = MemoryMetadata(tags=["test"], decision="run test", memory_type="episodic")
    result = store_memory(text, metadata)
    assert result is not None
    assert result.text == text

    search_results = search_memory(text)
    assert len(search_results) > 0
    assert any(res.text == text for res in search_results)

def test_memory_deduplication():
    text = "duplicate memory test text"

    # Store first time
    res1 = store_memory(text)
    assert res1 is not None

    # Store second time, should be rejected (return None)
    res2 = store_memory(text, similarity_threshold=0.99)
    assert res2 is None

def test_memory_metadata_filtering():
    text1 = "causal memory about failure"
    meta1 = MemoryMetadata(memory_type="causal", tags=["bug"])
    store_memory(text1, meta1)

    text2 = "semantic memory about architecture"
    meta2 = MemoryMetadata(memory_type="semantic", tags=["docs"])
    store_memory(text2, meta2)

    # Search filtering by type
    results_causal = search_memory("memory", memory_type="causal")
    assert all(r.metadata.memory_type == "causal" for r in results_causal if r.metadata)

    # Search filtering by tag
    results_docs = search_memory("memory", tags=["docs"])
    assert all("docs" in r.metadata.tags for r in results_docs if r.metadata and r.metadata.tags)

def test_memory_relevance_ranking():
    store_memory("How to fix an index out of bounds error in python array")
    store_memory("What to have for lunch on a tuesday")

    # Should rank the code error higher
    results = search_memory("python index error fix")
    assert len(results) >= 2
    assert "index out of bounds" in results[0].text
