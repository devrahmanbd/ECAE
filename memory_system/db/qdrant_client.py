from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from memory_system.core.config import COLLECTION_NAME, VECTOR_SIZE, QDRANT_HOST, QDRANT_PORT

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

def init_collection():
    """Ensure the collection exists and is configured correctly."""
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
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")
