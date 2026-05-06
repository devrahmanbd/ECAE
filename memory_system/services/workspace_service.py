import os
import json
from typing import Dict, Any

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
                return current_path
        current_path = os.path.dirname(current_path)

    return os.path.abspath(path) # Fallback to the provided path if no markers found

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
    Initialize the workspace by writing metadata and building the graph.
    """
    from memory_system.services.graph_service import ProjectGraph

    workspace_root = detect_workspace(path)

    # 1. Determine execution profile
    profile = get_execution_profile(workspace_root)

    # 2. Build graphify output directory
    graphify_out = os.path.join(workspace_root, "graphify-out")
    os.makedirs(graphify_out, exist_ok=True)

    # 3. Write project metadata
    metadata = {
        "project_root": workspace_root,
        "language_profile": profile,
        "initialized": True
    }

    metadata_path = os.path.join(graphify_out, "project.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    # 4. Build initial graph
    graph = ProjectGraph(workspace_root)
    # The graph is built automatically in the constructor (__init__ calls build_graph())

    # For now, we serialize the basic structure to show it was built
    graph_data = {
        "nodes_count": len(graph.nodes),
        "edges_count": len(graph.edges),
        "status": "built"
    }

    graph_json_path = os.path.join(graphify_out, "graph.json")
    with open(graph_json_path, "w") as f:
        json.dump(graph_data, f, indent=4)

    return metadata
