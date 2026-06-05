"""Low-level MCP server using the legacy SSE transport (mcp.server.sse).

Two endpoints: GET /sse for the server-to-client stream, POST /messages/ for
client requests. This is the older split-endpoint model — streamable HTTP
handles both directions on a single /mcp endpoint.

    python 6a_lowlevel_sse_transport/server_sse_transport.py
"""

import uvicorn
from typing import Any

import httpx
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

app = Server("mcp-website-fetcher")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch",
            title="Website Fetcher",          # title: human-readable display name
            description="Fetches a website and returns its content",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch",
                    }
                },
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    if name != "fetch":
        raise ValueError(f"Unknown tool: {name}")
    if "url" not in arguments:
        raise ValueError("Missing required argument 'url'")

    headers = {"User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"}
    async with httpx.AsyncClient(verify=False, headers=headers, follow_redirects=True) as client:
        response = await client.get(arguments["url"])
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]


# ---------------------------------------------------------------------------
# Legacy SSE transport wiring
# ---------------------------------------------------------------------------

sse = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    """Open the SSE stream for a connecting client."""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options(),  # simplified vs manual InitializationOptions
        )
    return Response()


starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="127.0.0.1", port=8000)
