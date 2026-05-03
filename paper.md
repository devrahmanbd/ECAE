# Predictive Entity-Centric Autonomous Engineering (ECAE)
## A Graph-Based, Multi-Objective Framework for Reliable AI-Assisted Software Development

**Status:** Research Draft / Submission-Style Paper

---

## Abstract

Large language model (LLM)-based coding systems improve developer productivity, but they frequently produce hallucinated, inconsistent, or redundant code due to weak structural awareness of software dependencies. Most current workflows remain reactive: a model generates code, the system executes it, and failures are fixed iteratively. This paper proposes **Predictive Entity-Centric Autonomous Engineering (ECAE)**, a graph-based framework for software development that models codebases as typed entity graphs and evaluates candidate changes before execution. The system combines dependency-aware context selection, multi-perspective scoring, constrained optimization, and execution-grounded memory to reduce regressions and repeated mistakes.

ECAE is positioned as a **system-level synthesis** of established fields, including graph-based program analysis, multi-objective optimization, adversarial robustness, causal reasoning, program synthesis, and control theory. We do not claim a new foundational theory of computation. Instead, we propose a practical architecture for improving agentic software engineering by introducing a **predict-before-write** loop.

---

## 1. Introduction

AI-assisted software development systems often fail in subtle ways: variable names are forgotten, dependencies are broken, code is duplicated, and previously solved problems reappear. These failures arise because the model reasons over text rather than over the structural state of the software.

This work proposes a different abstraction: software should be treated as an evolving graph of entities. A feature, module, bug, test, fix, or version is not merely text or a file path, but a structured element in a causal graph. The graph exposes dependencies and blast radius, allowing the system to predict which parts of the codebase may be affected before it writes code.

The key idea is that development should be driven by a pipeline of:

**Predict → Filter → Optimize → Generate → Execute → Learn**

rather than the usual:

**Generate → Execute → Fail → Fix**

This paper describes the architecture, mathematical framing, and evaluation plan of ECAE.

---

## 2. Problem Statement

Given a codebase with hidden dependencies and a proposed change, standard agentic coding systems struggle to answer:

- Which modules will this change affect?
- What failures are likely to appear downstream?
- Which candidate fixes are safest?
- How do we prevent repeated mistakes?

The central problem is to select a code transformation that satisfies hard constraints, improves utility, and remains robust under adversarial or uncertain runtime conditions.

---

## 3. System Design

### 3.1 High-Level Architecture

The ECAE system contains five components:

1. **Graph Builder** — constructs a dependency graph from the project.
2. **Predictive Layer** — estimates the blast radius of a proposed change.
3. **Decision Engine** — ranks candidate actions using Pareto, weighted utility, or minimax selection.
4. **Execution Engine** — runs sandboxed tests and builds.
5. **Causal Experience Graph (CEG)** — stores failures, fixes, and reusable patterns.

### 3.2 Entity-Centric Representation

The codebase is modeled as a directed attributed graph:

\[
G = (V, E, L)
\]

where:
- \(V\) is the set of entities,
- \(E\) is the set of directed dependency edges,
- \(L\) is the set of labels or attributes such as risk, latency, and test coverage.

Entities include:
- Goal
- Task
- Module
- Feature
- Failure
- Fix
- Test
- Skill
- Version
- Achievement

### 3.3 Execution-Driven Learning

After execution, the system stores outcomes in a **Causal Experience Graph (CEG)**. The CEG records:
- the cause of failure,
- the impacted entities,
- the fix applied,
- and the resulting stable state.

This converts repeated debugging from ad hoc trial-and-error into a reusable engineering memory.

### 3.4 Role Simulation as Objective Functions

Traditional SDLC roles are represented as scoring functions rather than human-like agents. For example:
- Product perspective scores usefulness and goal alignment.
- UX perspective scores friction and cognitive load.
- Security perspective scores vulnerability risk.
- QA perspective scores coverage and regression sensitivity.

The system uses these scores to evaluate a candidate change before execution.

---

## 4. Method Overview

Given a current graph state \(G_t\) and a proposed change \(\Delta\), the system performs the following steps:

1. Construct or update the dependency graph.
2. Identify the impacted subgraph.
3. Predict failure risk and dependency propagation.
4. Reject unsafe changes via hard constraints.
5. Rank remaining candidates using an optimization rule.
6. Execute the selected candidate in a sandbox.
7. Store the outcome in the CEG.
8. Reuse the stored pattern for future tasks.

The prototype is intentionally minimal and meant to answer one question:

> Does graph-aware pre-execution filtering reduce regressions and repeated failures compared to a reactive LLM coding loop?

---

## 5. Research Positioning

ECAE should be understood as a synthesis of existing research areas rather than a replacement for them.

### 5.1 Related Research Fields

| System Concept | Related Field |
|---|---|
| Entity graph modeling | Graph-based program analysis |
| Dependency propagation | Causal inference |
| Candidate selection under constraints | Multi-objective optimization |
| Attack/defense evaluation | Safety games / adversarial ML |
| State evolution | Control theory / MDPs |
| Code generation from structured context | Program synthesis |
| Verification of software state | Model checking / formal methods |
| Failure reuse | Memory-based learning / hierarchical RL |

### 5.2 Novelty Position

The novelty of ECAE is not a new theorem. The novelty is the **integration** of:
- entity-centric state modeling,
- predictive dependency reasoning,
- adversarial validation,
- and execution-grounded learning

into a single development loop for AI-assisted coding.

---

## 6. Evaluation Plan

The prototype should be evaluated on small but realistic tasks, such as:
- function renaming,
- API schema changes,
- webhook updates,
- frontend state modifications,
- authentication-related refactors.

### Metrics
- Regression rate
- Iteration count
- Failure repetition rate
- Causal prediction accuracy
- Token usage
- False completion rate

### Baseline
Compare against a standard reactive coding agent:

**Generate → Execute → Fail → Fix**

### Proposed Method

**Predict → Filter → Optimize → Generate → Execute → Learn**

---

## 7. Discussion

This framework is particularly relevant for high-stakes software domains where regressions are expensive, such as payments, infrastructure, and safety-critical systems. In such settings, a small dependency mistake can produce significant downstream cost. The goal of ECAE is not to eliminate all uncertainty, but to reduce repeated trial-and-error by making software state explicit and searchable.

The main risk is overengineering. If the graph becomes too large or the scoring functions become too vague, the system may lose its advantage. For this reason, the prototype should begin with a small codebase and a small set of entity types.

---

## 8. Conclusion

We presented Predictive Entity-Centric Autonomous Engineering (ECAE), a graph-based framework for agentic software development. The proposed approach treats code as a state-space graph of entities, uses pre-execution prediction to filter unsafe changes, and stores failures as first-class knowledge for future reuse.

The system is not intended as a replacement for formal verification or established engineering workflows. Rather, it is a structured proposal for reducing hallucination, repeated mistakes, and unnecessary execution cycles in AI-assisted development.

---

# Appendix A — Formal Mathematical Model

## A.1 Entity Definition

Each entity \(e_i\) is represented as:

\[
e_i = \langle \tau_i, \sigma_i, \vec{m}_i, \mathcal{C}_i \rangle
\]

where:
- \(\tau_i\) is the entity type (Task, Module, Skill, Failure, etc.),
- \(\sigma_i\) is the operational state,
- \(\vec{m}_i \in \mathbb{R}^k\) is a measurable feature vector,
- \(\mathcal{C}_i\) is the set of local constraints.

## A.2 Graph State

The global system state is:

\[
S_t \in \mathcal{S}
\]

and the codebase is represented as:

\[
G_t = (V_t, E_t, L_t)
\]

where \(V_t\) is the entity set at time \(t\).

## A.3 Stochastic Transition Function

A code change \(a_c\) transforms the system according to:

\[
P(S_{t+1} \mid S_t, a_c, z_t)
\]

where \(z_t\) is an external disturbance such as runtime variance or environment noise.

## A.4 Game-Theoretic Formulation

The system is modeled as a stochastic game:

\[
\mathcal{G} = \langle \mathcal{P}, \mathcal{S}, \mathcal{A}, P, R \rangle
\]

where:
- \(\mathcal{P}\) are the players,
- \(\mathcal{S}\) is the state space,
- \(\mathcal{A}\) are action spaces,
- \(P\) is the transition model,
- \(R\) is the reward function.

The equilibrium selection objective is:

\[
U(S^*) = \max_{\pi_c} \min_{\pi_r} \mathbb{E}[U(S_{t+1} \mid S_t, a_c, a_r)]
\]

## A.5 Optimization Modes

### Pareto Optimality
A candidate is Pareto-optimal if no other candidate dominates it across all objectives.

### Weighted Utility Maximization

\[
U(G') = \sum_{i=1}^{n} w_i \cdot \phi_i(G', a)
\]

and the selected action is:

\[
\arg\max_a U(G_{t+1})
\]

### Minimax Robustness

\[
\arg\max_{a_c} \min_{a_r} U(G_{t+1}(a_c, a_r))
\]

## A.6 Feasibility Constraint

Hard constraints are modeled as:

\[
g_j(\Delta) = 0 \quad \forall j
\]

If any constraint is violated, the candidate is rejected.

## A.7 Convergence Condition

A stable solution is reached when:

1. all feasibility constraints hold, and
2. no admissible action improves the objective significantly.

In discrete form, convergence can be approximated by:

\[
\Delta U(S^*) \le \epsilon
\]

for a small threshold \(\epsilon\).

---

# Appendix B — Prototype Implementation Notes

- Start with a small project.
- Build a graph from function-level dependencies first.
- Use heuristics before machine learning.
- Store only failures, fixes, and reusable patterns.
- Compare against a reactive baseline.
- Do not claim full autonomy until metrics support it.

---

# Appendix C — Suggested Paper Framing

If submitted to a workshop, the paper should be described as:

> A predictive, graph-based, and execution-grounded framework for reducing hallucination and repeated failure in AI-assisted software development.

This framing is accurate, measurable, and avoids overclaiming.
