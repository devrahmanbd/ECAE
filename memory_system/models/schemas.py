from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

# Phase 2 & 3: Metadata Structure
class MemoryMetadata(BaseModel):
    memory_type: Optional[str] = None # episodic, semantic, causal
    decision: Optional[str] = None
    reasoning: Optional[str] = None
    outcome: Optional[str] = None
    tags: Optional[List[str]] = None
    affected_files: Optional[List[str]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Phase 6 Meta-Learning Fields
    task: Optional[str] = None
    graph_context_summary: Optional[str] = None
    memory_context_summary: Optional[str] = None
    execution_result_summary: Optional[str] = None
    critique: Optional[str] = None
    semantic_labels: Optional[List[str]] = None
    relation_labels: Optional[List[str]] = None

    # Phase 7 Positive/Negative Learning Fields
    what_worked: Optional[str] = None
    what_failed: Optional[str] = None
    why_failed: Optional[str] = None
    never_repeat: Optional[str] = None
    promising_paths: Optional[str] = None
    timestamp: Optional[float] = None

    # Phase 8 Enhanced Episode Fields
    episode_data: Optional[Dict[str, Any]] = None
    critique_data: Optional[Dict[str, Any]] = None
    workspace: Optional[str] = None
    execution_profile: Optional[str] = None
    retries: Optional[int] = 0

    # Phase 8 Skill & Causal Learning
    linked_skills: Optional[List[str]] = None
    linked_causal_records: Optional[List[str]] = None
    is_skill: Optional[bool] = False
    is_causal: Optional[bool] = False
    is_toolchain: Optional[bool] = False
    skill_data: Optional[Dict[str, Any]] = None
    causal_data: Optional[Dict[str, Any]] = None
    toolchain_data: Optional[Dict[str, Any]] = None

    # Phase 8 Temporal Decay Fields
    created_at: Optional[float] = None
    last_used_at: Optional[float] = None
    decay_score: Optional[float] = 0.0
    freshness_score: Optional[float] = 1.0
    drift_score: Optional[float] = 0.0

    # Phase 9 Reward/Drift/Governance Fields
    reward_score: Optional[float] = 0.0
    penalty_score: Optional[float] = 0.0
    outcome_quality: Optional[str] = None
    recurrence_penalty: Optional[float] = 0.0
    critique_reward: Optional[float] = 0.0
    skill_reuse_reward: Optional[float] = 0.0
    drift_penalty: Optional[float] = 0.0
    freshness_reward: Optional[float] = 0.0
    workspace_match_reward: Optional[float] = 0.0
    drift_reason: Optional[str] = None
    drift_source: Optional[str] = None
    last_verified_at: Optional[float] = None
    last_seen_at: Optional[float] = None
    confidence_after_drift: Optional[float] = None
    invalidation_reason: Optional[str] = None

    # Allow extra fields for backward compatibility / flexibility
    model_config = {"extra": "allow"}

class MemoryItem(BaseModel):
    id: str
    text: str
    score: Optional[float] = None
    metadata: Optional[MemoryMetadata] = None

class StoreRequest(BaseModel):
    text: str
    metadata: Optional[MemoryMetadata] = None

class SearchResponse(BaseModel):
    text: str
    metadata: MemoryMetadata

# Phase 2: Graph Context Structure
class GraphDependency(BaseModel):
    entity: str
    type: str
    risk_level: str
    path: str

class GraphContext(BaseModel):
    query: str
    impacted_dependencies: Optional[List[GraphDependency]] = []
    blast_radius: Optional[int] = 0
    status: str = "success"
    context: Optional[str] = None
    graph_loaded: bool = True

# Phase 2: Execution Result Structure
class ExecuteRequest(BaseModel):
    command: str
    image: Optional[str] = None
    workdir: Optional[str] = "."

class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: Optional[int] = None
    error: Optional[str] = None

    # Phase 6 Crash & Envelope Fields
    profile_used: Optional[str] = None
    stack_trace: Optional[str] = None
    failing_stage: Optional[str] = None

# Phase 5: Decision Engine Structure
class CandidatePlan(BaseModel):
    id: str
    strategy: str
    commands: List[str]
    score: float = 0.0
    safe: bool = True
    rejection_reason: Optional[str] = None


# Phase 7: RAG + MCP Evidence Packet
class EvidencePacket(BaseModel):
    task: str
    graph_neighborhood: List[Dict[str, Any]] = []
    recent_successes: List[MemoryItem] = []
    recent_failures: List[MemoryItem] = []
    critique_records: List[MemoryItem] = []
    execution_traces: List[Dict[str, Any]] = []

# Phase 8: RAG Episode and Critique Records
class CritiqueRecord(BaseModel):
    what_worked: Optional[str] = None
    what_failed: Optional[str] = None
    why_failed: Optional[str] = None
    retry_recommendation: Optional[str] = None
    confidence_explanation: Optional[str] = None
    dangerous_paths: Optional[str] = None
    promising_partial_paths: Optional[str] = None
    execution_anomalies: Optional[str] = None
    graph_blind_spots: Optional[str] = None
    memory_blind_spots: Optional[str] = None

class EpisodeRecord(BaseModel):
    task: str
    workspace: str
    selected_strategy: str
    graph_neighborhood_used: List[Dict[str, Any]] = []
    evidence_packet_summary: Optional[str] = None
    memories_retrieved: List[str] = []
    tools_used: List[str] = []
    execution_profile: str
    execution_outcome: str
    retries_attempted: int
    crash_envelope: Optional[Dict[str, Any]] = None
    critique: CritiqueRecord
    confidence: float
    success: bool
    semantic_tags: List[str] = []
    relation_tags: List[str] = []
    affected_files: List[str] = []
    timestamp: float


class SkillRecord(BaseModel):
    skill_id: str
    name: str
    task_type: str
    description: str
    steps: List[str] = []
    prerequisites: List[str] = []
    success_conditions: List[str] = []
    failure_patterns: List[str] = []
    confidence: float
    source_episodes: List[str] = []
    related_graph_nodes: List[str] = []
    related_memory_records: List[str] = []
    last_verified_at: float
    usage_count: int = 0

    # Phase 9 Skill Lifecycle
    promoted_at: Optional[float] = None
    retired_at: Optional[float] = None
    promotion_reason: Optional[str] = None
    retirement_reason: Optional[str] = None

class CausalRecord(BaseModel):
    action: str
    outcome: str
    condition: str
    likely_cause: str
    confidence: float
    recurrence_count: int = 0
    first_seen: float
    last_seen: float
    source_episodes: List[str] = []
    linked_skills: List[str] = []
    linked_memory_items: List[str] = []

class ToolchainRecord(BaseModel):
    chain_id: str
    task_type: str
    steps: List[str] = []
    success_rate: float = 0.0
    failure_patterns: List[str] = []
    prerequisites: List[str] = []
    linked_skills: List[str] = []
    linked_episodes: List[str] = []
    verification_status: str

class CompressedEvidence(BaseModel):
    known_good_patterns: List[str] = []
    known_failure_patterns: List[str] = []
    high_confidence_paths: List[str] = []
    unsafe_paths: List[str] = []
    unresolved_questions: List[str] = []
    summary_confidence: float = 0.0
    source_bundle_ids: List[str] = []


class ReleaseGateReport(BaseModel):
    status: str # "PASS" or "FAIL"
    reasons: List[str] = []
    failed_checks: List[str] = []
    metrics_summary: Dict[str, Any] = {}
    drift_summary: Dict[str, Any] = {}
    skill_summary: Dict[str, Any] = {}
    stability_summary: Dict[str, Any] = {}
