import uuid
from memory_system.services.memory_service import store_memory, search_memory
from memory_system.db.qdrant_client import init_collection
from memory_system.models.schemas import MemoryMetadata

def setup_module(module):
    init_collection()

def test_memory_store_and_search():
    unique_text = f"pytest memory store test {uuid.uuid4()}"
    metadata = MemoryMetadata(tags=["test"], decision="run test", memory_type="episodic")
    result = store_memory(unique_text, metadata)
    assert result is not None
    assert result.text == unique_text

    search_results = search_memory(unique_text)
    assert len(search_results) > 0
    assert any(res.text == unique_text for res in search_results)

def test_memory_deduplication():
    unique_text = f"duplicate memory test text {uuid.uuid4()}"

    # Store first time
    res1 = store_memory(unique_text)
    assert res1 is not None

    # Store second time, should be rejected (return None) due to high similarity
    res2 = store_memory(unique_text, similarity_threshold=0.99)
    assert res2 is None

def test_memory_metadata_filtering():
    unique_causal = f"causal memory about failure {uuid.uuid4()}"
    meta1 = MemoryMetadata(memory_type="causal", tags=["bug"])
    store_memory(unique_causal, meta1)

    unique_semantic = f"semantic memory about architecture {uuid.uuid4()}"
    meta2 = MemoryMetadata(memory_type="semantic", tags=["docs"])
    store_memory(unique_semantic, meta2)

    # Search filtering by type
    results_causal = search_memory(unique_causal, memory_type="causal")
    assert all(r.metadata.memory_type == "causal" for r in results_causal if r.metadata)

    # Search filtering by tag
    results_docs = search_memory(unique_semantic, tags=["docs"])
    assert all("docs" in r.metadata.tags for r in results_docs if r.metadata and r.metadata.tags)

def test_memory_relevance_ranking():
    unique_err = f"How to fix an index out of bounds error {uuid.uuid4()}"
    unique_lunch = f"What to have for lunch {uuid.uuid4()}"
    store_memory(unique_err)
    store_memory(unique_lunch)

    # Should rank the code error higher
    results = search_memory("python index error fix")
    assert len(results) >= 2
    assert "index out of bounds" in results[0].text
