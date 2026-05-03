import subprocess
import os
from memory_system.models.schemas import GraphContext

def get_graph_context(query: str) -> GraphContext:
    """
    Use graphify CLI to get context from the knowledge graph.
    """
    graphify_out = "graphify-out/graph.json"

    if not os.path.exists(graphify_out):
        return GraphContext(
            query=query,
            context="Knowledge graph not found. Run 'graphify update .' first.",
            status="missing_graph"
        )

    try:
        # Try to use 'graphify query' for BFS traversal
        cmd = f"PYTHONPATH=./graphify python3 -m graphify query \"{query}\" --graph {graphify_out}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return GraphContext(
                query=query,
                context=result.stdout.strip(),
                status="success"
            )
        else:
            return GraphContext(
                query=query,
                context=f"Error running graphify: {result.stderr}",
                status="error"
            )

    except Exception as e:
        return GraphContext(
            query=query,
            context=str(e),
            status="exception"
        )

def get_graph_report():
    """Read the GRAPH_REPORT.md file."""
    report_path = "graphify-out/GRAPH_REPORT.md"
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return f.read()
    return "Report not found."
