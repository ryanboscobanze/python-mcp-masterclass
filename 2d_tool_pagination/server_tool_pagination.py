"""Cursor-based paging from a FastMCP tool (stdio transport).

File: 2d_tool_pagination/server_tool_pagination.py

Demonstrates returning large datasets in chunks from a FastMCP tool using a
cursor argument. This is application-level cursor paging — not the MCP
protocol's built-in pagination (which travels via PaginatedRequestParams on
list_resources). The cursor is just a regular tool argument.

This server exposes:
  - list_items_page tool: accepts cursor (integer offset as a string) and returns
    a page of items plus a next_cursor; cursor=None means "start from the beginning"
  - get_item resource template: fetch a single item by 1-based numeric ID

Run with:
    python 2d_tool_pagination/server_tool_pagination.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="PaginationExample")

ITEMS = [f"Item {i:03d}" for i in range(1, 101)]  # 100 items
PAGE_SIZE = 10


@mcp.tool(
    description=(
        "Return a page of items. Pass cursor=None for the first page, or the "
        "next_cursor value from the previous response to advance through the dataset."
    )
)
def list_items_page(cursor: str | None = None) -> dict:
    """Return one page of items and an optional next_cursor."""
    start = 0 if cursor is None else int(cursor)
    end = min(start + PAGE_SIZE, len(ITEMS))
    page = ITEMS[start:end]
    next_cursor = str(end) if end < len(ITEMS) else None
    return {
        "items": page,
        "next_cursor": next_cursor,
        "page_info": {
            "start": start,
            "end": end,
            "total": len(ITEMS),
        },
    }


@mcp.resource("items://{item_id}")
def get_item(item_id: str) -> str:
    """Fetch a single item by its 1-based numeric ID."""
    idx = int(item_id) - 1
    if 0 <= idx < len(ITEMS):
        return ITEMS[idx]
    raise ValueError(f"Item ID {item_id!r} out of range (1–{len(ITEMS)})")


if __name__ == "__main__":
    mcp.run(transport="stdio")
    # mcp.run(transport="streamable-http")
