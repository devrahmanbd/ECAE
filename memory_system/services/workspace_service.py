import os
import json
from typing import Dict, Any
from memory_system.core.event_bus import EventBus, Event, EventType

def detect_workspace(path: str = ".") -> str:
    """
    Automatically resolve the active project root based on common project files.
    Walks up the directory tree looking for markers.
    """
    current_path = os.path.abspath(path)

    # Common markers that indicate a project root
    markers = [".git", "package.json", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml"]

    while current_path != os.path.dirname(current_path): # Stop at root
        for marker in markers:
            if os.path.exists(os.path.join(current_path, marker)):
                EventBus.publish(Event(
                    event_type=EventType.WORKSPACE_CHANGED,
                    payload={"workspace": current_path, "marker": marker}
                ))
                return current_path
        current_path = os.path.dirname(current_path)

    fallback = os.path.abspath(path)
    EventBus.publish(Event(
        event_type=EventType.WORKSPACE_CHANGED,
        payload={"workspace": fallback, "marker": "fallback"}
    ))
    return fallback # Fallback to the provided path if no markers found

def get_execution_profile(path: str) -> str:
    """
    Return basic execution profile based on found files.
    """
    if os.path.exists(os.path.join(path, "requirements.txt")) or os.path.exists(os.path.join(path, "pytest.ini")) or os.path.exists(os.path.join(path, "setup.py")):
        return "python"
    elif os.path.exists(os.path.join(path, "go.mod")):
        return "go"
    elif os.path.exists(os.path.join(path, "package.json")):
        return "js/ts"
    elif os.path.exists(os.path.join(path, "Cargo.toml")):
        return "rust"
    elif any(f.endswith(".sql") for f in os.listdir(path)):
        return "sql/postgres"
    elif os.path.exists(os.path.join(path, "docker-compose.yml")) or os.path.exists(os.path.join(path, "redis.conf")):
        return "redis"
    elif any(f.endswith(".html") for f in os.listdir(path)):
        return "html/web"

    return "unknown"

def init_project(path: str = ".") -> Dict[str, Any]:
    """
    Initialize the workspace by resolving the project and building the graph dynamically in memory.
    No hardcoded graph.json references or file outputs.
    """
    from memory_system.services.graph_service import ProjectGraph

    workspace_root = detect_workspace(path)

    # 1. Determine execution profile
    profile = get_execution_profile(workspace_root)

    # 2. Build initial graph entirely in memory
    graph = ProjectGraph(workspace_root)

    # 3. Return project metadata and graph statistics dynamically
    metadata = {
        "project_root": workspace_root,
        "language_profile": profile,
        "initialized": True,
        "nodes_count": len(graph.nodes),
        "edges_count": len(graph.edges)
    }

    return metadata
