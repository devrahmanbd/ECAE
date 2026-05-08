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

        # Phase 8 Adaptive Hybrid Ranking Signals
        outcome_bonus = 0.0
        recency_bonus = 0.0
        critique_bonus = 0.0
        context_bonus = 0.0
        failure_penalty = 0.0

        # Safely handle explicit None values
        raw_conf = meta.get("confidence")
        confidence_weight = raw_conf if raw_conf is not None else 0.5

        outcome = meta.get("outcome")
        retries = meta.get("retries", 0)

        if outcome == "success":
            outcome_bonus += 0.25
        elif outcome == "failure":
            outcome_bonus += 0.1

            # Penalize recurrent failures and exhaustion
            if retries and retries >= 3:
                failure_penalty -= 0.15

        # Critique Usefulness (if critique exists and is robust, give it a bump)
        if meta.get("critique_data"):
            critique_bonus += 0.15
        elif meta.get("critique") and len(meta.get("critique")) > 10:
            critique_bonus += 0.1

        # Contextual Matching (if workspace or profiles match, prioritize relevance)
        # Note: In a full scale search we would pass these as query params, but here we boost generally
        # based on completeness of metadata fields.
        if meta.get("execution_profile") or meta.get("workspace"):
            context_bonus += 0.05

        # Recency (newer memories get a small bump)
        mem_time = meta.get("timestamp")
        if mem_time:
            age = time.time() - mem_time
            if age < 86400: # Less than 1 day old
                recency_bonus += 0.1

        # Fast learning: Degrade stale low-confidence inputs
        if confidence_weight < 0.4 and (not mem_time or (time.time() - mem_time) > 86400 * 7):
            failure_penalty -= 0.1

        # Reranked score calculation mapping adaptive learning weights
        final_score = (base_score * 0.4) + outcome_bonus + (confidence_weight * 0.1) + critique_bonus + recency_bonus + context_bonus + failure_penalty

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
    """Phase 8: Assemble a rich evidence packet for the LLM deeply integrating operational traces."""
    logger.info(f"Assembling evidence packet for task: {task}")

    # 1. Gather Graph Neighborhood
    graph_ctx = get_graph_context(task, root_dir=workspace_dir)
    neighborhood = [d.model_dump() for d in (graph_ctx.impacted_dependencies or [])]

    # 2. Gather Semantic Memories (Deeper Fetch)
    all_memories = search_memory(task, limit=15)

    successes = []
    failures = []
    critiques = []
    traces = []

    for mem in all_memories:
        meta = mem.metadata
        if not meta:
            continue

        # Parse Episode Record if available natively (Phase 8 priority)
        if hasattr(meta, "episode_data") and meta.episode_data:
            outcome = meta.episode_data.get("execution_outcome", meta.outcome)
        else:
            outcome = meta.outcome

        if outcome == "success":
            successes.append(mem)
        elif outcome == "failure":
            failures.append(mem)

        if getattr(meta, "critique_data", None) or meta.critique:
            critiques.append(mem)

        if meta.execution_result_summary:
            traces.append({
                "id": mem.id,
                "summary": meta.execution_result_summary,
                "profile": getattr(meta, "execution_profile", "unknown")
            })

    return EvidencePacket(
        task=task,
        graph_neighborhood=neighborhood,
        recent_successes=successes[:5],
        recent_failures=failures[:5],
        critique_records=critiques[:5],
        execution_traces=traces[:5]
    )
