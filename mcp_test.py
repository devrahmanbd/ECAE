import mcp.types as types
from mcp.server import Server

server = Server("test")

@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> types.GetPromptResult:
    pass

print("OK")
