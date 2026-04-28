"""Section 5 client: CallToolResult Patterns."""

import asyncio
import json
import os
import sys

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


async def run():
    # --- TRANSPORT: uncomment one line ---
    # STDIO — server launched as subprocess, run client only:
    async with stdio_client(server_params) as (read, write):
    # ↕ TOGGLE
    # HTTP — start server separately first (mcp.run transport="streamable-http"), then run client:
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools — full response written to tools_response.json
            tools = await session.list_tools()
            with open(os.path.join(_here, "tools_response.json"), "w") as f:
                json.dump(tools.model_dump(), f, indent=2, default=str)
            print("\n=== outputSchema presence per tool ===")
            for tool in tools.tools:
                has_schema = tool.outputSchema is not None
                print(f"  {tool.name}: {'outputSchema: present' if has_schema else 'outputSchema: null'}")
            print("-" * 50)

            # --- Invocation 1: check_pantry (error) ---
            # Tool (error): check result.isError before reading content
            print("\n" + "=" * 50)
            print("INVOCATION 1: check_pantry (isError=True)")
            print("=" * 50)
            result = await session.call_tool("check_pantry", arguments={"ingredient": "truffle oil"})
            print(f"[raw result] {result}")
            print("-" * 50)
            if result.isError:
                for content in result.content:
                    if isinstance(content, types.TextContent):
                        print(f"[error] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 2: check_pantry (success) ---
            print("\n" + "=" * 50)
            print("INVOCATION 2: check_pantry (isError=False)")
            print("=" * 50)
            result = await session.call_tool("check_pantry", arguments={"ingredient": "eggs"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[success] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 3: get_recipe_card ---
            # Tool (embedded resource): EmbeddedResource bundles URI + mimeType + data in the response
            print("\n" + "=" * 50)
            print("INVOCATION 3: get_recipe_card")
            print("=" * 50)
            result = await session.call_tool("get_recipe_card", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.EmbeddedResource):
                    resource = content.resource
                    if isinstance(resource, types.TextResourceContents):
                        print(f"[embedded resource] {resource.uri} ({resource.mimeType}): {resource.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 4: generate_serving_chart ---
            # Tool (image - CallToolResult): parse ImageContent from content list
            print("\n" + "=" * 50)
            print("INVOCATION 4: generate_serving_chart")
            print("=" * 50)
            result = await session.call_tool("generate_serving_chart", arguments={"servings": 4})
            for content in result.content:
                if isinstance(content, types.ImageContent):
                    print(f"[image - CallToolResult] mimeType={content.mimeType}, size={len(content.data)} bytes")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 5: create_recipe_label ---
            # Tool (image - FastMCP Image): identical wire format, simpler server-side API
            print("\n" + "=" * 50)
            print("INVOCATION 5: create_recipe_label")
            print("=" * 50)
            result = await session.call_tool("create_recipe_label", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.ImageContent):
                    print(f"[image - FastMCP Image] mimeType={content.mimeType}, size={len(content.data)} bytes")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 6: get_dish_info ---
            # Tool (CallToolResult + _meta): result.meta surfaces _meta at the client layer
            print("\n" + "=" * 50)
            print("INVOCATION 6: get_dish_info")
            print("=" * 50)
            result = await session.call_tool("get_dish_info", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[_meta] description: {content.text}")
            if result.meta:
                print(f"[_meta] client-only metadata: {result.meta}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 7: clear_added_dishes ---
            # Tool (empty CallToolResult): content=[] signals acknowledgment with no data
            print("\n" + "=" * 50)
            print("INVOCATION 7: clear_added_dishes")
            print("=" * 50)
            result = await session.call_tool("clear_added_dishes")
            print(f"[raw result] {result}")
            print("-" * 50)
            print(f"[empty CallToolResult] content={result.content}, isError={result.isError}")
            print(f"[structuredContent] {result.structuredContent}")

            # --- Invocation 8: get_validated_macros ---
            # Tool (Annotated[CallToolResult, Model]): read both TextContent and validated structuredContent
            print("\n" + "=" * 50)
            print("INVOCATION 8: get_validated_macros")
            print("=" * 50)
            result = await session.call_tool("get_validated_macros", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[annotated CallToolResult] {content.text}")
            if result.structuredContent:
                m = result.structuredContent
                print(f"[annotated CallToolResult] validated: dish={m.get('dish')}, dominant={m.get('dominant_macro')}, score={m.get('balance_score')}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
