"""Low-level MCP server demonstrating the experimental tasks API (SEP-1686).

The tool runs as a background task: the server returns a task ID immediately,
sends status updates while working, and the client polls for the final result.

    python 7a_lowlevel_simple_task/server_simple_task.py
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import mcp.types as types
import uvicorn
from mcp.server.experimental.task_context import ServerTaskContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount

server = Server("simple-task-server")

# One-line setup — auto-registers task protocol endpoints
server.experimental.enable_tasks()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="long_running_task",
            description="A task that takes a few seconds with status updates",
            inputSchema={"type": "object", "properties": {}},
            execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
        )
    ]


async def handle_long_running_task(arguments: dict[str, Any]) -> types.CreateTaskResult:
    ctx = server.request_context
    ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

    async def work(task: ServerTaskContext) -> types.CallToolResult:
        await task.update_status("Starting work...")
        await anyio.sleep(1)

        await task.update_status("Processing step 1...")
        await anyio.sleep(1)

        await task.update_status("Processing step 2...")
        await anyio.sleep(1)

        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Task completed!")]
        )

    return await ctx.experimental.run_task(work)


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> types.CallToolResult | types.CreateTaskResult:
    if name == "long_running_task":
        return await handle_long_running_task(arguments)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Unknown tool: {name}")],
        isError=True,
    )


# ---------------------------------------------------------------------------
# Starlette app — session_manager.handle_request used directly as ASGI app
# ---------------------------------------------------------------------------

session_manager = StreamableHTTPSessionManager(app=server)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with session_manager.run():
        yield


starlette_app = Starlette(
    routes=[Mount("/mcp", app=session_manager.handle_request)],
    lifespan=lifespan,
)

if __name__ == "__main__":
    print("Starting server on http://localhost:8000/mcp")
    uvicorn.run(starlette_app, host="127.0.0.1", port=8000)
