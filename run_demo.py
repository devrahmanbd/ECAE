from memory_system.agent_engine.orchestrator import AgentOrchestrator
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def main():
    orchestrator = AgentOrchestrator()
    task = "Fix the failing tests in demo_workspace/math_api.py without breaking existing functionality."

    workspace_dir = os.path.abspath("demo_workspace")
    print(f"Running demo with workspace: {workspace_dir}")

    result = orchestrator.process_task(task, workspace_dir=workspace_dir)
    print("\nFinal Result:")
    print(result)

if __name__ == "__main__":
    main()

# Initialize local qdrant for demo if it doesn't exist
try:
    client = QdrantClient(url="http://localhost:6333")
    if not client.collection_exists("memory"):
        client.create_collection(
            collection_name="memory",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
except Exception:
    pass
