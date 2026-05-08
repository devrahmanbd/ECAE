from memory_system.core.logger import logger
import uuid
from typing import List, Optional, Dict, Any
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from memory_system.db.qdrant_client import client
from memory_system.core.config import COLLECTION_NAME
from memory_system.core.embeddings import embed
from memory_system.models.schemas import MemoryItem, MemoryMetadata, EvidencePacket
from memory_system.services.graph_service import get_graph_context
import time

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
    if metadata and metadata.timestamp is None:
        metadata.timestamp = time.time()

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

        # Phase 7 Hybrid Ranking Signals
        outcome_bonus = 0.0
        recency_bonus = 0.0
        critique_bonus = 0.0

        # Safely handle explicit None values
        raw_conf = meta.get("confidence")
        confidence_weight = raw_conf if raw_conf is not None else 0.5

        outcome = meta.get("outcome")
        if outcome == "success":
            outcome_bonus += 0.2
        elif outcome == "failure":
            # Failures are valuable to learn from, but slightly less heavily weighted than straight successes
            outcome_bonus += 0.1

        # Critique Usefulness (if critique exists and is robust, give it a bump)
        if meta.get("critique") and len(meta.get("critique")) > 10:
            critique_bonus += 0.1

        # Recency (newer memories get a small bump)
        mem_time = meta.get("timestamp")
        if mem_time:
            age = time.time() - mem_time
            if age < 86400: # Less than 1 day old
                recency_bonus += 0.1

        # Reranked score calculation: Similarity (50%), Outcome (20%), Confidence (10%), Critique (10%), Recency (10%)
        final_score = (base_score * 0.5) + outcome_bonus + (confidence_weight * 0.1) + critique_bonus + recency_bonus

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


def assemble_evidence(task: str, workspace_dir: str = ".") -> EvidencePacket:
    """Phase 7: Assemble a rich evidence packet for the LLM."""
    logger.info(f"Assembling evidence packet for task: {task}")

    # 1. Gather Graph Neighborhood
    graph_ctx = get_graph_context(task, root_dir=workspace_dir)
    neighborhood = [d.model_dump() for d in (graph_ctx.impacted_dependencies or [])]

    # 2. Gather Semantic Memories
    all_memories = search_memory(task, limit=10)

    successes = []
    failures = []
    critiques = []
    traces = []

    for mem in all_memories:
        meta = mem.metadata
        if not meta:
            continue

        outcome = meta.outcome
        if outcome == "success":
            successes.append(mem)
        elif outcome == "failure":
            failures.append(mem)

        if meta.critique:
            critiques.append(mem)

        if meta.execution_result_summary:
            traces.append({"id": mem.id, "summary": meta.execution_result_summary})

    return EvidencePacket(
        task=task,
        graph_neighborhood=neighborhood,
        recent_successes=successes[:3],
        recent_failures=failures[:3],
        critique_records=critiques[:3],
        execution_traces=traces[:3]
    )
