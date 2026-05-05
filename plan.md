# PLAN.md — ECAE Autonomous Loop Upgrade

## Objective

Build a stronger ECAE system that can run autonomously inside Antigravity and across multiple project types.

The system must repeatedly execute this loop:

**Predict → Filter → Optimize → Generate → Execute → Result (success/fail) → Learn (from both success and failure)**

It must also:

* detect the active project automatically,
* build or refresh the project graph without manual intervention,
* expose a stable MCP interface that works across projects,
* avoid hard-coded `graph.json` paths in Antigravity,
* support multiple languages and project types,
* and keep graph, memory, and execution responsibilities strictly separated.

## Current Problems To Fix

1. Antigravity points to a fixed `graph.json` path, so each new project needs manual config edits.
2. The current flow is mostly linear instead of looping.
3. Graph creation is not automatic at project open.
4. The system does not always force tool use before answering.
5. The memory layer and graph layer are not cleanly separated in behavior.
6. The execution layer does not fully feed results back into learning.
7. Support is too Python-centric and must extend to Go, HTML, Redis, SQL, Postgres, and other common project types.

## Target Architecture

### 1) Graph Layer

Understands structure:

* files
* modules
* imports
* calls
* dependencies
* blast radius

Responsibilities:

* build a graph for the current workspace
* refresh the graph when files change
* expose structural context only
* never answer semantic questions from memory

### 2) Memory Layer

Understands context:

* prior fixes
* repeated failures
* successful patterns
* project-specific decisions

Responsibilities:

* store both success and failure outcomes
* retrieve relevant prior decisions
* rank memory by relevance
* avoid duplicate memories
* return context, not structure

### 3) Execution Layer

Prepares environment and runs code:

* install dependencies
* run tests
* run app
* capture stdout, stderr, and exit code

Responsibilities:

* execute only inside sandboxed environments
* use project-specific execution profiles
* return structured results
* never guess outcomes

### 4) Orchestrator

Coordinates the full loop:

* decide
* try
* validate
* learn
* retry or stop

Responsibilities:

* call graph first
* call memory second
* choose a safe candidate
* execute in sandbox
* store outcome
* repeat until success or stop condition

## Runtime Interfaces

### Launcher Requirement

Create a real `ecae` entrypoint on PATH.

It should support commands like:

* `ecae init`
* `ecae serve`
* `ecae run "<task>"`
* `ecae graph`
* `ecae doctor`

The launcher must:

* detect the current project root,
* create or refresh the graph automatically,
* start the MCP layer for that project,
* run the orchestration loop,
* and write back success/failure memory.

### Dynamic MCP Requirement

Antigravity must point to one stable MCP command, not a per-project `graph.json` file path.

Required behavior:

* the MCP server resolves the active workspace automatically,
* it builds `graphify-out/graph.json` if missing,
* it exposes `search_memory`, `get_graph_context`, `store_memory`, and `execute_command`,
* it works across projects without manual config edits.

## Execution Profiles

Support multiple project types with explicit profiles:

* Python: `pytest`, `python main.py`
* Go: `go test ./...`, `go build ./...`
* JS/TS: `npm test`, `npm run build`
* SQL/Postgres: migration + validation scripts
* Redis: health check + integration tests
* HTML/web: browser or smoke-test profile

## Learning Payloads

Store both success and failure outcomes.

Each memory item should include:

* task
* action
* graph context
* execution result
* reason
* outcome
* confidence
* affected files

## SKILL.md Update Requirements

The skill must enforce these rules:

* graph first
* memory second
* execution third
* learn from both success and failure
* no fake CLI assumptions
* no manual graph path edits
* no success without execution proof
* no mixing graph facts with memory facts

It must also say:

> If graph, memory, or execution are unavailable, stop and report the missing layer.

## Rules Engine Requirements

Add hard rules:

* Graph answers must stay structural.
* Memory answers must stay contextual.
* Execution answers must stay evidence-based.
* No tool call, no claim.
* No exit code, no success.
* No workspace detected, no run.

Add stop states:

* `allow`
* `reject`
* `retry`
* `stop`

## Suggested Document Flow

Your document is already solid, but it would flow more cleanly if reorganized into:

1. Problem Statement
2. Target Architecture
3. System Components (Graph / Memory / Execution / Orchestrator)
4. Runtime Interfaces (ecae + MCP)
5. Execution Loop Design
6. Policies (SKILL.md + Rules Engine)
7. Implementation Phases
8. Acceptance Criteria

## Minimal Orchestrator Reference Implementation

The implementation should stay small and deterministic: a state machine plus a dynamic MCP router plus a workspace resolver.

It should not rely on fake CLI assumptions.

It should do this:

1. detect workspace root
2. resolve or rebuild the current graph
3. load relevant memory
4. predict candidate actions
5. filter unsafe paths
6. optimize candidate selection
7. generate the change
8. execute in sandbox
9. learn from both success and failure
10. repeat until stop condition

That is the smallest useful version of the orchestrator that matches the loop exactly.

## Implementation Phases

### Phase 1 — Project Bootstrapper

Build a bootstrap command that:

* creates `.ecae/`
* writes project metadata
* detects supported languages
* builds the initial graphify output
* registers the project with the orchestrator

### Phase 2 — Dynamic MCP Router

Build the MCP server so it:

* serves the current workspace automatically
* resolves the graph path dynamically
* exposes the core tools
* requires no per-project config edits

### Phase 3 — Orchestrator Loop

Implement the loop:

1. Predict using graph + memory
2. Filter unsafe paths
3. Optimize candidate selection
4. Generate the change
5. Execute in sandbox
6. Read the result
7. Learn from the result
8. Repeat until stop condition

### Phase 4 — Cross-language Execution Profiles

Add language-specific profiles for Python, Go, JS/TS, SQL/Postgres, Redis, and HTML/web.

### Phase 5 — Skill and Rules Enforcement

Update `SKILL.md` and the rules engine so tool use is mandatory and the assistant cannot answer without the proper layer.

## Acceptance Criteria

The upgrade is complete only when all of the following are true:

* Antigravity can open any new project without editing `mcp_config.json`.
* The system can auto-build or refresh the project graph.
* The orchestrator loops through predict/filter/optimize/generate/execute/learn.
* Success and failure are both written to memory.
* Graph, memory, and execution remain separate and testable.
* The system supports more than Python projects.
* The skill file and rules engine force correct tool usage.

## Immediate Next Deliverables

1. Follow `PLAN.md` roadmap
2. Updated `SKILL.md`
3. Update rules engine `ecae.md` and Update `ecae_workflow.md`
4. `ecae` launcher
5. Dynamic MCP router
6. Orchestrator loop
7. Execution profiles for multiple languages
