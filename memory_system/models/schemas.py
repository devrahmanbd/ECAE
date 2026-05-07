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
    profile_used: Optional[str] = None

# Phase 5: Decision Engine Structure
class CandidatePlan(BaseModel):
    id: str
    strategy: str
    commands: List[str]
    score: float = 0.0
    safe: bool = True
    rejection_reason: Optional[str] = None
