# ECAE-lite Prototype Specification
## Predictive Entity-Centric Autonomous Engineering

**Author:** Prototype Engineering Draft
**Status:** Research Prototype
**Purpose:** Validate whether predictive graph filtering reduces coding errors, rework, and wasted execution cycles compared to reactive LLM-based coding.

---

## 1. Objective

This prototype tests one core hypothesis:

> **Predict-before-write reduces regression bugs, iteration count, and compute waste compared with write → fail → fix workflows.**

The prototype is intentionally small and measurable. It does **not** attempt to solve software engineering in full. It only demonstrates whether graph-based dependency reasoning and failure-memory reuse improve coding reliability.

---

## 2. Scope

### In Scope
- Build a causal dependency graph from a small codebase
- Predict the blast radius of proposed changes
- Reject unsafe changes before execution
- Execute only filtered candidates
- Store failures and successful patterns in a causal experience store
- Compare results against a baseline reactive agent

### Out of Scope
- Full autonomous product development
- Long-horizon planning across large repositories
- Human-level design reasoning
- Full formal verification

---

## 3. System Overview

### Baseline Workflow
```text
Generate → Execute → Fail → Fix → Repeat
```

### ECAE-lite Workflow
```text
Predict → Filter → Optimize → Generate → Execute → Learn
```

### Main Components
1. **Graph Builder** — constructs dependency graph
2. **Predictive Layer** — estimates impact of a change
3. **Decision Engine** — selects safe candidate actions
4. **Execution Engine** — runs tests in sandbox
5. **Causal Experience Graph (CEG)** — stores failures, fixes, and reusable patterns

---

## 4. Formal Model

### 4.1 Graph Representation
The software system is modeled as a directed attributed graph:

```text
G = (V, E, L)
```

Where:
- `V` = entities such as functions, APIs, modules, tests, and failures
- `E` = directed dependencies such as calls, event triggers, and data flow
- `L` = node labels or attributes such as risk, coverage, latency, and security score

Example:
```text
Frontend_Button → API_Handler → Payment_Service → Webhook_Listener
```

---

### 4.2 State Transition
A code change is treated as a transformation on graph state:

```text
G_{t+1} = f(G_t, Δ)
```

Where:
- `G_t` is the current graph state
- `Δ` is the proposed change
- `f` is the transition function that updates dependencies, labels, and failure predictions

---

### 4.3 Utility Function
Each candidate change is evaluated by a utility function:

```text
U(G') = Σ w_i · φ_i(G', Δ)
```

Where:
- `φ_i` is the metric for objective `i`
- `w_i` is the weight of objective `i`
- `Σ w_i = 1`

Typical utility terms:
- reliability
- performance
- simplicity
- maintainability
- security

---

## 5. Optimization Modes

The Decision Engine supports three selection strategies.

### 5.1 Pareto Optimization
A candidate is accepted if it is not dominated across all objectives.

A candidate `a_i` is Pareto-optimal if there is no `a_j` such that:

```text
U_k(G'_{j}) ≥ U_k(G'_{i}) for all k
```

and for at least one `m`:

```text
U_m(G'_{j}) > U_m(G'_{i})
```

---

### 5.2 Weighted Utility Maximization
Select the candidate with the maximum scalar utility:

```text
arg max_a U(G_{t+1})
```

This is the default mode for the prototype.

---

### 5.3 Minimax Adversarial Selection
Use an adversarial perturbation model:

```text
arg max_{a_coder} min_{a_attacker} U(G_{t+1}(a_coder, a_attacker))
```

This mode is used for high-risk paths such as authentication, payments, and security-sensitive changes.

---

## 6. Causal Experience Graph (CEG)

The **Causal Experience Graph** stores failure patterns and successful patterns.

### Entity Types
- `Failure`
- `Fix`
- `Pattern`
- `Skill`
- `Achievement`

### Failure Record Schema
```json
{
  "cause": "function_rename",
  "effect": "webhook_break",
  "context_graph": ["payment_service", "webhook_listener"],
  "fix": "introduce_mapping_layer",
  "timestamp": "..."
}
```

### Pattern Record Schema
```json
{
  "pattern": "renaming a payment function requires webhook dependency validation",
  "trigger": ["function_rename"],
  "prevention": ["dependency_check", "test_selection"],
  "confidence": 0.87
}
```

The CEG prevents repeated failures by matching new proposed changes against historical failure topology.

---

## 7. Prototype Algorithm

### Algorithm 1: Predictive Change Selection

**Input:** current graph `G_t`, proposed change `Δ`

**Output:** accepted or rejected change + execution result

```text
1. Build or update dependency graph G_t
2. Extract impacted subgraph S from Δ
3. Predict failure risk r(S)
4. Check hard constraints C(S)
5. If any constraint fails: reject Δ
6. Search CEG for similar failure patterns
7. If high-confidence match exists: reject or rewrite Δ
8. Score remaining candidates using utility U
9. Select best candidate a*
10. Execute a* in sandbox
11. Store result in CEG
12. If execution fails: derive fix and repeat
```

---

### Algorithm 2: Failure Pattern Matching

```text
Input: proposed change Δ, failure memory M
Output: match score m

1. Compute impacted nodes S from Δ
2. For each failure record f in M:
      a. Compare context graph of f with S
      b. Compare trigger type with Δ type
      c. Compare dependency topology
3. Aggregate similarity into score m
4. Return top-k matching failures
```

Similarity may be computed using:
- graph edit distance
- node overlap
- dependency path overlap
- weighted feature similarity

---

## 8. Mathematical Details

### 8.1 Risk Score
Define a risk function:

```text
r(Δ) = α · dependency_breaks + β · security_exposure + γ · test_gap + δ · historical_failure_match
```

Where:
- `dependency_breaks` = number of broken edges predicted by the graph
- `security_exposure` = count of security constraints violated
- `test_gap` = fraction of impacted nodes without tests
- `historical_failure_match` = similarity to known failures

A lower risk score is better.

---

### 8.2 Utility Score
Define utility as:

```text
U(Δ) = w_r · reliability + w_p · performance + w_s · simplicity + w_m · maintainability
```

Subject to:

```text
risk(Δ) < τ
```

Where `τ` is a risk threshold.

---

### 8.3 Decision Rule
A change is accepted only if:

```text
C(Δ) = true
risk(Δ) < τ
U(Δ) is maximal among safe candidates
```

This makes the system a **constrained optimization engine** rather than a pure generation loop.

---

## 9. Build Instructions

### 9.1 Prerequisites
- Python 3.11+
- Docker
- Git
- Optional: NetworkX, FastAPI, SQLite or JSON storage

### 9.2 Repository Layout
```text
prototype/
├── graph/
│   ├── builder.py
│   ├── predictor.py
│   └── metrics.py
├── ceg/
│   ├── store.py
│   ├── matcher.py
│   └── schema.py
├── engine/
│   ├── decision.py
│   ├── executor.py
│   └── loop.py
├── experiments/
│   ├── baseline.py
│   ├── ecae_lite.py
│   └── runner.py
├── data/
├── tests/
└── README.md
```

### 9.3 Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install networkx fastapi uvicorn pytest pydantic
```

Optional:
```bash
pip install tree-sitter
```

### 9.4 Run the Prototype
```bash
python -m experiments.runner --task payment_webhook_change
```

### 9.5 Run Tests
```bash
pytest -q
```

### 9.6 Run Sandbox Execution
```bash
docker run --rm -v "$PWD:/app" -w /app python:3.11 python -m pytest -q
```

---

## 10. Development Guide

### Phase 1 — Graph Construction
Start with a small project and extract:
- functions
- APIs
- test files
- event handlers
- shared utilities

Goal: produce a dependency graph with meaningful edges.

### Phase 2 — Prediction Heuristics
Implement simple rules first:
- rename detection
- dependency break detection
- missing reference detection
- test coverage gaps

Do not start with complex ML.

### Phase 3 — CEG Storage
Store:
- failures
- fixes
- graph context
- pattern confidence

Use this to reduce repeated mistakes.

### Phase 4 — Decision Engine
Implement Pareto, weighted utility, and minimax selection. Use hard constraints for security-sensitive conditions.

### Phase 5 — Evaluation
Compare against a baseline reactive agent.

Track:
- regressions introduced
- iterations until success
- repeated failures
- execution cost
- token usage

---

## 11. Experimental Protocol

### Task Family
Use small but realistic tasks:
- function rename
- API schema change
- webhook flow update
- frontend state update

### Baseline
Reactive LLM agent:
```text
Generate → Execute → Fail → Fix
```

### ECAE-lite
Predictive graph-aware agent:
```text
Predict → Filter → Optimize → Generate → Execute → Learn
```

### Metrics
- Regression Rate
- Iteration Count
- Failure Repetition Rate
- Token Cost
- Causal Accuracy

---

## 12. Success Criteria

The prototype is successful if it can:
- predict at least one real failure before execution
- reduce repeated mistakes compared with baseline
- reduce total iteration count
- preserve functional correctness on the test suite

---

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Graph too vague | Use a small project scope |
| Over-reliance on heuristics | Keep baseline comparison |
| Memory pollution | Store only failures, fixes, and reusable patterns |
| Overengineering | Keep prototype minimal |

---

## 14. Research Positioning

This prototype should be positioned as a **system-level synthesis** of:
- graph-based program analysis
- causal reasoning
- constrained optimization
- adversarial validation
- execution-grounded learning

It is not a claim of new foundational mathematics.
It is a proposal for a more reliable agentic software workflow.

---

## 15. Expected Contribution

If the experiment succeeds, the main contribution is:

> A structured development loop that reduces hallucination and rework by predicting dependency failures before code execution.

This is practically useful even if the system is not globally optimal.

---

## 16. Notes for Implementation

- Start small
- Measure everything
- Prefer deterministic heuristics first
- Treat failures as data
- Keep the graph explainable
- Avoid broad claims until experiments support them

---

## 17. Summary

ECAE-lite is a minimal prototype designed to prove that a causal dependency graph, failure memory, and constrained decision engine can improve coding reliability over reactive LLM workflows.

It is intentionally simple enough to build and evaluate, but expressive enough to test the core hypothesis of predictive, entity-centric autonomous engineering.

