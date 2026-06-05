"""Low-level MCP server: resources (stdio transport).

Demonstrates the low-level resource handlers — the protocol primitives
FastMCP's @mcp.resource() hides:

  list_resources  — returns the resource catalogue (URI, name, title, mimeType)
  read_resource   — receives the requested URI and returns the content

All routing in read_resource is manual — you parse the URI and decide
what to return. Nothing is inferred.

Two new types not seen in previous low-level examples:
  FileUrl              — Pydantic's typed file:// URL for constructing resource URIs
  ReadResourceContents — the low-level return type that wraps content with mime_type
"""

import asyncio

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl, FileUrl

server = Server("mcp-simple-resource")

RESOURCES = {
    "greeting": {
        "content": "Hello! This is a sample text resource.",
        "title": "Welcome Message",
    },
    "help": {
        "content": "This server provides sample text resources for testing.",
        "title": "Help Documentation",
    },
    "about": {
        "content": "This is the simple-resource low-level MCP server.",
        "title": "About This Server",
    },
}


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    """Return the resource catalog — URI, name, title, description, mimeType."""
    return [
        types.Resource(
            uri=FileUrl(f"file:///{name}.txt"),
            name=name,
            title=RESOURCES[name]["title"],      # human-readable display name
            description=f"A sample text resource named {name}",
            mimeType="text/plain",
        )
        for name in RESOURCES
    ]


@server.read_resource()
async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
    """Return the content for the requested URI. All routing is manual."""
    if uri.path is None:
        raise ValueError(f"Invalid resource URI: {uri}")

    name = uri.path.replace(".txt", "").lstrip("/")

    if name not in RESOURCES:
        raise ValueError(f"Unknown resource: {uri}")

    return [
        ReadResourceContents(
            content=RESOURCES[name]["content"],
            mime_type="text/plain",
        )
    ]


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-simple-resource",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
