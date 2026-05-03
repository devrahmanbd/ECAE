from memory_system.services.graph_service import get_graph_context

def test_graph_context():
    query = "test context query"
    result = get_graph_context(query)

    assert "query" in result
    assert result["query"] == query
    assert "status" in result
    assert result["status"] in ["success", "missing_graph", "error", "exception"]
