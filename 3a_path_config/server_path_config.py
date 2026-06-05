"""MCP server: Starlette ASGI path configuration (streamable HTTP transport).

File: 3a_path_config/server_path_config.py

Demonstrates the streamable_http_path constructor parameter — which controls
where inside a Starlette Mount() the MCP protocol endpoint is registered:

  Default behaviour:
      FastMCP("My App")
      Mount("/api", app=mcp.streamable_http_app())
      → MCP reachable at /api/mcp

  With streamable_http_path="/":
      FastMCP("My App", streamable_http_path="/")
      Mount("/process", app=mcp.streamable_http_app())
      → MCP reachable at /process  (not /process/mcp)

The path is collapsed to the mount point itself, which is useful when you
want a clean URL for the MCP endpoint (e.g. /api instead of /api/mcp) or
when a reverse-proxy strips the prefix before forwarding to the app.

Contrast with mcp_revamp/starlette_mounting/ which uses the default path
so MCP lives at /mcp under the Starlette root.

Run with (from the demo directory):
    uvicorn 3a_path_config.server_path_config:app --port 8000
"""

import contextlib

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server.fastmcp import FastMCP

# streamable_http_path="/" collapses the protocol endpoint to the Mount() root.
# json_response=True: HTTP responses carry JSON rather than SSE/event-streams,
# which works with any plain HTTP client.
mcp = FastMCP("Path Config", json_response=True, streamable_http_path="/")


@mcp.tool()
def process_data(data: str) -> str:
    """Process some data and return a confirmation."""
    return f"Processed: {data}"


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Drive the MCP session manager for the full Starlette app lifetime."""
    async with mcp.session_manager.run():
        yield


# Mount at /process.  Because streamable_http_path="/", the MCP protocol
# endpoint lives exactly at /process — not at /process/mcp.
app = Starlette(
    routes=[
        Mount("/process", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
