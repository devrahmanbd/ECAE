import uuid
from typing import Dict, Any, List, Optional
from memory_system.db.qdrant_client import get_client, COLLECTION_NAME
from memory_system.core.embeddings import get_embedding
from qdrant_client.http.models import PointStruct

def store_memory(text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    client = get_client()
    embedding = get_embedding(text)

    point_id = str(uuid.uuid4())
    payload = {"text": text}
    if metadata:
        payload["metadata"] = metadata

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
        ]
    )
    return point_id

def search_memory(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    client = get_client()
    embedding = get_embedding(query)

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=limit
    )

    results = []
    for hit in search_result.points:
        results.append({
            "id": str(hit.id),
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "metadata": hit.payload.get("metadata", None)
        })

    return results
