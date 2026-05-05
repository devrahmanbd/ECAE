import os
import json
import pytest
import shutil
from memory_system.services.workspace_service import detect_workspace, get_execution_profile, init_project

@pytest.fixture
def temp_workspace(tmp_path):
    # Create a dummy workspace structure
    workspace = tmp_path / "my_project"
    workspace.mkdir()

    # Add a requirements.txt to simulate a python project
    (workspace / "requirements.txt").write_text("pytest\n")

    # Create a subfolder to test upward resolution
    subfolder = workspace / "src" / "module"
    subfolder.mkdir(parents=True)

    # Create a dummy file to be parsed by AST graph builder (needs valid python)
    (workspace / "main.py").write_text("def hello():\n    pass\n")

    yield workspace

    # Cleanup if necessary (tmp_path handles its own cleanup, but just in case)
    if workspace.exists():
        shutil.rmtree(workspace)

def test_detect_workspace(temp_workspace):
    subfolder = temp_workspace / "src" / "module"
    # Should resolve to the root where requirements.txt is
    root = detect_workspace(str(subfolder))
    assert root == str(temp_workspace)

def test_get_execution_profile(temp_workspace):
    profile = get_execution_profile(str(temp_workspace))
    assert profile == "python"

def test_init_project(temp_workspace):
    # Change current working directory to not mess up path resolutions, or just pass the path
    metadata = init_project(str(temp_workspace))

    assert metadata["project_root"] == str(temp_workspace)
    assert metadata["language_profile"] == "python"
    assert metadata["initialized"] is True

    # Check if graphify-out directory was created
    graphify_out = temp_workspace / "graphify-out"
    assert graphify_out.exists()
    assert graphify_out.is_dir()

    # Check if project.json was created
    project_json_path = graphify_out / "project.json"
    assert project_json_path.exists()

    with open(project_json_path, "r") as f:
        data = json.load(f)
        assert data["language_profile"] == "python"

    # Check if graph.json was created
    graph_json_path = graphify_out / "graph.json"
    assert graph_json_path.exists()

    with open(graph_json_path, "r") as f:
        graph_data = json.load(f)
        assert graph_data["status"] == "built"
        assert "nodes_count" in graph_data
