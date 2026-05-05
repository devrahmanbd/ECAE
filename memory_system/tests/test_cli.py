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
        # Assuming ProjectGraph has the logic, but since parse_and_route_ecae_command calls the function directly with "."
        # it might not find the tempdir correctly if not mocked, but we can test the parsing logic

        # Test missing args
        res = parse_and_route_ecae_command("/ecae path a")
        assert "Error: Missing nodes" in res

        # We can't easily inject the root_dir into the global trace_graph_path call from the CLI parser without changing its signature,
        # so we'll mock the trace_graph_path in the test.
        import memory_system.cli_parser as cli
        original_trace = cli.trace_graph_path

        def mock_trace(a, b):
            return [a, "mid", b]

        cli.trace_graph_path = mock_trace
        try:
            res = parse_and_route_ecae_command('/ecae path "start" "end"')
            assert "start -> mid -> end" in res
        finally:
            cli.trace_graph_path = original_trace

def test_cli_explain_command():
    res = parse_and_route_ecae_command("/ecae explain")
    assert "Error: Missing node" in res

    import memory_system.cli_parser as cli
    original_explain = cli.explain_graph_node

    def mock_explain(node):
        return {"node": node, "type": "function", "path": "test.py", "called_by": ["caller"], "calls": []}

    cli.explain_graph_node = mock_explain
    try:
        res = parse_and_route_ecae_command('/ecae explain "test_node"')
        parsed = json.loads(res)
        assert parsed["node"] == "test_node"
        assert parsed["type"] == "function"
    finally:
        cli.explain_graph_node = original_explain

def test_graph_trace_and_explain_logic():
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_mock_project(tmpdir)
        graph = ProjectGraph(tmpdir)

        # Test trace
        path = graph.trace_graph_path("api.handle_request", "core_logic")
        assert len(path) == 2
        assert path[0] == "api.handle_request"
        assert path[1] == "core_logic"

        # Test explain
        explanation = graph.explain_graph_node("api.handle_request")
        assert explanation["node"] == "api.handle_request"
        assert explanation["type"] == "function"
        assert "core_logic" in explanation["calls"]
