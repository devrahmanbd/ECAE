import httpx
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# The base URL of our FastAPI server
BASE_URL = "http://localhost:8000"

server = Server("memory-system")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_memory",
            description="Retrieve relevant project context and past decisions using semantic search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query (e.g., 'auth pattern')"}
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
                    "metadata": {"type": "object", "description": "Optional metadata (e.g., {'project': 'agent'})"}
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="execute_command",
            description="Execute a shell command in a sandboxed environment for testing and verification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run"},
                    "workdir": {"type": "string", "description": "Optional working directory", "default": "."}
                },
                "required": ["command"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "search_memory":
                resp = await client.get(f"{BASE_URL}/memory/search", params={"query": arguments["query"]})
                return [types.TextContent(type="text", text=resp.text)]
            
            elif name == "store_memory":
                resp = await client.post(f"{BASE_URL}/memory/store", json={
                    "text": arguments["text"],
                    "metadata": arguments.get("metadata", {})
                })
                return [types.TextContent(type="text", text=resp.text)]
            
            elif name == "execute_command":
                resp = await client.post(f"{BASE_URL}/execute", json={
                    "command": arguments["command"],
                    "workdir": arguments.get("workdir", ".")
                })
                return [types.TextContent(type="text", text=resp.text)]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error connecting to memory API: {str(e)}")]

async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
