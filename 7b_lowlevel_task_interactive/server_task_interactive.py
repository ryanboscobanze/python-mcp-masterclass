"""Low-level MCP server demonstrating elicitation and sampling inside background tasks.

Two tools — confirm_delete and write_haiku — both TASK_REQUIRED. Inside the background
task, task.elicit() pauses for user input and task.create_message() pauses for LLM
output. Both resume when the client calls get_task_result().

    python 7b_lowlevel_task_interactive/server_task_interactive.py
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.types as types
import uvicorn
from mcp.server.experimental.task_context import ServerTaskContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount

server = Server("simple-task-interactive")
server.experimental.enable_tasks()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="confirm_delete",
            description="Asks for confirmation before deleting (demonstrates elicitation in a task)",
            inputSchema={
                "type": "object",
                "properties": {"filename": {"type": "string"}},
            },
            execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
        ),
        types.Tool(
            name="write_haiku",
            description="Asks LLM to write a haiku (demonstrates sampling in a task)",
            inputSchema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
            },
            execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
        ),
    ]


async def handle_confirm_delete(arguments: dict[str, Any]) -> types.CreateTaskResult:
    ctx = server.request_context
    ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

    filename = arguments.get("filename", "unknown.txt")

    async def work(task: ServerTaskContext) -> types.CallToolResult:
        # task.elicit() — elicitation queued through the task context
        result = await task.elicit(
            message=f"Are you sure you want to delete '{filename}'?",
            requestedSchema={
                "type": "object",
                "properties": {"confirm": {"type": "boolean"}},
                "required": ["confirm"],
            },
        )

        if result.action == "accept" and result.content:
            confirmed = result.content.get("confirm", False)
            text = f"Deleted '{filename}'" if confirmed else "Deletion cancelled"
        else:
            text = "Deletion cancelled"

        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])

    return await ctx.experimental.run_task(work)


async def handle_write_haiku(arguments: dict[str, Any]) -> types.CreateTaskResult:
    ctx = server.request_context
    ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

    topic = arguments.get("topic", "nature")

    async def work(task: ServerTaskContext) -> types.CallToolResult:
        # task.create_message() — sampling queued through the task context
        result = await task.create_message(
            messages=[
                types.SamplingMessage(
                    role="user",
                    content=types.TextContent(
                        type="text", text=f"Write a haiku about {topic}"
                    ),
                )
            ],
            max_tokens=50,
        )

        haiku = result.content.text if isinstance(result.content, types.TextContent) else "No response"
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Haiku:\n{haiku}")]
        )

    return await ctx.experimental.run_task(work)


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> types.CallToolResult | types.CreateTaskResult:
    if name == "confirm_delete":
        return await handle_confirm_delete(arguments)
    elif name == "write_haiku":
        return await handle_write_haiku(arguments)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Unknown tool: {name}")],
        isError=True,
    )


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
