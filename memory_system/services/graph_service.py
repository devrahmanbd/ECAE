from typing import Dict, Any

def get_graph_context(query: str) -> Dict[str, Any]:
    return {
        "query": query,
        "impacted_dependencies": [
            {
                "entity": "user_auth_service",
                "type": "function",
                "risk_level": "high",
                "path": "src/auth/service.py"
            },
            {
                "entity": "test_user_auth",
                "type": "test",
                "risk_level": "medium",
                "path": "tests/auth/test_service.py"
            }
        ],
        "blast_radius": 2
    }

def get_graph_report() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "Graph system mocked out."
    }
