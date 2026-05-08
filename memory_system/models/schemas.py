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
