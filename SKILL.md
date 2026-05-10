---

name: ecae
description: "ECAE-lite autonomous engineering loop - graph context - memory retrieval - sandbox execution - audit trail - strict tool use"
trigger: /ecae
--------------

# /ecae

Use the available tools to make software changes safely and reproducibly.

This skill is not a CLI program. It is a strict workflow for the assistant to follow using the real tools that already exist:

* graph context lookup
* memory search and store
* sandbox execution

The goal is to reduce hallucinated edits, repeated mistakes, and unsafe code changes.

## What this skill is for

Use `/ecae` when the task needs one or more of these:

* understanding what a change will affect
* checking past fixes or failures
* running code or tests in the sandbox
* deciding whether a proposed change is safe
* recording the outcome for future runs

## What the skill does not do

* It does not invent dependencies.
* It does not claim success without execution.
* It does not treat memory as proof.
* It does not assume a real `ecae` shell command exists.
* It does not pretend to enforce sandbox boundaries. The backend already does that.

---

## Usage

```
/ecae init [path]                       # Initialize the workspace graph and memory profiles
/ecae path <node_a> <node_b>            # Trace the graph dependency path between two nodes
/ecae explain <node>                    # Explain the graph metrics for a specific node
/ecae dashboard [task]                  # Run benchmarks comparing ECAE to baseline agents
/ecae evaluate                          # Evaluate learning metrics and release readiness
/ecae . --task "<task_description>"     # Run the ECAE orchestrator on the given task
/ecae help                              # Show this help message
```

*Note: Antigravity has access to the `/ecae` binary to execute workflows locally exactly the same way it executes `/graphify`. You can invoke the binary `./ecae` from the repository root.*

If no path is given, use the current directory `.`.
If the path is a GitHub URL, clone it first using standard git tooling, then continue on the local path.

---

## The real operating order

Always follow this order unless the task clearly does not require one of the steps:

1. **Graph Layer** — understand structure and blast radius.
2. **Memory Layer** — retrieve similar past decisions, failures, and fixes.
3. **Plan** — write a short, concrete plan.
4. **Execution Layer** — run the command or tests in the sandbox.
5. **Validation** — interpret the result.
6. **Write-back** — store the outcome in memory.
7. **Repeat** — only if the task is still unsolved.

---

## What to do when invoked

### Step 0 — Resolve the target path

If the user gave a path, use it.
If not, use `.`.
If the path is wrong or inaccessible, say so clearly and stop.

### Step 1 — Call graph context first

Use the graph tool to inspect the relevant files, modules, or symbols.

Required output:

* which nodes or files are involved
* which ones depend on which
* estimated blast radius
* whether the target was found or not

Rules:

* If a filename is not recognized, do not rename it silently.
* If the graph returns no match, report `not_found`.
* If graph data is missing, say that the graph is unavailable.
* Do not invent edges or dependencies.

### Step 2 — Search memory second

Use memory search for prior fixes, repeated failures, and useful patterns.

Required output:

* relevant memories
* why they matter
* whether they are strong or weak evidence

Rules:

* Memory is context, not proof.
* If memory conflicts with execution, execution wins.
* Keep memory separate from graph facts.

### Step 3 — Build a short plan

Write a compact plan with:

* proposed change
* affected files
* possible risks
* validation command or test

Do not over-explain.
Do not speculate beyond the evidence.

### Step 4 — Execute in the sandbox

Run the build or tests using the execution tool.

Required output:

* command run
* exit status
* stdout/stderr summary
* pass/fail classification

Rules:

* Treat timeout as a failure that needs a smaller or safer command.
* Treat non-zero exit codes as real failures.
* Do not claim success unless the command succeeded.

### Step 5 — Validate the result

If execution passes, check whether it actually proves the task.
If the task still is not solved, loop back with updated graph and memory context.

### Step 6 — Store the outcome

Write a memory entry with:

* problem
* decision
* reason
* outcome
* affected files
* confidence
* next action

Store both success and failure outcomes.

---

## Rules engine

The rules engine decides whether a step is allowed.

### Graph rules

* Graph queries must stay structural.
* File names and symbol names must not be mixed up silently.
* If the graph is empty or missing, stop.

### Memory rules

* Memory may suggest a path, but it cannot prove correctness.
* Do not blend semantic memory with structural graph facts.
* Log when memory influenced the decision.

### Execution rules

* Execution happens only through the sandbox tool.
* No hidden fallback success.
* No unverified completion.
* If execution fails, report failure and retry only with a safer plan.

### Decision rules

* Unsafe candidates are rejected.
* If evidence is weak, say so.
* If the task is ambiguous, stop instead of inventing a fix.

Allowed decision statuses:

* `allow`
* `reject`
* `retry`
* `stop`

---

## Output contract

Every `/ecae` run should end with an audit summary:

* task
* graph result
* memory result
* plan
* execution result
* validation result
* stored memory id
* next action

If a step failed, name the step and the reason.

---

## Honesty rules

* Never invent a dependency.
* Never invent a file that was not found.
* Never invent execution success.
* Never claim autonomy if the loop did not actually run.
* Never pretend the skill is a CLI command.
* Never mix memory evidence with graph evidence.
* Never require manual graph.json edits.

---

## One-line mission statement

**Graph says what can be affected. Memory says what happened before. Execution says what is true. Rules decide what is allowed.**
