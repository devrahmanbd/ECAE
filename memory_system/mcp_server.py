import asyncio
import sys
import os
import warnings

# Ensure the root project directory is in the python path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings("ignore")

# Suppress HuggingFace hub warnings from polluting stdout (which breaks MCP stdio)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

try:
    import tqdm
    import tqdm.auto
    orig_init = tqdm.tqdm.__init__
    def custom_tqdm_init(self, *args, **kwargs):
        kwargs['file'] = sys.stderr
        orig_init(self, *args, **kwargs)
    tqdm.tqdm.__init__ = custom_tqdm_init
except ImportError:
    pass

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from memory_system.services.memory_service import search_memory, store_memory
from memory_system.services.graph_service import get_graph_context
from memory_system.services.execution_service import run_in_docker
from memory_system.models.schemas import MemoryMetadata
from memory_system.services.workspace_service import detect_workspace, init_project
from memory_system.db.qdrant_client import init_collection

# The server wrapper representing the Agent
server = Server("memory-system-agent")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ecae_cli",
            description="Process a raw /ecae CLI command (e.g. '/ecae . --task \"fix bug\"' or '/ecae explain \"node\"').",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The full /ecae command string"}
                },
                "required": ["command"]
            }
        ),
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
            name="assemble_evidence",
            description="Retrieve a rich evidence packet mapping relevant memories, prior traces, critiques, and dynamic graph structures for planning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The target task"}
                },
                "required": ["task"]
            }
        ),
        types.Tool(
            name="resolve_workspace",
            description="Phase 8 Tool: Resolve the dynamic workspace path based on repository root configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        types.Tool(
            name="retrieve_episodes",
            description="Phase 8 Tool: Retrieve targeted historical episode records for deeper reasoning constraints.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The target task to find episodes for"}
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
                    "query": {"type": "string", "description": "A single target entity or a space-separated list or JSON array of target entities to analyze (e.g. 'main.py filter_duplicate.py')"},
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
            arguments=[]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> types.GetPromptResult:
    if name == "agent_rules":
        return types.GetPromptResult(
            description="System rules for IDE integration.",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="You are an ECAE-lite agent. You MUST follow these rules strictly:\n"
                             "1. Call search_memory FIRST to retrieve prior decisions and failure patterns.\n"
                             "2. Call get_graph_context SECOND to check structural impact before coding.\n"
                             "3. Call execute_command to validate your work before declaring completion.\n"
                             "4. Summarize your plan, graph risk, affected files, and validation result clearly to the user.\n"
                             "5. If the user provides an /ecae command, use the ecae_cli tool to execute it directly and return the result."
                    )
                )
            ]
        )
    raise ValueError(f"Prompt not found: {name}")

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "ecae_cli":
            from memory_system.cli_parser import parse_and_route_ecae_command
            res_str = parse_and_route_ecae_command(arguments["command"])
            return [types.TextContent(type="text", text=res_str)]

        elif name == "search_memory":
            results = search_memory(arguments["query"])
            res_str = "\n".join([f"ID: {r.id}, Text: {r.text}, Score: {r.score}" for r in results])
            return [types.TextContent(type="text", text=res_str if res_str else "No memories found.")]

        elif name == "assemble_evidence":
            from memory_system.services.memory_service import assemble_evidence
            resolved_root = detect_workspace(".")
            evidence = assemble_evidence(arguments["task"], workspace_dir=resolved_root)
            return [types.TextContent(type="text", text=evidence.model_dump_json())]

        elif name == "resolve_workspace":
            resolved_root = detect_workspace(".")
            return [types.TextContent(type="text", text=resolved_root)]

        elif name == "retrieve_episodes":
            # Native retrieval of exclusively parsed episode records utilizing our semantic filter
            results = search_memory(arguments["query"], limit=10)
            episodes = [r.metadata.episode_data for r in results if r.metadata and hasattr(r.metadata, "episode_data") and r.metadata.episode_data]
            return [types.TextContent(type="text", text=json.dumps(episodes))]

        elif name == "get_graph_context":
            resolved_root = detect_workspace(arguments.get("root_dir", "."))
            ctx = get_graph_context(arguments["query"], root_dir=resolved_root)
            return [types.TextContent(type="text", text=ctx.model_dump_json())]
            
        elif name == "store_memory":
            meta_dict = arguments.get("metadata", {})
            meta = MemoryMetadata(**meta_dict) if meta_dict else None
            result = store_memory(arguments["text"], metadata=meta)
            return [types.TextContent(type="text", text=f"Stored memory: {result.id if result else 'Duplicate'}")]
        
        elif name == "execute_command":
            resolved_workspace = detect_workspace(arguments.get("workspace_dir", "."))
            volumes = {os.path.abspath(resolved_workspace): "/app"}
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
    # Detect workspace and ensure graph is initialized before serving
    workspace_dir = detect_workspace(".")
    try:
        init_collection()
        init_project(workspace_dir)
        logging.info(f"Initialized workspace at {workspace_dir}")
    except Exception as e:
        logging.error(f"Failed to initialize workspace: {e}")

    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
