"""Section 4 client: Structured Return Types.

Calls each of the six tools in server.py and prints both layers of the result:
content (the text wire representation) and structuredContent (the typed dict).
Demonstrates which return types produce a usable structuredContent and which
fall back to a memory address string in content with structuredContent=None.
"""

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

            # --- Invocation 1: get_nutrition ---
            # Tool (structured - Pydantic): structuredContent populated from BaseModel schema
            print("\n" + "=" * 50)
            print("INVOCATION 1: get_nutrition")
            print("=" * 50)
            result = await session.call_tool("get_nutrition", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                info = result.structuredContent
                print(f"[structuredContent - Pydantic] {info.get('dish')}: {info.get('calories')} kcal, {info.get('protein_g')}g protein")

            # --- Invocation 2: get_cooking_time ---
            # Tool (structured - TypedDict): structuredContent populated from TypedDict schema
            print("\n" + "=" * 50)
            print("INVOCATION 2: get_cooking_time")
            print("=" * 50)
            result = await session.call_tool("get_cooking_time", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                t = result.structuredContent
                print(f"[structuredContent - TypedDict] pancakes: prep={t.get('prep_minutes')}min, cook={t.get('cook_minutes')}min, total={t.get('total_minutes')}min")

            # --- Invocation 3: get_macro_ratios ---
            # Tool (structured - dict[str, float]): structuredContent populated from dict schema
            print("\n" + "=" * 50)
            print("INVOCATION 3: get_macro_ratios")
            print("=" * 50)
            result = await session.call_tool("get_macro_ratios", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                ratios = result.structuredContent
                print(f"[structuredContent - dict] pancakes macros: carbs={ratios.get('carbs_pct')}, protein={ratios.get('protein_pct')}, fat={ratios.get('fat_pct')}")

            # --- Invocation 4: get_dish_rating ---
            # Tool (plain class + annotations): structuredContent populated, content is a memory address
            # pydantic_core cannot serialize a plain class → falls back to str() → memory address
            print("\n" + "=" * 50)
            print("INVOCATION 4: get_dish_rating")
            print("=" * 50)
            result = await session.call_tool("get_dish_rating", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - plain class] {content.text}")
            if result.structuredContent:
                rating = result.structuredContent
                print(f"[structuredContent - plain class] {rating.get('dish')}: {rating.get('score')}/10 by {rating.get('reviewer')}")

            # --- Invocation 5: get_substitute ---
            # Tool (dataclass): both layers populated — pydantic_core natively serializes dataclasses to JSON
            print("\n" + "=" * 50)
            print("INVOCATION 5: get_substitute")
            print("=" * 50)
            result = await session.call_tool("get_substitute", arguments={"ingredient": "butter"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - dataclass] {content.text}")
            if result.structuredContent:
                sub = result.structuredContent
                print(f"[structuredContent - dataclass] substitute for {sub.get('original')}: {sub.get('substitute')} ({sub.get('ratio')})")

            # --- Invocation 6: get_recipe_note ---
            # Tool (plain class, no annotations): no schema → structuredContent=None, content is a memory address
            print("\n" + "=" * 50)
            print("INVOCATION 6: get_recipe_note")
            print("=" * 50)
            result = await session.call_tool("get_recipe_note", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            notes = []
            for content in result.content:
                if isinstance(content, types.TextContent):
                    notes.append(content.text)
            print(f"[untyped class] text only: {notes}")
            print(f"[untyped class] structuredContent={result.structuredContent}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
