"""Section 7 client: Full Tour — all six concept sections in one client.

Exercises every tool, resource, and prompt from sections 1–6 in a single
sequential run. Each section block is self-contained and mirrors the pattern
from its dedicated section_* client.
"""

import asyncio
import json
import os
import sys

from pydantic import AnyUrl

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

            # List all tools
            tools = await session.list_tools()
            print(json.dumps(tools.model_dump(), indent=2, default=str))
            print("-" * 50)

            # =========================================================
            # SECTION 1: Simple Tools
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 1: Simple Tools")
            print("=" * 50)

            # get_display_name: with and without title
            print("=== get_display_name behavior ===")
            for tool in tools.tools:
                print(f"  name={tool.name!r:35} title={str(tool.title)!r:30} → display={get_display_name(tool)!r}")
            print("-" * 50)

            # Tool (text): int return → TextContent on the wire
            result = await session.call_tool("double_servings", arguments={"servings": 4})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[text] double_servings(4) = {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # Tool (primitive - list[str]): FastMCP expands list into multiple TextContent items
            result = await session.call_tool("list_dishes")
            print(f"[raw result] {result}")
            print("-" * 50)
            dishes = []
            for content in result.content:
                if isinstance(content, types.TextContent):
                    dishes.append(content.text)
            print(f"[primitive - list[str]] available dishes: {dishes}")
            print(f"[structuredContent] {result.structuredContent}")

            # Tool (title): called by function name, displayed via get_display_name
            result = await session.call_tool("suggest_wine", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[wine pairing] pancakes → {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # Tool (Field descriptions): only required arg passed; defaults fill the rest
            result = await session.call_tool("scale_recipe", arguments={"dish": "pasta"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[Field descriptions] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # =========================================================
            # SECTION 2: Resources
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 2: Resources")
            print("=" * 50)

            # List static resources
            resources = await session.list_resources()
            print(f"[static resources] {[r.uri for r in resources.resources]}")

            # Read static resource (fixed URI)
            conversions = await session.read_resource(AnyUrl("kitchen://conversions"))
            content_block = conversions.contents[0]
            if isinstance(content_block, types.TextResourceContents):
                print(f"[static resource] {content_block.text}")

            # List resource templates
            templates = await session.list_resource_templates()
            print(f"[resource templates] {[t.uriTemplate for t in templates.resourceTemplates]}")

            # Read dynamic resource (URI template)
            resource_content = await session.read_resource(AnyUrl("recipe://pancakes"))
            content_block = resource_content.contents[0]
            if isinstance(content_block, types.TextResourceContents):
                print(f"[dynamic resource] {content_block.text}")

            # =========================================================
            # SECTION 3: Prompts
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 3: Prompts")
            print("=" * 50)

            # List prompts
            prompts = await session.list_prompts()
            print(f"[prompts] {[p.name for p in prompts.prompts]}")

            # Prompt (string): single message result
            prompt = await session.get_prompt(
                "cooking_instructions",
                arguments={"dish": "pancakes", "skill_level": "beginner"},
            )
            print(f"[prompt - string] {prompt.messages[0].content.text}")

            # Prompt (messages): multi-turn result
            prompt = await session.get_prompt(
                "troubleshoot_dish",
                arguments={"dish": "pancakes", "problem": "they came out flat and rubbery"},
            )
            print("[prompt - messages]")
            for msg in prompt.messages:
                print(f"  [{msg.role}]: {msg.content.text}")

            # =========================================================
            # SECTION 4: Structured Return Types
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 4: Structured Return Types")
            print("=" * 50)

            # Pydantic model → structuredContent
            result = await session.call_tool("get_nutrition", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                info = result.structuredContent
                print(f"[structuredContent - Pydantic] {info.get('dish')}: {info.get('calories')} kcal, {info.get('protein_g')}g protein")

            # TypedDict → structuredContent
            result = await session.call_tool("get_cooking_time", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                t = result.structuredContent
                print(f"[structuredContent - TypedDict] prep={t.get('prep_minutes')}min, cook={t.get('cook_minutes')}min, total={t.get('total_minutes')}min")

            # dict[str, float] → structuredContent
            result = await session.call_tool("get_macro_ratios", arguments={"dish": "pancakes"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                ratios = result.structuredContent
                print(f"[structuredContent - dict] carbs={ratios.get('carbs_pct')}, protein={ratios.get('protein_pct')}, fat={ratios.get('fat_pct')}")

            # class with type hints → structuredContent
            result = await session.call_tool("get_substitute", arguments={"ingredient": "butter"})
            print(f"[raw result] {result}")
            print("-" * 50)
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[content - text] {content.text}")
            if result.structuredContent:
                sub = result.structuredContent
                print(f"[structuredContent - class] substitute for {sub.get('original')}: {sub.get('substitute')} ({sub.get('ratio')})")

            # class WITHOUT type hints → structuredContent is None
            result = await session.call_tool("get_recipe_note", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[untyped class] text only: {content.text}")
            print(f"[untyped class] structuredContent={result.structuredContent}")

            # =========================================================
            # SECTION 5: CallToolResult Patterns
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 5: CallToolResult Patterns")
            print("=" * 50)

            # isError=True path
            result = await session.call_tool("check_pantry", arguments={"ingredient": "truffle oil"})
            if result.isError:
                for content in result.content:
                    if isinstance(content, types.TextContent):
                        print(f"[error] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # isError=False path
            result = await session.call_tool("check_pantry", arguments={"ingredient": "eggs"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[success] {content.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # EmbeddedResource in content
            result = await session.call_tool("get_recipe_card", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.EmbeddedResource):
                    resource = content.resource
                    if isinstance(resource, types.TextResourceContents):
                        print(f"[embedded resource] {resource.uri} ({resource.mimeType}): {resource.text}")
            print(f"[structuredContent] {result.structuredContent}")

            # ImageContent via CallToolResult
            result = await session.call_tool("generate_serving_chart", arguments={"servings": 4})
            for content in result.content:
                if isinstance(content, types.ImageContent):
                    print(f"[image - CallToolResult] mimeType={content.mimeType}, size={len(content.data)} bytes")
            print(f"[structuredContent] {result.structuredContent}")

            # ImageContent via FastMCP Image
            result = await session.call_tool("create_recipe_label", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.ImageContent):
                    print(f"[image - FastMCP Image] mimeType={content.mimeType}, size={len(content.data)} bytes")
            print(f"[structuredContent] {result.structuredContent}")

            # _meta: client-only metadata
            result = await session.call_tool("get_dish_info", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[_meta] description: {content.text}")
            if result.meta:
                print(f"[_meta] client-only metadata: {result.meta}")
            print(f"[structuredContent] {result.structuredContent}")

            # Empty CallToolResult
            result = await session.call_tool("clear_added_dishes")
            print(f"[empty CallToolResult] content={result.content}, isError={result.isError}")
            print(f"[structuredContent] {result.structuredContent}")

            # Annotated[CallToolResult, Model] → validated structuredContent
            result = await session.call_tool("get_validated_macros", arguments={"dish": "pancakes"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"[annotated CallToolResult] {content.text}")
            if result.structuredContent:
                m = result.structuredContent
                print(f"[annotated CallToolResult] validated: dish={m.get('dish')}, dominant={m.get('dominant_macro')}, score={m.get('balance_score')}")

            # =========================================================
            # SECTION 6: Async + Context
            # =========================================================

            print("\n" + "=" * 50)
            print("SECTION 6: Async + Context")
            print("=" * 50)

            # ctx.error — empty list triggers error log and early return
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

            # ctx.warning — "soup" unknown; known dishes proceed; progress reported per dish
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

            # send_resource_list_changed — mutates recipes dict and notifies client
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

            # Confirm recipe://risotto is now resolvable
            risotto_content = await session.read_resource(AnyUrl("recipe://risotto"))
            content_block = risotto_content.contents[0]
            if isinstance(content_block, types.TextResourceContents):
                print(f"[new resource] {content_block.uri}: {content_block.text}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
