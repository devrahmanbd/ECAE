from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from memory_system.core.config import COLLECTION_NAME, VECTOR_SIZE

import warnings

_client = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        # For tests/sandbox, fallback to memory if local port isn't available
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _client = QdrantClient(host="localhost", port=6333)
                _client.get_collections()
        except Exception:
            _client = QdrantClient(":memory:")
    return _client

def init_collection():
    """Ensure the collection exists and is configured correctly."""
    client = get_client()
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
