"""Client for the interactive task server (server_task_interactive.py).

Extends the simple-task pattern with elicitation and sampling inside background tasks.
Registers elicitation_callback and sampling_callback on ClientSession. When the task
pauses at input_required, get_task_result() triggers delivery to the callbacks.

    python 7b_lowlevel_task_interactive/client_task_interactive.py
"""

import asyncio
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.context import RequestContext
from mcp.types import (
    CallToolResult,
    CreateMessageRequestParams,
    CreateMessageResult,
    ElicitRequestParams,
    ElicitResult,
    TextContent,
)


async def elicitation_callback(
    context: RequestContext[ClientSession, Any],
    params: ElicitRequestParams,
) -> ElicitResult:
    """Handle elicitation requests from the server."""
    print(f"\n[Elicitation] Server asks: {params.message}")
    response = input("Your response (y/n): ").strip().lower()
    confirmed = response in ("y", "yes", "true", "1")
    print(f"[Elicitation] Responding with: confirm={confirmed}")
    return ElicitResult(action="accept", content={"confirm": confirmed})


async def sampling_callback(
    context: RequestContext[ClientSession, Any],
    params: CreateMessageRequestParams,
) -> CreateMessageResult:
    """Handle sampling requests from the server (hardcoded — replace with real LLM)."""
    prompt = "unknown"
    if params.messages:
        content = params.messages[0].content
        if isinstance(content, TextContent):
            prompt = content.text

    print(f"\n[Sampling] Server requests LLM completion for: {prompt}")

    haiku = "Cherry blossoms fall\nSoftly on the quiet pond\nSpring whispers goodbye"
    print("[Sampling] Responding with hardcoded haiku")
    return CreateMessageResult(
        model="mock-haiku-model",
        role="assistant",
        content=TextContent(type="text", text=haiku),
    )


def get_text(result: CallToolResult) -> str:
    if result.content and isinstance(result.content[0], TextContent):
        return result.content[0].text
    return "(no text)"


async def run() -> None:
    async with streamable_http_client("http://localhost:8000/mcp/") as (read, write, _):
        async with ClientSession(
            read,
            write,
            elicitation_callback=elicitation_callback,
            sampling_callback=sampling_callback,
        ) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # ----------------------------------------------------------------
            # Demo 1: Elicitation inside a task
            # ----------------------------------------------------------------
            print("\n--- Demo 1: Elicitation ---")
            elicit_task = await session.experimental.call_tool_as_task(
                "confirm_delete", {"filename": "important.txt"}
            )
            elicit_task_id = elicit_task.task.taskId
            print(f"Task created: {elicit_task_id}")

            async for status in session.experimental.poll_task(elicit_task_id):
                print(f"[Poll] Status: {status.status}")
                if status.status == "input_required":
                    # get_task_result triggers delivery of the elicitation request
                    elicit_result = await session.experimental.get_task_result(
                        elicit_task_id, CallToolResult
                    )
                    break
            else:
                elicit_result = await session.experimental.get_task_result(
                    elicit_task_id, CallToolResult
                )

            print(f"Result: {get_text(elicit_result)}")

            # ----------------------------------------------------------------
            # Demo 2: Sampling inside a task
            # ----------------------------------------------------------------
            print("\n--- Demo 2: Sampling ---")
            sampling_task = await session.experimental.call_tool_as_task(
                "write_haiku", {"topic": "autumn leaves"}
            )
            sampling_task_id = sampling_task.task.taskId
            print(f"Task created: {sampling_task_id}")

            async for status in session.experimental.poll_task(sampling_task_id):
                print(f"[Poll] Status: {status.status}")
                if status.status == "input_required":
                    sampling_result = await session.experimental.get_task_result(
                        sampling_task_id, CallToolResult
                    )
                    break
            else:
                sampling_result = await session.experimental.get_task_result(
                    sampling_task_id, CallToolResult
                )

            print(f"Result:\n{get_text(sampling_result)}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
