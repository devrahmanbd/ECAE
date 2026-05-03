# Phase 0 — System Boundaries

## 1. Phase Objective
Define the system responsibilities and constraints for the AI Development System (ECAE-lite) to ensure non-overlapping roles before building subsequent components.

## 2. Implementation Plan
- Document the roles of the core systems: Memory, Graph, Execution, and Orchestrator.
- Document system rules.
- Document success criteria.

## 3. Dependencies Check
- None. This is the foundational planning phase.

## 4. Build Instructions
See roles and rules defined below.

## 5. Unit Test Plan
- Requirements completeness review (manual verification).
- Role separation validation (manual verification).

## 6. Roles & Responsibilities

### Memory System
- Stores and retrieves prior decisions and failure patterns.
- Acts as a decision input to prevent repeated mistakes and guide candidate generation.
- Owner: Memory Layer.

### Graph System
- Understands the project as a graph of connected entities (functions, APIs, tests).
- Provides structural context and dependency impact analysis before code changes.
- Owner: Graph Layer.

### Execution System
- Runs code in isolated sandboxes (Docker).
- Acts as the final deterministic truth layer to validate changes.
- Owner: Execution Layer.

### Orchestrator
- Connects memory, graph, and execution into a predictive decision and planning loop.
- Proposes candidates, scores them, and manages the lifecycle until validation passes.
- Owner: Decision Layer.

## 7. System Rules
- **Memory is a decision input**, not just storage.
- **Graphify is a structural context layer**, not a replacement for reasoning.
- **Execution is the final truth layer**. No change is accepted without validation.

## 8. Success Criteria
- Reduced hallucinated code.
- Reduced duplicated mistakes.
- Reduced broken dependencies.
- Reduced wasted execution cycles.
- All system responsibilities are clearly non-overlapping.

## 9. Output Artifacts
- `PROJECT.md` (this file).

## 10. Stop Condition
- Wait for team agreement on the defined boundaries.
