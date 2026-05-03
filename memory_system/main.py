from fastapi import FastAPI
from memory_system.db.qdrant_client import init_collection
from memory_system.services.memory_service import store_memory, search_memory
from memory_system.services.graph_service import get_graph_context, get_graph_report
from memory_system.services.execution_service import execute_command, run_in_docker
from memory_system.models.schemas import StoreRequest, ExecuteRequest

app = FastAPI(title="AI Memory System")

@app.on_event("startup")
def startup():
    init_collection()

# ---------------- MEMORY ----------------

@app.post("/memory/store")
def store(req: StoreRequest):
    return store_memory(req.text, req.metadata)

@app.get("/memory/search")
def search(query: str):
    return search_memory(query)

# ---------------- GRAPH ----------------

@app.get("/graph/context")
def graph(query: str):
    return get_graph_context(query)

@app.get("/graph/report")
def report():
    return {"report": get_graph_report()}


# ---------------- EXECUTION ----------------

@app.post("/execute")
def execute(req: ExecuteRequest):
    if req.image:
        return run_in_docker(req.image, req.command, volumes={".": "/app"})
    return execute_command(req.command, req.workdir)

# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "services": ["memory", "graph"]
    }
