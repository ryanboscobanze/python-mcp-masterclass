"""Section 1 client: Simple Tools."""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.metadata_utils import get_display_name

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


async def run():
    # --- TRANSPORT: uncomment one line ---
    # STDIO — server launched as subprocess, run client only:
    async with stdio_client(server_params) as (read, write):
    # HTTP — start server separately first (mcp.run transport="streamable-http"), then run client:
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools: show get_display_name() with and without title
            # - WITHOUT title → falls back to function name
            # - WITH title    → returns the human-readable title
            tools = await session.list_tools()
            with open(os.path.join(_here, "tools_response.json"), "w") as f:
                json.dump(tools.model_dump(), f, indent=2, default=str)
            print("=== Tools (get_display_name behavior) ===")
            for tool in tools.tools:
                print(f"  name={tool.name!r:30} title={str(tool.title)!r:30} → display={get_display_name(tool)!r}")

            # --- Invocation 1: double_servings ---
            # Tool (text): double_servings returns int → TextContent on the wire
            print("\n" + "=" * 50)
            print("INVOCATION 1: double_servings")
            print("=" * 50)
            result = await session.call_tool("double_servings", arguments={"servings": 4})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] double_servings(4) = {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 2: list_dishes ---
            # Tool (primitive - list[str]): FastMCP returns each item as a separate TextContent
            print("\n" + "=" * 50)
            print("INVOCATION 2: list_dishes")
            print("=" * 50)
            result = await session.call_tool("list_dishes")
            print(f"[raw result] {result}")
            print("-" * 50)
            dishes = []
            for content in result.content:
                if isinstance(content, types.TextContent):
                    dishes.append(content.text)
            print(f"[content - list[str]] available dishes: {dishes}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 3: suggest_wine ---
            # Tool (title): suggest_wine — display name comes from its title
            print("\n" + "=" * 50)
            print("INVOCATION 3: suggest_wine")
            print("=" * 50)
            result = await session.call_tool("suggest_wine", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] pancakes → {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 4: scale_recipe ---
            # Tool (Field descriptions): only dish is required; servings and unit use Field defaults
            print("\n" + "=" * 50)
            print("INVOCATION 4: scale_recipe")
            print("=" * 50)
            result = await session.call_tool("scale_recipe", arguments={"dish": "pasta"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
