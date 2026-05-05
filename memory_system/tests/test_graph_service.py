import os
import tempfile
from memory_system.services.graph_service import get_graph_context, ProjectGraph

def setup_mock_project(base_dir):
    # Create service file
    service_code = """
def core_logic():
    return True
"""
    with open(os.path.join(base_dir, "service.py"), "w") as f:
        f.write(service_code)

    # Create API file that depends on service
    api_code = """
from service import core_logic

# Mocking a FastAPI endpoint for our heuristic
@app.get("/endpoint")
def handle_request():
    result = core_logic()
    return result
"""
    with open(os.path.join(base_dir, "api.py"), "w") as f:
        f.write(api_code)

    # Create test file that depends on both
    test_code = """
from api import handle_request
from service import core_logic

def test_api():
    assert handle_request()

def test_service():
    assert core_logic()
"""
    with open(os.path.join(base_dir, "test_app.py"), "w") as f:
        f.write(test_code)

def test_graph_dependency_correctness():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)
        graph = ProjectGraph(tmpdir)

        # Verify nodes exist
        assert "service.core_logic" in graph.nodes
        assert "api.handle_request" in graph.nodes
        assert "test_app.test_service" in graph.nodes

        # Verify edges (call dependencies)
        # handle_request calls core_logic
        assert "core_logic" in graph.edges["api.handle_request"] or "service.core_logic" in graph.edges["api.handle_request"]
        # test_api calls handle_request
        assert "handle_request" in graph.edges["test_app.test_api"] or "api.handle_request" in graph.edges["test_app.test_api"]

def test_graph_impact_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)

        # Impact of changing core_logic
        result = get_graph_context("Modify core_logic", root_dir=tmpdir)

        assert result.status == "success"
        assert result.blast_radius > 0

        impacted_entities = [d.entity for d in result.impacted_dependencies]

        # Changing core_logic should impact the API and tests
        # We need to make sure the exact node names match
        assert "api.handle_request" in impacted_entities or "api" in impacted_entities or "service" in impacted_entities
        assert "test_app.test_service" in impacted_entities or "test_app" in impacted_entities

def test_graph_no_impact():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)

        # Impact of a non-existent function
        result = get_graph_context("Change nonexistent_function", root_dir=tmpdir)

        assert result.status == "not_found"
        assert result.blast_radius == 0
        assert len(result.impacted_dependencies) == 0
