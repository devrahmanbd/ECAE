import uuid
from memory_system.db.qdrant_client import client
from memory_system.core.config import COLLECTION_NAME
from memory_system.core.embeddings import embed

def store_memory(text: str, metadata: dict = None):
    """Embed text and store in Qdrant."""
    vector = embed(text)

    payload = {
        "text": text,
        "metadata": metadata or {}
    }

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[{
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": payload
        }]
    )

    return {"status": "stored", "text": text}

def search_memory(query: str, limit: int = 5):
    """Search for similar memories."""
    vector = embed(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit
    )

    return [
        r.payload for r in results.points
    ]
