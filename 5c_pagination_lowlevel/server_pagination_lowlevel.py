"""Low-level MCP pagination server (stdio transport).

Demonstrates MCP protocol-level cursor pagination — FastMCP list endpoints
return all items at once; the low-level API lets you page them.

Each list handler receives a typed Request whose params.cursor is the client's
page token, slices the dataset, and returns nextCursor in the result.

Cursor encoding: decimal integer offset as a string.
  cursor=None → first page   |   nextCursor=None → dataset exhausted

Three endpoints, same pattern:
  list_tools     — 25 tools,   5/page
  list_resources — 100 items, 10/page
  list_prompts   — 20 prompts, 7/page
"""

import asyncio

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

server = Server("pagination-server-lowlevel")

# ---------------------------------------------------------------------------
# Sample datasets
# ---------------------------------------------------------------------------

TOOLS = [
    types.Tool(
        name=f"tool_{i}",
        description=f"Sample tool number {i}",
        inputSchema={"type": "object", "properties": {}},
    )
    for i in range(1, 26)   # 25 tools
]

RESOURCES = [f"Item {i:03d}" for i in range(1, 101)]  # 100 items

PROMPTS = [
    types.Prompt(
        name=f"prompt_{i}",
        description=f"Sample prompt number {i}",
    )
    for i in range(1, 21)   # 20 prompts
]


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------

def _paginate(dataset: list, cursor: str | None, page_size: int) -> tuple[list, str | None]:
    start = 0 if cursor is None else int(cursor)
    end = start + page_size
    page = dataset[start:end]
    next_cursor = str(end) if end < len(dataset) else None
    return page, next_cursor


# ---------------------------------------------------------------------------
# List handlers — same cursor pattern on three different endpoints
# ---------------------------------------------------------------------------

@server.list_tools()
async def handle_list_tools(
    request: types.ListToolsRequest,
) -> types.ListToolsResult:
    cursor = request.params.cursor if request.params is not None else None
    page, next_cursor = _paginate(TOOLS, cursor, page_size=5)
    return types.ListToolsResult(tools=page, nextCursor=next_cursor)


@server.list_resources()
async def handle_list_resources(
    request: types.ListResourcesRequest,
) -> types.ListResourcesResult:
    cursor = request.params.cursor if request.params is not None else None
    page_names, next_cursor = _paginate(RESOURCES, cursor, page_size=10)
    resources = [
        types.Resource(
            uri=f"items://item/{name}",
            name=name,
            description=f"Description for {name}",
        )
        for name in page_names
    ]
    return types.ListResourcesResult(resources=resources, nextCursor=next_cursor)


@server.list_prompts()
async def handle_list_prompts(
    request: types.ListPromptsRequest,
) -> types.ListPromptsResult:
    cursor = request.params.cursor if request.params is not None else None
    page, next_cursor = _paginate(PROMPTS, cursor, page_size=7)
    return types.ListPromptsResult(prompts=page, nextCursor=next_cursor)


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
