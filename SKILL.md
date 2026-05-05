# SKILL.md: ECAE Agent System

## Purpose
This document enforces the system architecture and runtime guarantees of the Predictive Entity-Centric Autonomous Engineering (ECAE) system.

## Architectural Constraints
- **Graph Layer:** Must remain strictly structural (ast-based) and devoid of context logic. Avoid explicit `graph.json` locks; prefer dynamic generation.
- **Memory Layer:** Uses Qdrant (`memory_system/db`). Must provide explicit retrieval evidence before making decisions. Both success and failure states must be logged.
- **Execution Layer:** A Docker sandbox (`memory_system/services/execution_service.py`). The sole source of truth for validation.
- **Orchestrator:** The minimal state machine. MUST route cleanly without hallucinations.
- **Antigravity integration:** Stable MCP route exposed. The single MCP entrypoint is `/memory-system-agent`, utilizing standard `get_prompt` protocols.

## Validations
No structural change is accepted unless:
1. `get_graph_context` is successfully requested.
2. A test passes via the docker sandbox.
3. Memory is successfully retrieved beforehand, and saved afterward.

## Commands
Use `./ecae . --task "<task>"` locally or route through Antigravity MCP CLI calls to execute orchestrator paths.
