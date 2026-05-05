import shlex
import sys
import json
import os
from typing import Dict, Any

def parse_and_route_ecae_command(command_str: str) -> str:
    """Parses an /ecae command string and routes it to the corresponding logic."""
    if not command_str.startswith("/ecae"):
        return "Error: Command must start with /ecae"

    # Remove the /ecae prefix
    command_str = command_str[5:].strip()

    if not command_str:
        return "Error: Missing command body."

    try:
        parts = shlex.split(command_str)
    except ValueError as e:
        return f"Error parsing command: {e}"

    if not parts:
        return "Error: Empty command."

    subcommand = parts[0]

    # Handle 'path' subcommand
    if subcommand == "path":
        if len(parts) < 3:
            return "Error: Missing nodes for path command. Usage: /ecae path <node_a> <node_b>"
        node_a = parts[1]
        node_b = parts[2]

        from memory_system.services.graph_service import trace_graph_path
        path = trace_graph_path(node_a, node_b)
        if path:
            return " -> ".join(path)
        else:
            return f"No path found between {node_a} and {node_b}"

    # Handle 'explain' subcommand
    elif subcommand == "explain":
        if len(parts) < 2:
            return "Error: Missing node for explain command. Usage: /ecae explain <node>"
        node = parts[1]

        from memory_system.services.graph_service import explain_graph_node
        explanation = explain_graph_node(node)
        return json.dumps(explanation, indent=2)

    # Handle the full orchestrator task (e.g., /ecae . --task "Implement X")
    elif subcommand == ".":
        task = ""
        if "--task" in parts:
            task_idx = parts.index("--task")
            if task_idx + 1 < len(parts):
                task = parts[task_idx + 1]

        if not task:
            return "Error: Missing --task argument."

        return process_task(task)

    else:
        return f"Error: Unknown command or subcommand: {subcommand}"

def process_task(task: str) -> str:
    """Wrapper to run the orchestrator synchronously."""
    import asyncio
    from memory_system.agent_engine.orchestrator import AgentOrchestrator
    import logging

    # We want to capture the output, or at least run it cleanly.
    # The simplest way is to run the loop and return the result.
    orchestrator = AgentOrchestrator(workspace_dir=".")

    # Simple synchronous wrapper for the async run loop
    try:
        # In python 3.10+ we might be able to use asyncio.run
        # But wait, orchestrator.run() is NOT async in our implementation!
        result = orchestrator.run(task)
        if result:
            return f"Task completed successfully: {task}"
        else:
            return f"Task failed: {task}"
    except Exception as e:
        return f"Error executing task: {str(e)}"
