import shlex
import os
import json
from typing import Dict, Any, List

from memory_system.agent_engine.orchestrator import AgentOrchestrator
from memory_system.services.graph_service import get_graph_context, trace_graph_path, explain_graph_node
from memory_system.services.memory_service import search_memory
from memory_system.services.execution_service import execute_command
from memory_system.core.logger import logger

def parse_and_route_ecae_command(command_str: str) -> str:
    """
    Parses a /ecae command from the Antigravity assistant and routes it.
    """
    if not command_str.startswith("/ecae"):
        return "Error: Command must start with /ecae"

    # Remove the /ecae prefix
    cmd = command_str[5:].strip()

    try:
        parts = shlex.split(cmd)
    except Exception as e:
        return f"Error parsing command: {str(e)}"

    if not parts:
        return "Error: Missing arguments for /ecae command."

    # Check for subcommands
    subcommand = parts[0]

    if subcommand == "query":
        if len(parts) < 2:
            return "Error: Missing query string. Usage: /ecae query \"<question>\""
        query = parts[1]

        # Answer using graph + memory, with tool evidence
        graph_res = get_graph_context(query)
        memory_res = search_memory(query)

        mem_str = "\n".join([f"- {m.text} (Score: {m.score})" for m in memory_res])
        graph_str = graph_res.model_dump_json(indent=2)

        return f"Query: {query}\n\n=== Graph Evidence ===\n{graph_str}\n\n=== Memory Evidence ===\n{mem_str}"

    elif subcommand == "path":
        if len(parts) < 3:
            return "Error: Missing nodes. Usage: /ecae path \"<a>\" \"<b>\""
        node_a = parts[1]
        node_b = parts[2]

        path = trace_graph_path(node_a, node_b)
        if not path:
            return f"No path found between {node_a} and {node_b}."
        return f"Path found: {' -> '.join(path)}"

    elif subcommand == "explain":
        if len(parts) < 2:
            return "Error: Missing node. Usage: /ecae explain \"<node>\""
        node = parts[1]

        explanation = explain_graph_node(node)
        return json.dumps(explanation, indent=2)

    # If not a subcommand, assume it's a project path + flags
    path = parts[0]
    if not os.path.exists(path) and path != ".":
        logger.warning(f"Path '{path}' not found. Defaulting to '.'")
        path = "."

    flags = parts[1:]

    # Parse flags
    task = "Analyze project directory and run ECAE loop"
    force_graph = False
    force_memory = False
    force_execute = False
    deep_inspect = False
    update_refresh = False

    i = 0
    while i < len(flags):
        flag = flags[i]
        if flag == "--task":
            if i + 1 < len(flags):
                task = flags[i+1]
                i += 1
        elif flag == "--graph":
            force_graph = True
        elif flag == "--memory":
            force_memory = True
        elif flag == "--execute":
            force_execute = True
        elif flag == "--deep":
            deep_inspect = True
        elif flag == "--update":
            update_refresh = True
        i += 1

    # Logic routing based on flags
    # Since this is a prototype, we'll map these flags to orchestrator behaviors or manual tool calls

    if force_graph and not force_memory and not force_execute and "--task" not in command_str:
        # Just run graph inspection
        res = get_graph_context("all", root_dir=path)
        return res.model_dump_json(indent=2)

    if force_memory and not force_graph and not force_execute and "--task" not in command_str:
        # Just run memory retrieval
        res = search_memory("recent failures")
        return "\n".join([f"- {m.text}" for m in res])

    if force_execute and not force_graph and not force_memory and "--task" not in command_str:
        # Just run a simple execution validation
        res = execute_command("pytest", workdir=path)
        return res.model_dump_json(indent=2)

    # Run the full ECAE loop on the task
    orchestrator = AgentOrchestrator()
    result = orchestrator.process_task(task, workspace_dir=path)

    return json.dumps(result, indent=2)
