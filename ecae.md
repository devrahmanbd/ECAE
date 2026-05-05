## ECAE

This project uses the ECAE autonomous loop system with a dynamic graph, memory, execution, and MCP orchestration layer.

The system is workspace-aware and must not rely on static configuration paths like `graph.json`.

---

## Core Principle

**Graph = structure**
**Memory = history**
**Execution = truth**
**Orchestrator = loop controller**

---

## Rules

### 1) Workspace First

* Always detect the active workspace before any reasoning
* If workspace cannot be detected, stop execution and report missing context

---

### 2) Graph Layer Usage

* Before answering architecture, dependency, or codebase questions, query the graph layer using MCP tools:

  * `get_graph_context`
  * `query_graph` (if available)
  * `get_node`
  * `shortest_path`

* The graph is the source of structural truth

* Do NOT infer architecture from memory alone

* Do NOT guess module relationships without graph confirmation

---

### 3) Memory Layer Usage

* Use memory only for historical outcomes:

  * past failures
  * past successful fixes
  * recurring patterns

* Use MCP tools:

  * `search_memory`
  * `store_memory`

* Memory must NEVER override graph structure

---

### 4) Execution Layer Usage

* All code-level validation must go through execution:

  * `execute_command`

* Execution results are the only source of truth for:

  * success
  * failure
  * correctness

* Never assume execution outcomes without sandbox results

---

### 5) MCP First Principle

* Always prefer MCP tools over manual file inspection
* If MCP server is active, NEVER fall back to raw filesystem grep for:

  * architecture questions
  * dependency tracing
  * cross-module navigation

---

### 6) CLI Fallback Rules (Only if MCP is unavailable)

If MCP is not active:

* Use workspace-aware CLI equivalents instead of grep:

  * graph query → `ecae graph query "<question>"`
  * path search → `ecae graph path "A" "B"`
  * explain → `ecae graph explain "<concept>"`

Do NOT use raw grep for structural reasoning unless no other option exists

---

### 7) Graph Maintenance

* After any code modification:

  * update graph automatically via MCP or CLI equivalent
  * ensure graph stays AST-consistent

* Never require manual `graph.json` editing

---

### 8) Tool Use Discipline

* No answer without tool confirmation when tools are available
* No hallucinated execution results
* No inferred success/failure without execution output

---

### 9) Failure Handling

* If execution fails:

  * store failure in memory
  * analyze graph context for structural cause
  * retry only after optimization step

---

### 10) Stop Conditions

Stop execution loop if:

* workspace is invalid
* graph is unavailable
* memory layer is unreachable
* execution sandbox is offline

---

## Summary

ECAE operates as a closed-loop system:

**Predict → Filter → Optimize → Generate → Execute → Observe → Learn → Repeat**

The graph defines structure, memory defines experience, execution defines truth, and MCP ensures workspace-aware coordination without manual configuration.
