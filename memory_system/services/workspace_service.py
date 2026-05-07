import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ExecutionProfile(BaseModel):
    language: str
    validation_command: str
    execution_command: str

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

def get_execution_profile(path: str) -> ExecutionProfile:
    """
    Return execution profile based on found files.
    """
    if os.path.exists(os.path.join(path, "requirements.txt")) or os.path.exists(os.path.join(path, "pytest.ini")) or os.path.exists(os.path.join(path, "setup.py")):
        return ExecutionProfile(language="python", validation_command="pytest", execution_command="python main.py")
    elif os.path.exists(os.path.join(path, "go.mod")):
        return ExecutionProfile(language="go", validation_command="go test ./...", execution_command="go build ./...")
    elif os.path.exists(os.path.join(path, "package.json")):
        return ExecutionProfile(language="js/ts", validation_command="npm test", execution_command="npm run build")

    elif any(f.endswith(".sql") for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))):
        return ExecutionProfile(language="sql/postgres", validation_command="migration validation command", execution_command="deterministic SQL validation workflow")
    elif os.path.exists(os.path.join(path, "redis.conf")):
        return ExecutionProfile(language="redis", validation_command="redis health check", execution_command="integration verification workflow")
    elif os.path.exists(os.path.join(path, "docker-compose.yml")):
        with open(os.path.join(path, "docker-compose.yml"), "r") as f:
            if "redis" in f.read().lower():
                return ExecutionProfile(language="redis", validation_command="redis health check", execution_command="integration verification workflow")
            else:
                return ExecutionProfile(language="unknown", validation_command="", execution_command="")
    elif any(f.endswith(".html") for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))):
        return ExecutionProfile(language="html/web", validation_command="smoke test", execution_command="static verification workflow")

    return ExecutionProfile(language="unknown", validation_command="", execution_command="")

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
        "language_profile": profile.language,
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
