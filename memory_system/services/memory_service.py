import uuid
from typing import List, Optional
from qdrant_client.http.models import PointStruct
from memory_system.db.qdrant_client import client
from memory_system.core.config import COLLECTION_NAME
from memory_system.core.embeddings import embed
from memory_system.models.schemas import MemoryItem, MemoryMetadata

def store_memory(text: str, metadata: Optional[MemoryMetadata] = None) -> MemoryItem:
    """Embed text and store in Qdrant."""
    vector = embed(text)

    # Use dict dump if provided, otherwise empty
    meta_dict = metadata.model_dump() if metadata else {}
    payload = {
        "text": text,
        "metadata": meta_dict
    }

    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )]
    )

    return MemoryItem(id=point_id, text=text, metadata=metadata)

def search_memory(query: str, limit: int = 5) -> List[MemoryItem]:
    """Search for similar memories."""
    vector = embed(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit
    )

    memories = []
    # query_points returns an object with a .points attribute
    for r in getattr(results, "points", results):
        if not hasattr(r, "payload"):
            continue
        meta = r.payload.get("metadata", {})
        memories.append(MemoryItem(
            id=str(r.id),
            score=getattr(r, "score", None),
            text=r.payload.get("text", ""),
            metadata=MemoryMetadata(**meta) if meta else None
        ))
    return memories
