import asyncio
import time
from enum import Enum
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field

class EventType(str, Enum):
    WORKSPACE_CHANGED = "workspace_changed"
    GRAPH_INVALIDATED = "graph_invalidated"
    SKILL_PROMOTED = "skill_promoted"
    POLICY_FAILED = "policy_failed"
    EXECUTION_CRASHED = "execution_crashed"
    BENCHMARK_REGRESSED = "benchmark_regressed"
    RETRIEVAL_QUALITY_DROPPED = "retrieval_quality_dropped"
    MEMORY_CONTRADICTED = "memory_contradicted"
    STATE_TRANSITIONED = "state_transitioned"

class Event(BaseModel):
    event_type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class EventBus:
    """An asynchronous event bus that handles system-wide events decoupled from execution constraints."""

    _subscribers: Dict[EventType, List[Callable[[Event], Any]]] = {}

    @classmethod
    def subscribe(cls, event_type: EventType, handler: Callable[[Event], Any]):
        """Subscribe an asynchronous or synchronous handler to an event."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)

    @classmethod
    def publish(cls, event: Event):
        """Publish an event to all subscribers natively via asyncio tasks to ensure asynchronous execution."""
        from memory_system.core.logger import logger
        logger.info(f"Published Event: {event.event_type.value} | Payload: {list(event.payload.keys())}")

        handlers = cls._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                # If running an event loop, fire natively as background tasks
                if asyncio.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(event))
                    except RuntimeError:
                        # Fallback for sync execution contexts (like pytest sync runs)
                        asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler failed processing {event.event_type}: {str(e)}")
