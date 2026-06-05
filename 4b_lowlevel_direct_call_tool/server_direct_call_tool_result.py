"""Low-level MCP server: direct CallToolResult return (stdio transport).

Demonstrates returning types.CallToolResult directly from @server.call_tool()
with explicit control over all three layers:

  content           — list[TextContent | ImageContent | ...] visible to the model
  structuredContent — dict of machine-readable data for the client application
  _meta             — arbitrary metadata passed through to the client as result.meta

The only real low-level distinction: one function handles every tool call.
You write the if/elif routing yourself — FastMCP does this automatically.
"""

import asyncio
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("direct-call-tool-result-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Declare the tool with its input schema."""
    return [
        types.Tool(
            name="advanced_tool",
            description="Tool with full control including structuredContent and _meta",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> types.CallToolResult:
    """Return CallToolResult directly — all three layers are set explicitly."""
    if name == "advanced_tool":
        message = str(arguments.get("message", ""))
        return types.CallToolResult(
            content=[
                types.TextContent(type="text", text=f"Processed: {message}")
            ],
            structuredContent={"result": "success", "message": message},
            _meta={"hidden": "data for client applications only"},
        )

    raise ValueError(f"Unknown tool: {name}")


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="direct-call-tool-result-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
