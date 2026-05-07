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

Follow the ECAE execution protocol defined in the core skill system exactly in this deterministic order:

- detect workspace
- resolve graph
- query memory
- choose candidate
- execute in sandbox
- store result
- repeat or stop

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

## End State

- Predict
- Filter
- Optimize
- Generate
- Execute
- Read result
- Learn from success and failure
- Repeat until stop condition

Do not answer from memory alone. Do not answer from graph alone. Do not answer from execution alone. Use the required tool for the required layer.
