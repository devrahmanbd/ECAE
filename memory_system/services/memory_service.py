from memory_system.core.logger import logger
import uuid
from typing import List, Optional, Dict, Any
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from memory_system.db.qdrant_client import client
from memory_system.core.config import COLLECTION_NAME
from memory_system.core.embeddings import embed
from memory_system.models.schemas import MemoryItem, MemoryMetadata

def store_memory(text: str, metadata: Optional[MemoryMetadata] = None, similarity_threshold: float = 0.95) -> Optional[MemoryItem]:
    """Embed text and store in Qdrant, preventing duplicates."""
    vector = embed(text)

    # Deduplication check
    existing = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=1,
        with_payload=True
    )

    points = getattr(existing, "points", existing)
    if points:
        top_match = points[0]
        score = getattr(top_match, "score", 0.0)
        # If highly similar, do not store duplicate
        if score >= similarity_threshold:
            return None

    # Use dict dump if provided, otherwise empty
    meta_dict = metadata.model_dump(exclude_none=True) if metadata else {}
    payload = {
        "text": text,
        "metadata": meta_dict
    }

    point_id = str(uuid.uuid4())
    logger.info(f"Storing memory point {point_id}")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )]
    )

    return MemoryItem(id=point_id, text=text, metadata=metadata)

def search_memory(
    query: str,
    limit: int = 5,
    memory_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[MemoryItem]:
    """Search for similar memories with ranking and metadata filtering."""
    vector = embed(query)

    must_conditions = []

    if memory_type:
        must_conditions.append(
            FieldCondition(
                key="metadata.memory_type",
                match=MatchValue(value=memory_type)
            )
        )

    if tags:
        must_conditions.append(
            FieldCondition(
                key="metadata.tags",
                match=MatchAny(any=tags)
            )
        )

    query_filter = Filter(must=must_conditions) if must_conditions else None

    logger.info(f"Searching memory with limit {limit}")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        query_filter=query_filter,
        with_payload=True
    )

    memories = []
    points = getattr(results, "points", results)

    # query_points already sorts by score natively, but we can explicitly ensure it
    sorted_points = sorted(points, key=lambda x: getattr(x, "score", 0.0), reverse=True)

    for r in points:
        if not hasattr(r, "payload") or not r.payload:
            continue
        meta = r.payload.get("metadata", {})
        base_score = getattr(r, "score", 0.0)

        # Meta-Learning Reranking Signals
        outcome_bonus = 0.0
        # safely handle explicit None values alongside missing keys
        raw_conf = meta.get("confidence")
        confidence_weight = raw_conf if raw_conf is not None else 0.5

        if meta.get("outcome") == "success":
            outcome_bonus += 0.2

        # Reranked score calculation
        final_score = (base_score * 0.7) + (outcome_bonus * 0.2) + (confidence_weight * 0.1)

        memories.append(MemoryItem(
            id=str(r.id),
            score=final_score,
            text=r.payload.get("text", ""),
            metadata=MemoryMetadata(**meta) if meta else None
        ))

    # Resort by reranked final score
    memories.sort(key=lambda x: x.score, reverse=True)

    return memories[:limit]

def cleanup_memory(min_confidence: float = 0.5):
    """
    Remove low-confidence memories to prevent unbounded growth.
    """
    logger.info(f"Cleaning up memories with confidence < {min_confidence}")
    try:
        # In Qdrant, we use delete with a filter
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.confidence",
                        range={"lt": min_confidence}
                    )
                ]
            )
        )
        logger.info("Memory cleanup successful")
    except Exception as e:
        logger.error(f"Memory cleanup failed: {str(e)}")
