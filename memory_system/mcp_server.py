import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.graph_service import get_graph_context
from memory_system.services.execution_service import run_in_docker
from memory_system.models.schemas import MemoryMetadata

# The server wrapper representing the Agent
server = Server("memory-system-agent")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_memory",
            description="Retrieve relevant project context and past decisions using semantic search. MUST be called first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query (e.g., 'auth pattern')"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_graph_context",
            description="Retrieve structural dependency graph and blast radius. MUST be called second.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The target entity to analyze (e.g. 'core_logic')"},
                    "root_dir": {"type": "string", "description": "The project root dir", "default": "."}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="store_memory",
            description="Store a new memory, decision, or architectural pattern for future agents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The content to remember"},
                    "metadata": {"type": "object", "description": "Optional metadata dictionary"}
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="execute_command",
            description="Execute a shell command in a sandboxed environment for testing and verification. MUST be called before completion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "build_command": {"type": "string", "description": "The build phase command"},
                    "test_command": {"type": "string", "description": "The test phase command"},
                    "image": {"type": "string", "description": "Docker image to use", "default": "python:3.11-slim"}
                },
                "required": ["test_command"]
            }
        )
    ]

@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="agent_rules",
            description="System rules for IDE integration.",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="You are an ECAE-lite agent. You MUST follow these rules strictly:\n1. Call search_memory FIRST to retrieve prior decisions and failure patterns.\n2. Call get_graph_context SECOND to check structural impact before coding.\n3. Call execute_command to validate your work before declaring completion.\n4. Summarize your plan, graph risk, affected files, and validation result clearly to the user."
                    )
                )
            ]
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "search_memory":
            results = search_memory(arguments["query"])
            res_str = "\n".join([f"ID: {r.id}, Text: {r.text}, Score: {r.score}" for r in results])
            return [types.TextContent(type="text", text=res_str if res_str else "No memories found.")]

        elif name == "get_graph_context":
            ctx = get_graph_context(arguments["query"], root_dir=arguments.get("root_dir", "."))
            return [types.TextContent(type="text", text=ctx.model_dump_json())]
            
        elif name == "store_memory":
            meta_dict = arguments.get("metadata", {})
            meta = MemoryMetadata(**meta_dict) if meta_dict else None
            result = store_memory(arguments["text"], metadata=meta)
            return [types.TextContent(type="text", text=f"Stored memory: {result.id if result else 'Duplicate'}")]
        
        elif name == "execute_command":
            volumes = {arguments.get("workspace_dir", "."): "/app"}
            res = run_in_docker(
                image=arguments.get("image", "python:3.11-slim"),
                build_command=arguments.get("build_command", ""),
                test_command=arguments["test_command"],
                volumes=volumes
            )
            return [types.TextContent(type="text", text=res.model_dump_json())]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing tool: {str(e)}")]

async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
