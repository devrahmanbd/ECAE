from memory_system.cli_parser import parse_and_route_ecae_command
from memory_system.services.graph_service import ProjectGraph
from memory_system.db.qdrant_client import init_collection
import tempfile
import os
import json

def setup_module(module):
    init_collection()

def setup_mock_project(base_dir):
    with open(os.path.join(base_dir, "service.py"), "w") as f:
        f.write("def core_logic():\n    return True\n")

    with open(os.path.join(base_dir, "api.py"), "w") as f:
        f.write("from service import core_logic\n\ndef handle_request():\n    return core_logic()\n")

def test_cli_parsing_missing_prefix():
    res = parse_and_route_ecae_command("some random command")
    assert "Error: Command must start with /ecae" in res

def test_cli_path_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)
        res = parse_and_route_ecae_command("/ecae path a")
        assert "Error: Missing nodes" in res

def test_cli_explain_command():
    res = parse_and_route_ecae_command("/ecae explain")
    assert "Error: Missing node" in res

def test_graph_trace_and_explain_logic():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)
        graph = ProjectGraph(tmpdir)

        path = graph.trace_graph_path("api.handle_request", "core_logic")
        assert len(path) == 2
        assert path[0] == "api.handle_request"
        assert path[1] == "core_logic"

        explanation = graph.explain_graph_node("api.handle_request")
        assert explanation["node"] == "api.handle_request"
        assert explanation["type"] == "function"
        assert "core_logic" in explanation["calls"]
