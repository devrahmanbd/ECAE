# ECAE Operational Runtime Documentation

## 1. What ECAE Is
ECAE is a predictive, orchestrated runtime for local agents. It operates not as a reactive chatbot, but as a deterministic state machine managing distributed cognitive tools. ECAE forces an explicit progression (Predict → Filter → Optimize → Generate → Execute → Learn) to ensure execution reliability and contextual safety. It relies on a sandboxed validation boundary to prove success and persists historical memory traces natively.

## 2. Architecture Overview
ECAE strictly separates responsibility across distinct layers. Do not confuse their purposes:

- **Orchestrator:** The sole control-flow authority. It owns the state machine transitions deterministically (`WORKSPACE_CHECK` -> `GRAPH_LOAD` -> `MEMORY_LOAD` -> `PREDICT` -> `FILTER` -> `OPTIMIZE` -> `GENERATE` -> `EXECUTE` -> `RESULT` -> `CRITIQUE` -> `LEARN`).
- **Graph Layer (Graphify):** The structural source of truth. It resolves AST-based dependencies and calculates blast radii. It does not store execution truth.
- **Memory Layer (Qdrant):** The contextual source of truth. It tracks hierarchical memory (Working, Episodic, Semantic, Skill, Causal, Operational) over time. It never overrides structural dependencies.
- **Execution Layer:** The sandbox truth. True execution takes place inside isolated Docker bounds. Success requires evidence convergence (e.g., test pass logs), not just an `exit_code == 0`.
- **Event Bus:** Asynchronous decoupler publishing runtime events (`EXECUTION_CRASHED`, `WORKSPACE_CHANGED`) natively.
- **MCP Router:** The dynamic entrypoint integrating AI IDEs natively tracking `stdio` without hardcoded path dependencies.
- **Evaluation & Governance:** Tracks drift, handles Rollback trace isolation, and bounds release capabilities dynamically (`/ecae evaluate`).

## 3. How ECAE is Started
ECAE operates seamlessly locally without hardcoded `graph.json` configuration traces.

- **Launcher:** Invoked via the local `/ecae` CLI executable or directly via module testing bounds (`PYTHONPATH=. python memory_system/mcp_server.py`).
- **Workspace Resolution:** ECAE dynamically walks up directories finding common project root boundaries (`package.json`, `.git`, `requirements.txt`).
- **MCP Entrypoint:** Communicates natively via JSON-RPC over `stdout`. HuggingFace and application logs are routed to `stderr` guaranteeing protocol integrity.
- **Graph Refresh:** Graph dependencies are assembled or refreshed natively in memory dynamically upon the `GRAPH_LOAD` state iteration.

## 4. How to use ECAE with Antigravity (or similar AI IDEs)
Antigravity connects via the native Model Context Protocol (MCP) server endpoints.

1. **Connection:** Point your configuration strictly to `memory_system/mcp_server.py` natively executing with the official Python MCP SDK.
2. **Dynamic Binding:** Do not modify repository configurations. ECAE dynamically resolves the active workspace using the `.git` boundaries regardless of where it starts.
3. **Execution Routing:** The IDE must route `/ecae` logic explicitly through the exposed `ecae_cli` tool.
4. **Limits:** Do NOT hardcode per-project settings. Do NOT instruct the IDE to bypass orchestrator execution flows. Do NOT fabricate `graph.json` wrappers locally.

## 5. Operating Rules
To maintain the predictive stability of ECAE, the following invariants are enforced:

- **Graph facts are structural only.**
- **Memory facts are contextual only.**
- **Execution facts come from sandbox results.**
- **Orchestrator owns control flow.**
- **No tool call, no claim:** Never answer from memory or graph isolated contexts without validating real sandbox trace data.
- **No exit code alone means success:** Validation logs must explicitly confirm convergence (e.g., testing suites logging "pass").
- **No guessed result:** If an error occurs, it is recorded into `CAUSAL FAILURE` bounds organically.

## 6. Typical Workflows
The CLI manages interaction explicitly through `cli_parser.py`:

- **Starting on a new workspace:** ECAE evaluates directories natively. Simply run `/ecae init .`
- **Running a task:** Leverage the orchestrator native hooks `/ecae . --task "Refactor login token generation"`
- **Recovering from a failure:** Crashed executions natively trigger the orchestration state machine to consult `CAUSAL FAILURE` memories natively predicting recovery limits.
- **Re-running after a crash:** The `RuntimeQueue` caches queued scheduling limits safely.
- **Watching graph state:** Use `/ecae explain <node>` or `/ecae path <node_a> <node_b>`.
- **Running evaluations:** Run `/ecae evaluate` to calculate Release Readiness governance limits or `/ecae dashboard` to trace synthetic benchmark logic bounds.

## 7. Safety and Limitations
- **Capabilities:** Can securely evaluate, rewrite, rollback, and test arbitrary Python/Go/TS/JS implementations securely predicting side effects using the dependency graph.
- **Limitations:** Cannot operate reliably outside of Dockerized sandboxes.
- **Missing Boundaries:** If Graph structures, Memory servers (Qdrant), or Sandbox bounds fail, the Orchestrator stops cleanly emitting a `Background Worker Loop Exception` without guessing logic safely.
- **Clean execution:** You must not leave `modify_*.py`, `debug_*.py`, or scratchpad temporary artifacts in the root directory. `evaluate_release_readiness` blocks releases if garbage tracks remain.

## 8. Troubleshooting
- **Stop Conditions:** The Orchestrator will print "Max iterations reached" or explicit sandbox unavailability traps stopping safely.
- **Interpreting Failures:** Failures write into causal memory naturally. Inspect using explicit `search_memory` calls evaluating `<task> resulted in failure`.
- **Governance Flags:** If `/ecae evaluate` throws FAIL, ensure no test scripts remain and check that `analyze_learning_trends()` limits aren't regressing significantly.
- **MCP Startup Issues:** Ensure `python-mcp`, `qdrant-client`, and `fastapi` are available to avoid missing package crashes. Check `stderr` for HuggingFace model download traces.

## 9. Best Practices for AI IDE Usage
- Follow the workflow boundaries implicitly: 1. `search_memory`, 2. `get_graph_context`, 3. `execute_command`, 4. Route `/ecae` limits to the CLI tools.
- Do not manually manipulate path limits (especially `graph.json`).
- Assume all modifications introduce regressions until validated through the sandbox. Ground decisions only through explicit execution testing logic natively validating test suite integrations explicitly.

## 10. Quick-Start
1. Spin up the Qdrant DB natively (`docker run -d -p 6333:6333 qdrant/qdrant` or rely on the local memory fallback).
2. Configure your AI IDE (like Antigravity) attaching `memory_system/mcp_server.py`.
3. Dispatch your required implementation target directly using the `ecae_cli` endpoint.
4. Let the Orchestrator perform loop completion safely checking release bounds dynamically.