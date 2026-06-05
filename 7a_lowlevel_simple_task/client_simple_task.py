"""Client for the simple-task server (server_simple_task.py).

Calls the tool as a background task, polls for status updates, then retrieves
the final result. Three separate calls: call_tool_as_task → poll_task → get_task_result.

    python 7a_lowlevel_simple_task/client_simple_task.py
"""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent


async def run() -> None:
    async with streamable_http_client("http://localhost:8000/mcp/") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            print("\nCalling tool as a task...")
            result = await session.experimental.call_tool_as_task(
                "long_running_task",
                arguments={},
                ttl=60000,
            )
            task_id = result.task.taskId
            print(f"Task created: {task_id}")

            # Poll until done
            async for status in session.experimental.poll_task(task_id):
                print(f"  Status: {status.status} - {status.statusMessage or ''}")

            if status.status != "completed":
                print(f"Task ended with status: {status.status}")
                return

            # Retrieve final result
            task_result = await session.experimental.get_task_result(task_id, CallToolResult)
            content = task_result.content[0]
            if isinstance(content, TextContent):
                print(f"\nResult: {content.text}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
