from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "memory"

def init_qdrant():
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def init_collection():
    try:
        init_qdrant()
    except Exception as e:
        print(f"Failed to initialize Qdrant collection: {e}")

# Initialize on import
try:
    init_qdrant()
except Exception as e:
    print(f"Failed to initialize Qdrant (might not be running): {e}")

def get_client() -> QdrantClient:
    return client
