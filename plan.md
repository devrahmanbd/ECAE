# 🧠 AI Development System Setup Plan

## Goal

Build a reliable AI-assisted development system that:

* Does NOT break existing code
* Understands project structure (Graphify)
* Recalls past decisions (Qdrant memory)
* Executes and tests code in isolated sandboxes
* Iterates until validation passes
* Works inside Antigravity IDE

---

# 🧱 Phase 1: Core Infrastructure

## 1. Install Vector Database (Qdrant)

Run Qdrant using Docker:

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

Test:

* Open `http://localhost:6333`
* It should show Qdrant API response or dashboard behavior depending on version

---

## 2. Create Memory API (RAG Bridge)

Create a file: `memory_api.py`

Install dependencies:

```bash
pip install fastapi uvicorn qdrant-client sentence-transformers
```

Add code:

```python
from fastapi import FastAPI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import uuid

app = FastAPI()

client = QdrantClient("localhost", port=6333)
model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION = "memory"


@app.on_event("startup")
def setup():
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )


@app.post("/store")
def store_memory(data: dict):
    vector = model.encode(data["text"]).tolist()

    client.upsert(
        collection_name=COLLECTION,
        points=[{
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": data
        }]
    )
    return {"status": "stored"}


@app.get("/search")
def search_memory(query: str):
    vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=5
    )

    return [r.payload for r in results.points]
```

Run API:

```bash
uvicorn memory_api:app --reload --port 8000
```

Test:

* `http://localhost:8000/search?query=test`

---

# 🧩 Phase 2: Graphify Integration

## 3. Install Graphify

Clone or include:

* [https://github.com/safishamsi/graphify](https://github.com/safishamsi/graphify)

---

## 4. Create Graph API Wrapper

Add to `memory_api.py`:

```python
@app.get("/graph_context")
def graph_context(query: str):
    # Replace with actual Graphify call
    result = f"Graph context for: {query}"
    return {"context": result}
```

This can later be replaced with a real Graphify call or wrapper service.

---

# 🔌 Phase 3: Antigravity Integration

## 5. Add Tools in Antigravity IDE

Open:

* Agent Manager → Tools → Add Tool

---

### Tool 1: search_memory

* Name: `search_memory`
* Method: `GET`
* URL: `http://localhost:8000/search`

Parameter:

* `query` → `{{input}}`

---

### Tool 2: store_memory

* Name: `store_memory`
* Method: `POST`
* URL: `http://localhost:8000/store`

Body:

```json
{
  "text": "{{input}}"
}
```

---

### Tool 3: graph_context

* Name: `graph_context`
* Method: `GET`
* URL: `http://localhost:8000/graph_context`

Parameter:

* `query` → `{{input}}`

---

# 🧭 Phase 4: Behavior Control (Critical)

## 6. Create `PROJECT.md`

```md
# Project Goal
[Describe your system]

# Rules
- Never break API contracts
- All DB changes require migration
- Maintain backward compatibility

# Architecture
- [Your architecture]
```

---

## 7. Add Agent System Prompt

```md
MISSION_START:

Before coding:
1. Call graph_context to understand structure
2. Call search_memory for relevant patterns
3. Read PROJECT.md rules

Then:
4. Propose a plan
5. List risks
6. Show affected files

After completion:
7. Summarize decision
8. Call store_memory
```

---

# 🔁 Phase 5: Workflow

## Daily Usage Flow

1. Ask Antigravity to build a feature
2. Agent:

   * Uses Graphify → understands code
   * Uses Qdrant → recalls patterns
   * Reads PROJECT.md → respects rules
3. Agent proposes plan
4. You review
5. Agent writes code
6. You run tests
7. Agent stores memory

---

# ⚙️ Phase 6: Optional Enhancements

## Add Metadata

Store richer memory:

```json
{
  "problem": "...",
  "decision": "...",
  "reason": "...",
  "outcome": "...",
  "tags": ["auth", "billing"]
}
```

---

## Add Tailscale (for remote server)

Use:

* Tailscale

Benefits:

* Secure private access
* No public ports exposed

---

## Add Dify (optional)

Use:

* Dify

Only for:

* document ingestion
* chunking
* UI

Keep it optional; do not make it part of the core control loop.

---

# 🧠 Final Architecture

```text
Antigravity IDE
↓
Tools (API)
↓
Memory API (FastAPI)
↓
├── Qdrant (semantic memory)
└── Graphify (code structure)
```

---

# 🧾 Final Notes

* Memory helps recall patterns, NOT enforce correctness
* Graphify prevents structural mistakes
* PROJECT.md enforces rules
* Tests are mandatory for reliability

---

# ✅ Result

You now have:

* Persistent memory across projects
* Structural awareness of code
* Controlled, safer AI development workflow

---

# 🧠 Target System Design (clean + scalable)

Split the system into 5 layers:

```text
API Layer (FastAPI routes)
   ↓
Service Layer (logic)
   ↓
Memory Layer (Qdrant)
   ↓
Embedding Layer (SentenceTransformer)
   ↓
Graph Layer (Graphify)
```

---

# 🏗️ FINAL SYSTEM STRUCTURE

Create this folder layout:

```text
memory_system/
│
├── main.py
├── core/
│   ├── config.py
│   ├── embeddings.py
│
├── services/
│   ├── memory_service.py
│   ├── graph_service.py
│
├── db/
│   ├── qdrant_client.py
│
└── models/
    ├── schemas.py
```

---

## ⚙️ 1. Config: `core/config.py`

```python
COLLECTION_NAME = "memory"
VECTOR_SIZE = 384
```

---

## 🧠 2. Embedding Layer: `core/embeddings.py`

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str):
    return model.encode(text).tolist()
```

---

## 🗄️ 3. Qdrant Layer: `db/qdrant_client.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from core.config import COLLECTION_NAME, VECTOR_SIZE

client = QdrantClient("localhost", port=6333)

def init_collection():
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
```

---

## 🧠 4. Memory Service: `services/memory_service.py`

```python
import uuid
from db.qdrant_client import client
from core.config import COLLECTION_NAME
from core.embeddings import embed


def store_memory(text: str, metadata: dict = None):
    vector = embed(text)

    payload = {
        "text": text,
        "metadata": metadata or {}
    }

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[{
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": payload
        }]
    )

    return {"status": "stored"}


def search_memory(query: str):
    vector = embed(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=5
    )

    return [
        r.payload for r in results.points
    ]
```

---

## 🧠 5. Graph Service: `services/graph_service.py`

```python
def get_graph_context(query: str):
    # Replace with real Graphify call later
    return {
        "query": query,
        "context": f"Graph structure context for: {query}"
    }
```

---

## 📦 6. API Schemas: `models/schemas.py`

```python
from pydantic import BaseModel
from typing import Optional, Dict

class StoreRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = None
```

---

## 🚀 7. Main API: `main.py`

```python
from fastapi import FastAPI
from db.qdrant_client import init_collection
from services.memory_service import store_memory, search_memory
from services.graph_service import get_graph_context
from models.schemas import StoreRequest

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


# ---------------- HEALTH ----------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "services": ["memory", "graph"]
    }
```

Run it:

```bash
uvicorn main:app --reload --port 8000
```

---

# 🧠 What you now have (important)

Before:

* single-file prototype
* tightly coupled logic
* fragile

After:

You now have a real system architecture

| Layer      | Responsibility         |
| ---------- | ---------------------- |
| API        | Antigravity interface  |
| Service    | logic                  |
| Qdrant     | memory                 |
| Graphify   | structure              |
| Embeddings | semantic understanding |

---

# 🔌 How Antigravity connects now (Official MCP Method)

The system utilizes **MCP (Model Context Protocol)** for unified tool discovery. Add this to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "memory-system": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "http://localhost:8000"]
    },
    "graphify": {
      "command": "uv",
      "args": ["run", "--with", "graphifyy", "--with", "mcp", "-m", "graphify.serve", "${workspace.path}/graphify-out/graph.json"]
    }
  }
}
```

---

# 🧪 Phase 6: Execution & Testing Sandbox (NEW CORE LAYER)

## Goal

Enable the AI system to:

* run code safely
* test web applications
* test Go services
* validate outputs automatically
* feed results back into the agent loop

---

## 1. Add Execution Sandbox Layer

Recommended architecture:

```text
Antigravity IDE
      ↓
Agent Loop Controller
      ↓
Execution API (NEW)
      ↓
Docker Sandbox Runner
      ↓
Test Results → back to agent
```

---

## 2. Use Docker as the Execution Layer (MANDATORY)

Do NOT run code directly on the host.

Every execution happens inside containers.

---

## 3. Execution API Design

Endpoint: `POST /execute`

Input:

```json
{
  "language": "go",
  "code_path": "./project",
  "command": "go test ./..."
}
```

Output:

```json
{
  "success": true,
  "stdout": "...",
  "stderr": "...",
  "tests_passed": 12,
  "tests_failed": 0
}
```

---

## 4. Docker Sandbox Strategy (IMPORTANT)

### Option A (Simple + strong)

Use ephemeral containers.

Go example:

```bash
docker run --rm -v $PWD:/app -w /app golang:1.22 go test ./...
```

Node/Web:

```bash
docker run --rm -v $PWD:/app -w /app node:20 npm test
```

Python:

```bash
docker run --rm -v $PWD:/app -w /app python:3.11 pytest
```

---

## 5. Add Execution Service (FastAPI layer)

`execution_service.py`

```python
import subprocess
from fastapi import FastAPI

app = FastAPI()

@app.post("/execute")
def execute(cmd: str):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 6. How this connects to the loop system

Your agent loop becomes:

1. Plan
2. Generate code
3. Write to workspace
4. Call `execution_api`
5. Get results
6. Fix errors
7. Repeat

---

## 7. Web Software Testing (important upgrade)

For web apps:

### Option A (best): Playwright container

```bash
docker run --rm mcr.microsoft.com/playwright
```

Use it for:

* UI tests
* API tests
* full browser simulation

### Option B: Headless browser service

Add Playwright or Puppeteer for:

* login flows
* API validation
* UI checks

---

## 8. Go Software Testing (your use case)

Inside sandbox:

```bash
go test ./...
go build ./...
```

Return:

* test coverage
* failures
* logs

---

## 9. Loop integration (CRITICAL)

Your loop controller now becomes:

```text
FOR each iteration:

  1. generate code
  2. write to container workspace
  3. execute in sandbox
  4. collect results
  5. feed back into agent
  6. update Qdrant memory
```

---

## 10. Why this is the real breakthrough

Now your system has:

| Layer           | Function           |
| --------------- | ------------------ |
| Qdrant          | memory             |
| Graphify        | structure          |
| Antigravity     | reasoning          |
| Docker sandbox  | truth verification |
| loop controller | iteration          |

---

# 🚀 Result

You now have:

> A self-correcting software development system

Not:

* RAG system
* chatbot
* IDE assistant

---

# ⚠️ Important limitation (honest truth)

Even with this:

* it will still fail complex architecture decisions
* it will still need constraints (`PROJECT.md`)
* it will still need human review for critical systems

But:

> It will reliably improve itself through iteration

---

# 🧭 Final Summary

This plan gives you:

* Persistent memory across projects
* Structural code awareness
* Safe execution and testing
* Autonomous loop correction
* IDE-native control in Antigravity

---

# 🚀 Next Step Ideas

Possible future upgrades:

* add reranking layer to improve memory quality
* add caching (Redis)
* add streaming responses
* replace Graphify stub with real integration
* build a multi-agent version:

  * planner agent
  * coder agent
  * tester agent
  * critic agent
  * memory curator agent
