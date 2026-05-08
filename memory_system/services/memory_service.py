from memory_system.core.logger import logger
import uuid
from typing import List, Optional, Dict, Any
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from memory_system.db.qdrant_client import client
from memory_system.core.config import COLLECTION_NAME
from memory_system.core.embeddings import embed
from memory_system.models.schemas import MemoryItem, MemoryMetadata, EvidencePacket, SkillRecord, CausalRecord, ToolchainRecord
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

        # Fast learning & Phase 8/9 Temporal Decay and RL Rewards
        drift_score = meta.get("drift_penalty", 0.0)
        decay_score = 0.0

        if mem_time:
            age_days = (time.time() - mem_time) / 86400

            # Penalize completely stale entries (>30 days) heavily
            if age_days > 30:
                decay_score -= 0.3
            # Low confidence memories decay faster
            if confidence_weight < 0.4 and age_days > 7:
                decay_score -= 0.2

            # Phase 9: Active Drift detection
            if meta.get("critique") and "timeout" in meta.get("critique", "").lower():
                drift_score -= 0.1

        # Phase 9 RL Scoring
        reward_score = meta.get("reward_score", 0.0)
        penalty_score = meta.get("penalty_score", 0.0)

        if meta.get("critique") and len(meta.get("critique")) > 20:
            reward_score += 0.1 # Useful critique reward

        if meta.get("is_skill"):
            reward_score += 0.2 # Skill reuse reward

        if retries and retries >= 3:
            penalty_score -= 0.2 # Exhaustion penalty

        workspace_match = 0.0
        if meta.get("workspace"):
            workspace_match = 0.05

        # Reranked score calculation mapping adaptive learning weights
        final_score = (base_score * 0.4) + outcome_bonus + (confidence_weight * 0.1) + critique_bonus + recency_bonus + context_bonus + failure_penalty + decay_score + drift_score + reward_score + penalty_score + workspace_match

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

    from memory_system.models.schemas import CompressedEvidence

    # Phase 8: Compress Evidence
    known_good = []
    known_fails = []
    unsafe = []

    for s in successes:
        if s.metadata and s.metadata.what_worked and s.metadata.what_worked not in known_good:
            known_good.append(s.metadata.what_worked)

    for f in failures:
        if f.metadata:
            if f.metadata.what_failed and f.metadata.what_failed not in known_fails:
                known_fails.append(f.metadata.what_failed)
            if f.metadata.never_repeat and f.metadata.never_repeat not in unsafe:
                unsafe.append(f.metadata.never_repeat)

    compressed = CompressedEvidence(
        known_good_patterns=known_good[:5],
        known_failure_patterns=known_fails[:5],
        high_confidence_paths=known_good[:2],
        unsafe_paths=unsafe[:5],
        unresolved_questions=[],
        summary_confidence=0.8 if known_good else 0.4,
        source_bundle_ids=[m.id for m in successes + failures]
    )

    return EvidencePacket(
        task=task,
        graph_neighborhood=neighborhood,
        recent_successes=successes[:3], # Distilled context bounds
        recent_failures=failures[:3],
        critique_records=critiques[:3],
        execution_traces=traces[:3]
    )


def evaluate_skill_lifecycle(skill: SkillRecord) -> SkillRecord:
    """Phase 9: Promote or retire skills based on usage counts and drift."""
    import time

    # Promotion check
    if skill.usage_count >= 3 and not skill.promoted_at:
        skill.promoted_at = time.time()
        skill.promotion_reason = "Repeated successful execution validations."
        skill.confidence = min(skill.confidence + 0.1, 1.0)

    # Demotion/Retirement check based on a mock drift rule (simulating a contradicted rule threshold)
    # If confidence drops massively or it hasn't been verified in 60 days
    if skill.last_verified_at and (time.time() - skill.last_verified_at) > (86400 * 60):
        if not skill.retired_at:
            skill.retired_at = time.time()
            skill.retirement_reason = "Stale skill; unverified for over 60 days."
            skill.confidence = max(skill.confidence - 0.5, 0.0)

    return skill

def extract_skills_and_causal(episode_data: Dict[str, Any], task: str) -> None:
    """Phase 8: Extract reusable skills and causal records from successfully completed episodes."""
    if not episode_data.get("success"):
        # Extract Causal Failure Path
        causal = CausalRecord(
            action=episode_data.get("selected_strategy", "unknown"),
            outcome="failure",
            condition=episode_data.get("workspace", "unknown"),
            likely_cause=episode_data.get("critique", {}).get("why_failed", "unknown"),
            confidence=episode_data.get("confidence", 0.5),
            first_seen=episode_data.get("timestamp", time.time()),
            last_seen=episode_data.get("timestamp", time.time()),
            source_episodes=[task]
        )

        # Store causal as semantic causal memory
        store_memory(
            text=f"CAUSAL FAILURE: {causal.action} resulted in {causal.outcome} because {causal.likely_cause}",
            metadata=MemoryMetadata(
                memory_type="causal",
                is_causal=True,
                causal_data=causal.model_dump(),
                tags=["causal", "failure_pattern"],
                timestamp=causal.last_seen
            )
        )
    else:
        strategy_desc = episode_data.get("selected_strategy", "unknown")

        # Check if skill exists
        existing_skills = search_memory(f"SKILL SUCCESS: {strategy_desc}", limit=5)
        existing_skill_item = next((r for r in existing_skills if r.metadata and r.metadata.is_skill and r.metadata.skill_data and r.metadata.skill_data.get("description") == strategy_desc), None)

        if existing_skill_item and existing_skill_item.metadata and existing_skill_item.metadata.skill_data:
            skill = SkillRecord(**existing_skill_item.metadata.skill_data)
            skill.usage_count += 1
            skill.last_verified_at = episode_data.get("timestamp", time.time())
            if task not in skill.source_episodes:
                skill.source_episodes.append(task)
        else:
            # Extract Successful Skill natively
            skill = SkillRecord(
                skill_id=str(uuid.uuid4()),
                name=f"Skill extracted from {task}",
                task_type="resolved_task",
                description=strategy_desc,
                confidence=episode_data.get("confidence", 0.5),
                last_verified_at=episode_data.get("timestamp", time.time()),
                usage_count=1,
                source_episodes=[task]
            )

        # Phase 9: Evaluate skill constraints securely
        skill = evaluate_skill_lifecycle(skill)

        # Store skill as semantic skill memory
        store_memory(
            text=f"SKILL SUCCESS: {skill.description} resolves {task}",
            metadata=MemoryMetadata(
                memory_type="semantic",
                is_skill=True,
                skill_data=skill.model_dump(),
                tags=["skill", "success_pattern"],
                timestamp=skill.last_verified_at,
                created_at=time.time(),
                last_used_at=time.time()
            )
        )

        # Phase 8: Extract Autonomous Toolchain Synthesis
        # Standard workflow sequence mapped into a reusable synthesis chain
        toolchain = ToolchainRecord(
            chain_id=str(uuid.uuid4()),
            task_type="resolved_task_toolchain",
            steps=["detect_workspace", "get_graph_context", "search_memory", "assemble_evidence", "execute_command"],
            success_rate=1.0,
            failure_patterns=[],
            prerequisites=[task],
            linked_skills=[skill.skill_id],
            linked_episodes=[task],
            verification_status="verified_success"
        )

        # Store toolchain as semantic toolchain memory
        store_memory(
            text=f"TOOLCHAIN SYNTHESIS: Standard loop mapped to resolve {task}",
            metadata=MemoryMetadata(
                memory_type="semantic",
                is_toolchain=True,
                toolchain_data=toolchain.model_dump(),
                tags=["toolchain", "success_pattern"],
                timestamp=time.time(),
                created_at=time.time(),
                last_used_at=time.time()
            )
        )
