"""Section 6 client: Async + Context.

Two mechanisms needed to receive server-side context notifications:

1. logging_callback on ClientSession — captures ctx.info / ctx.warning / ctx.debug / ctx.error.
   These are sent as LoggingMessageNotification (notifications/message) with .level and .data fields.

2. progress_callback on call_tool — captures ctx.report_progress().
   Signature: (progress: float, total: float | None, message: str | None) -> None.

Neither appears in result.content — they are protocol-level push notifications, not tool result data.
"""

import asyncio
import json
import os
import sys

from pydantic import AnyUrl

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_here = os.path.dirname(os.path.abspath(__file__))
_venv_root = os.path.dirname(os.path.dirname(_here))
_python = os.path.join(
    _venv_root, ".venv",
    "Scripts" if sys.platform == "win32" else "bin",
    "python.exe" if sys.platform == "win32" else "python",
)
server_params = StdioServerParameters(
    command=_python,
    args=[os.path.join(_here, "server.py")],
)


async def _logging_callback(params: types.LoggingMessageNotificationParams) -> None:
    print(f"[ctx.{params.level}] {params.data}")


async def _progress_callback(progress: float, total: float | None, message: str | None) -> None:
    print(f"[ctx.report_progress] {progress}/{total} - {message}")


async def run():
    # --- TRANSPORT: uncomment one line ---
    # STDIO — server launched as subprocess, run client only:
    async with stdio_client(server_params) as (read, write):
    # ↕ TOGGLE
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write, logging_callback=_logging_callback) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(json.dumps(tools.model_dump(), indent=2, default=str))
            print("-" * 50)

            # --- Invocation 1: generate_shopping_list (error) ---
            # Tool (progress): ctx.error — empty list triggers error log and early return
            print("\n" + "=" * 50)
            print("INVOCATION 1: generate_shopping_list (empty list → ctx.error)")
            print("=" * 50)
            result = await session.call_tool(
                "generate_shopping_list",
                arguments={"dishes": []},
                progress_callback=_progress_callback,
            )
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[progress - error] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 2: generate_shopping_list (with dishes) ---
            # Tool (progress): ctx.warning — "soup" is unknown, triggers warning; known dishes proceed
            print("\n" + "=" * 50)
            print("INVOCATION 2: generate_shopping_list (with dishes → ctx.warning for unknown)")
            print("=" * 50)
            result = await session.call_tool(
                "generate_shopping_list",
                arguments={"dishes": ["pancakes", "omelette", "pasta", "soup"]},
                progress_callback=_progress_callback,
            )
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[progress] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 3: add_dish ---
            # Tool (notification): add_dish fires send_resource_list_changed
            print("\n" + "=" * 50)
            print("INVOCATION 3: add_dish (fires send_resource_list_changed)")
            print("=" * 50)
            result = await session.call_tool(
                "add_dish",
                arguments={
                    "dish": "risotto",
                    "ingredients": "arborio rice, parmesan, butter, onion, white wine, stock",
                },
            )
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[notification] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # Re-read the dynamic resource to confirm recipe://risotto is now available
            risotto_content = await session.read_resource(AnyUrl("recipe://risotto"))
            content_block = risotto_content.contents[0]
            if isinstance(content_block, types.TextResourceContents):
                print(f"[new resource] {content_block.uri}: {content_block.text}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
