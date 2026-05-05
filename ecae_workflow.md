# ECAE Dynamic Workflow

## Initialization & Discovery
- Always detect the local workspace.
- The `ecae` launcher dynamically injects paths to bypass fixed `graph.json` traps.
- Antigravity queries via MCP endpoints utilizing `types.PromptMessage` mappings correctly.

## Execution Rules
- Never use a mock if real docker can be spun up.
- Report all failure statuses clearly up to the orchestration agent.
- Halt execution and error gracefully if Graph, Memory, or Execution layers are unavailable.
