"""Low-level MCP server: counter with lifespan (stdio transport).

Same counter example as lifespan/counter/server_counter.py, implemented with
mcp.server.lowlevel.Server instead of FastMCP.

Three things differ from the FastMCP variant:
  lifespan context — yields a plain dict instead of a typed dataclass
  tool registration — list_tools and call_tool are two separate handlers
  context access   — server.request_context (module-level) instead of injected ctx
"""

import asyncio
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions


class AppState:
    """Simple state that persists across tool calls."""

    def __init__(self):
        self.counter = 0
        self.startup_time = time.strftime("%H:%M:%S")
        print(f"[STARTUP] AppState initialized at {self.startup_time}", file=sys.stderr)

    def increment(self) -> int:
        self.counter += 1
        return self.counter

    def get_status(self) -> str:
        return f"Counter: {self.counter}, Server started at: {self.startup_time}"

    def cleanup(self):
        print(
            f"[CLEANUP] AppState cleanup. Final counter value: {self.counter}",
            file=sys.stderr,
        )


@asynccontextmanager
async def server_lifespan(_server: Server) -> AsyncIterator[dict[str, Any]]:
    """Manage server startup and shutdown lifecycle."""
    state = AppState()
    try:
        yield {"state": state}
    finally:
        state.cleanup()


server = Server("counter-server-lowlevel", lifespan=server_lifespan)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="increment",
            description="Increment the counter and return the new value.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="status",
            description="Get current server status showing counter and startup time.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    ctx = server.request_context
    state = ctx.lifespan_context["state"]

    if name == "increment":
        count = state.increment()
        return [types.TextContent(type="text", text=f"Counter incremented to: {count}")]

    if name == "status":
        return [types.TextContent(type="text", text=state.get_status())]

    raise ValueError(f"Unknown tool: {name}")


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="counter-server-lowlevel",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
