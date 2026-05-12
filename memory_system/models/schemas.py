from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

# Phase 2 & 3: Metadata Structure
class MemoryMetadata(BaseModel):
    memory_type: Optional[str] = None # working, episodic, semantic, skill, causal, operational
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

    namespace: str = Field(default="production")
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
    is_operational: Optional[bool] = False

    # Phase 10: Strategic Planning
    goals: Optional[List[str]] = None
    subgoals: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    milestones_completed: Optional[List[str]] = None
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

    # Phase 11 Skill Lifecycle Governance
    lifecycle_state: str = "candidate" # candidate, verified, promoted, degraded, retired, contradicted
    promotion_count: int = 0
    degradation_count: int = 0
    contradiction_count: int = 0
    last_success_at: Optional[float] = None
    last_failure_at: Optional[float] = None
    cross_workspace_success_rate: float = 0.0
    governance_notes: List[str] = []

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

    # Phase 11 Requirements
    regression_summary: Dict[str, Any] = {}
    benchmark_summary: Dict[str, Any] = {}
    evaluation_summary: Dict[str, Any] = {}
    recovery_summary: Dict[str, Any] = {}
    policy_summary: Dict[str, Any] = {}
    stability_score: float = 1.0


class EvaluationReport(BaseModel):
    retrieval_precision: float = 0.0
    rerank_improvement: float = 0.0
    skill_reuse_quality: float = 0.0
    recovery_success_rate: float = 0.0
    critique_usefulness: float = 0.0
    retry_exhaustion_rate: float = 0.0
    drift_frequency: float = 0.0
    policy_success_rate: float = 0.0
    benchmark_pass_rate: float = 0.0
    plan_success_rate: float = 0.0
    evidence_packet_quality: float = 0.0
    failure_recurrence_rate: float = 0.0
    execution_reliability: float = 0.0
    time_to_recovery: float = 0.0
    stale_memory_ratio: float = 0.0

class HistoricalTrendSummary(BaseModel):
    trend_direction: str = "stable"
    confidence: float = 1.0
    supporting_metrics: Dict[str, Any] = {}
    regression_indicators: List[str] = []
    anomaly_flags: List[str] = []

class RegressionAlert(BaseModel):
    metric_name: str
    previous_value: float
    current_value: float
    severity: str
    timestamp: float

class DriftAuditReport(BaseModel):
    total_stale_memories: int = 0
    total_contradictions: int = 0
    drift_score: float = 0.0

class DriftClusterSummary(BaseModel):
    cluster_id: str
    affected_entities: List[str] = []
    drift_reason: str

class KnowledgeDecaySummary(BaseModel):
    decayed_items: int = 0
    reclaimed_confidence: float = 0.0

# Phase 12 Additions
class ArchitectureFreezeReport(BaseModel):
    is_frozen: bool = True
    structural_mutations_detected: List[str] = []
    control_flow_bypasses: List[str] = []

class CompatibilityGuardReport(BaseModel):
    status: str = "PASS"
    unsupported_mutations: List[str] = []
    shims_used: List[str] = []

class ReleaseCandidateReport(BaseModel):
    candidate_id: str
    status: str = "PENDING"
    workspaces_tested: List[str] = []
    failed_checks: List[str] = []

class CanaryRunReport(BaseModel):
    run_id: str
    startup_success_rate: float = 0.0
    loop_completion_rate: float = 0.0
    recovery_success_rate: float = 0.0
    failure_recurrence_rate: float = 0.0
    drift_rate: float = 0.0

class RollbackReport(BaseModel):
    release_candidate_id: str
    trigger_reason: str
    failing_stage: str
    affected_files: List[str] = []
    execution_result: Optional[ExecutionResult] = None
    drift_summary: Dict[str, Any] = {}
    rollback_action_taken: str = "REVERTED_TO_LAST_STABLE"
    outcome: str = "SUCCESS"

class ProductionDriftReport(BaseModel):
    drift_trend: str = "stable"
    dependency_drift: float = 0.0
    workspace_drift: float = 0.0
    retrieval_drift: float = 0.0
    policy_drift: float = 0.0
    outdated_skills_flagged: int = 0

class StabilityDashboardPayload(BaseModel):
    release_candidate_trends: Dict[str, Any] = {}
    canary_health: Dict[str, Any] = {}
    rollback_frequency: float = 0.0
    drift_frequency: float = 0.0
    execution_recovery_trend: str = "stable"
    skill_reuse_trend: str = "stable"
    release_readiness_score: float = 1.0
    architecture_freeze_status: str = "FROZEN"

class VersionFreezeReport(BaseModel):
    version: str
    is_frozen: bool = True
    mcp_entrypoint_stable: bool = True
    graphify_stable: bool = True
    launcher_stable: bool = True

class OperationalReleaseAudit(BaseModel):
    audit_id: str
    timestamp: float
    release_candidate_checks: Dict[str, Any] = {}
    canary_outcomes: Dict[str, Any] = {}
    rollback_events: List[Dict[str, Any]] = []
    freeze_status: str = "VERIFIED"
    compatibility_guard_outcomes: str = "PASS"

# Phase 13 Additions
class BackgroundOperationReport(BaseModel):
    cycles_completed: int = 0
    drift_scans_run: int = 0
    memories_cleaned: int = 0
    benchmarks_executed: int = 0

class SchedulingReport(BaseModel):
    tasks_queued: int = 0
    tasks_deferred: int = 0
    priority_inversions_prevented: int = 0
    queue_depth: int = 0

class ResourceBudgetReport(BaseModel):
    token_budget_remaining: float = 1.0
    context_pressure: float = 0.0
    memory_saturation: float = 0.0
    adaptive_depth: str = "normal"

class ModelRoutingReport(BaseModel):
    selected_model: str = "default_planner"
    routing_reason: str = "standard_complexity"
    fallback_invoked: bool = False

class ForecastReport(BaseModel):
    plan_outcome_estimate: float = 0.0
    failure_probability: float = 0.0
    rollback_cost_estimate: str = "low"
    drift_risk: str = "low"
    policy_risk: str = "low"

class MemoryFederationReport(BaseModel):
    local_memory_size: int = 0
    global_memory_size: int = 0
    cold_memory_size: int = 0
    cache_hits: int = 0

class TelemetryReport(BaseModel):
    orchestration_latency_avg: float = 0.0
    retrieval_latency_avg: float = 0.0
    recovery_latency_avg: float = 0.0
    policy_hit_rate: float = 1.0
    drift_acceleration: float = 0.0

class CognitiveKernelReport(BaseModel):
    coordination_health: str = "stable"
    active_agents: List[str] = []
    kernel_uptime: float = 0.0
