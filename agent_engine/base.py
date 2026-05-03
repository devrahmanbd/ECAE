from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AgentState(Enum):
    INIT = "INIT"
    PLANNING = "PLANNING"
    FETCHING_MEMORY = "FETCHING_MEMORY"
    FETCHING_GRAPH = "FETCHING_GRAPH"
    BRANCHING = "BRANCHING" # New: ToT branching
    EXEC_BRANCHES = "EXEC_BRANCHES" # New: Parallel execution
    SCORING = "SCORING" # New: Critic scoring
    SELECTION = "SELECTION" # New: Winner choice
    PROMOTING = "PROMOTING"
    SKILL_EXTRACTION = "SKILL_EXTRACTION" # New: Knowledge distillation
    STORING_MEMORY = "STORING_MEMORY"
    COMPLETED = "COMPLETED"

class OperationMode(Enum):
    TASK_EXECUTION = "TASK_EXECUTION"
    SELF_EVOLUTION = "SELF_EVOLUTION" # Renamed from SELF_IMPROVEMENT

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent engine.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: AgentContext) -> AgentContext:
        pass

class BranchContext:
    """Context for a single parallel solution branch."""
    def __init__(self, name: str, plan: str):
        self.name = name
        self.plan = plan
        self.code_changes: List[Dict[str, str]] = []
        self.execution_result: Dict[str, Any] = {}
        self.scores: Dict[str, float] = {
            "test_pass": 0.0,
            "architecture": 0.0,
            "performance": 0.0,
            "minimal_change": 0.0
        }
        self.total_score = 0.0

class AgentContext:
    """
    Shared memory and state for the self-evolutionary engine.
    """
    def __init__(self, task: str):
        self.task = task
        self.state = AgentState.INIT
        self.mode = OperationMode.TASK_EXECUTION
        self.plan: Optional[str] = None
        self.branches: List[BranchContext] = [] # ToT branches
        self.winner: Optional[BranchContext] = None
        
        # History & Artifacts
        self.code_changes: List[Dict[str, str]] = []
        self.execution_results: List[Dict[str, Any]] = []
        self.critique: Optional[str] = None
        self.history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.versioned_artifacts: List[str] = []
        
        # Memory & Cache Control
        self.memory_cache: Dict[str, Any] = {}
        self.memory_calls_count = 0
        self.graph_calls_count = 0
        self.execution_calls_count = 0
        self.duplicate_memory_writes = 0
        self.restart_events = 0
        
        # Optimization Mode
        self.optimization_mode = False
        self.confidence_score = 1.0

    def transition_to(self, new_state: AgentState):
        print(f"[Engine] Transitioning from {self.state.value} to {new_state.value}")
        self.state = new_state
