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
        # Fallback for empty path handling
        parts = ["."]

    subcommand = parts[0]

    # Handle 'init' subcommand
    if subcommand == "init":
        from memory_system.services.workspace_service import init_project
        path = parts[1] if len(parts) > 1 else "."
        try:
            metadata = init_project(path)
            return f"Project initialized successfully at {metadata['project_root']} with profile {metadata['language_profile']}."
        except Exception as e:
            return f"Error initializing project: {e}"

    # Handle 'path' subcommand
    elif subcommand == "path":
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
        from memory_system.services.workspace_service import detect_workspace

        # Determine actual workspace path (handles missing path gracefully)
        workspace_dir = detect_workspace(".")

        task = ""
        if "--task" in parts:
            task_idx = parts.index("--task")
            if task_idx + 1 < len(parts):
                task = parts[task_idx + 1]

        if not task:
            return "Error: Missing --task argument."

        return process_task(task, workspace_dir)

    else:
        return f"Error: Unknown command or subcommand: {subcommand}"

def process_task(task: str, workspace_dir: str = ".") -> str:
    """Wrapper to run the orchestrator synchronously."""
    import asyncio
    from memory_system.agent_engine.orchestrator import AgentOrchestrator
    import logging

    # We want to capture the output, or at least run it cleanly.
    # The simplest way is to run the loop and return the result.
    orchestrator = AgentOrchestrator()

    # Simple synchronous wrapper for the async run loop
    try:
        # The orchestrator method is process_task(task_query, workspace_dir)
        result = orchestrator.process_task(task_query=task, workspace_dir=workspace_dir)
        if result:
            return f"Task completed successfully: {task}"
        else:
            return f"Task failed: {task}"
    except Exception as e:
        return f"Error executing task: {str(e)}"
