from memory_system.services.memory_service import store_memory, search_memory
from memory_system.db.qdrant_client import init_collection
from memory_system.models.schemas import MemoryMetadata

def setup_module(module):
    init_collection()

def test_memory_store_and_search():
    text = "pytest memory store test"
    metadata = MemoryMetadata(tags=["test"], decision="run test")
    result = store_memory(text, metadata)
    assert result.text == text

    search_results = search_memory(text)
    assert len(search_results) > 0
    assert any(res.text == text for res in search_results)
