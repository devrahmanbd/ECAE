# Workflow: ecae

**Command:** /ecae
**Description:** Autonomous project intelligence system that builds a graph, maintains memory, and executes a Predict → Filter → Optimize → Generate → Execute → Learn loop across any workspace

---

## Entry Behavior

If no path argument is provided, default to:

```
.
```

The system MUST automatically detect the workspace root before any other step.

---

## Steps

Follow the ECAE execution protocol defined in the core skill system:

### 1) Workspace Detection

* Identify project root
* Validate supported project structure
* Abort if workspace is invalid

---

### 2) Graph Initialization / Refresh

* If graph does not exist:

  * build initial graph from workspace
* If graph exists:

  * refresh incrementally

Graph output location:

```
graphify-out/graph.json (or ECAE equivalent dynamic graph store)
```

---

### 3) Memory Load

* Load relevant historical memory:

  * prior failures
  * prior successful fixes
  * similar tasks

Tooling:

* search_memory
* get_relevant_memory

---

### 4) Predict Phase

* Use graph + memory to generate candidate actions
* Identify impacted nodes and dependencies

Output:

* candidate plan set

---

### 5) Filter Phase

* Remove unsafe or invalid candidates
* Reject actions violating:

  * dependency constraints
  * execution policies
  * workspace rules

---

### 6) Optimize Phase

* Rank remaining candidates by:

  * success probability
  * graph centrality impact
  * memory similarity to past success

---

### 7) Generate Phase

* Produce concrete implementation steps
* Must be executable in sandbox
* Must reference real files from graph

---

### 8) Execute Phase

* Run in sandbox environment
* Capture:

  * stdout
  * stderr
  * exit code

Tool:

* execute_command

---

### 9) Observe Result

* Classify outcome:

  * success
  * failure

---

### 10) Learn Phase

* Store result in memory:

  * success → reinforcement memory
  * failure → corrective memory

Tool:

* store_memory

---

### 11) Loop Decision

* If failure and retries allowed:

  * return to Predict phase
* If success or stop condition met:

  * terminate workflow

---

## System Constraints

* No execution without workspace detection
* No memory-only reasoning without graph context
* No graph modification without execution feedback
* No success claim without sandbox proof

---

## Stop Conditions

Workflow must stop if:

* workspace cannot be resolved
* graph cannot be built or loaded
* execution sandbox is unavailable
* memory layer is unreachable

---

## Final Principle

**Graph de
