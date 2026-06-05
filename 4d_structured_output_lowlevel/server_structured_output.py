"""Low-level MCP server: outputSchema + server-side validation (stdio transport).

Demonstrates two low-level capabilities FastMCP does not expose:

  outputSchema on types.Tool — declares the shape of the result in list_tools,
                               visible to the client before calling the tool
  Plain-dict return          — return a dict from call_tool; the server validates
                               it against outputSchema and wraps it into TextContent

Contrast with server_direct_call_tool_result.py:
  here  — handler returns a plain dict        (server validates + wraps)
  there — handler returns types.CallToolResult (you build every layer)
"""

import asyncio
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("structured-output-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Declare the tool with both inputSchema and outputSchema."""
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "description": "Temperature in Celsius",
                    },
                    "condition": {
                        "type": "string",
                        "description": "Weather condition",
                    },
                    "humidity": {
                        "type": "number",
                        "description": "Humidity percentage",
                    },
                    "city": {
                        "type": "string",
                        "description": "City name",
                    },
                },
                "required": ["temperature", "condition", "humidity", "city"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Return a plain dict — the server validates it against outputSchema
    and serialises it into a TextContent block for backward compatibility."""
    if name == "get_weather":
        city = arguments["city"]
        return {
            "temperature": 22.5,
            "condition": "partly cloudy",
            "humidity": 65,
            "city": city,
        }

    raise ValueError(f"Unknown tool: {name}")


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="structured-output-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
