"""Cursor-based paging from a FastMCP tool — client (stdio transport).

File: 2d_tool_pagination/client_tool_pagination.py

Demonstrates consuming a FastMCP tool that returns data in chunks using a
cursor argument. This is application-level cursor paging, not MCP protocol
pagination. The cursor is passed as a plain tool argument and the client
manages the loop manually.

Run from the demo directory:
    python 2d_tool_pagination/client_tool_pagination.py

Transport:
    stdio (default)       — client spawns the server; run this file only
    streamable-http       — start the server first, then run this file
                            Uncomment the streamable_http_client line below
                            and comment out the stdio_client line.
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_tool_pagination.py")],
)


async def run():
    async with stdio_client(server_params) as (read, write):              # spawns the server as a subprocess
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):  # connects to a running server; note the extra _
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # Discovery — list tools and resource templates
            # =========================================================
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            templates = await session.list_resource_templates()
            print("Available resource templates:")
            for t in templates.resourceTemplates:
                print(f"  - {t.uriTemplate}")
            print()

            # =========================================================
            # Collect all items across every page
            # =========================================================
            all_items: list[str] = []
            cursor = None
            page_num = 0

            print("Paging through all items via list_items_page tool:")
            while True:
                page_num += 1
                result = await session.call_tool(
                    "list_items_page", {"cursor": cursor}
                )
                data = json.loads(result.content[0].text)
                all_items.extend(data["items"])
                info = data["page_info"]
                print(
                    f"  Page {page_num}: items {info['start'] + 1}–{info['end']}"
                    f"  ({len(data['items'])} items), next_cursor={data['next_cursor']!r}"
                )
                cursor = data["next_cursor"]
                if cursor is None:
                    break

            print(f"\nTotal collected: {len(all_items)} items")
            print(f"First: {all_items[0]!r}, Last: {all_items[-1]!r}\n")

            # =========================================================
            # First page only — cursor omitted, uses default None
            # =========================================================
            print("First page only (cursor omitted → default None):")
            result = await session.call_tool("list_items_page", {})
            data = json.loads(result.content[0].text)
            print(f"  items: {data['items']}")
            print(f"  next_cursor: {data['next_cursor']!r}\n")

            # =========================================================
            # Explicit cursor=None (semantically identical to the first page)
            # =========================================================
            print("Explicit cursor=None (same as first page):")
            result = await session.call_tool("list_items_page", {"cursor": None})
            data = json.loads(result.content[0].text)
            print(f"  items: {data['items']}")
            print(f"  next_cursor: {data['next_cursor']!r}\n")

            # =========================================================
            # Mid-dataset cursor — jump directly to items 51–60
            # =========================================================
            print("Mid-dataset cursor='50' (items 51–60):")
            result = await session.call_tool("list_items_page", {"cursor": "50"})
            data = json.loads(result.content[0].text)
            print(f"  items: {data['items']}")
            print(f"  next_cursor: {data['next_cursor']!r}\n")

            # =========================================================
            # Last page — cursor exhausts the dataset, next_cursor → None
            # =========================================================
            print("Last page cursor='90' (items 91–100):")
            result = await session.call_tool("list_items_page", {"cursor": "90"})
            data = json.loads(result.content[0].text)
            print(f"  items: {data['items']}")
            print(f"  next_cursor: {data['next_cursor']!r}  ← None signals end of data\n")

            # =========================================================
            # Resource template — fetch a single item by ID
            # =========================================================
            print("Fetching individual item resource items://42:")
            item = await session.read_resource("items://42")
            print(f"  Content: {item.contents[0].text!r}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
