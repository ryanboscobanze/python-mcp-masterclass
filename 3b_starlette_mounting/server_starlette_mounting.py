"""MCP server: Starlette ASGI mounting (streamable HTTP transport).

File: 3b_starlette_mounting/server_starlette_mounting.py

Demonstrates how to embed a FastMCP server inside an existing Starlette ASGI
application — the right pattern when MCP is one component of a larger web service:

  - FastMCP("My App", json_response=True) enables JSON-encoded HTTP responses
    instead of SSE/newline-delimited streams; works with plain HTTP clients.
  - mcp.streamable_http_app() returns an ASGI sub-application for the MCP
    transport layer. Pass it to Starlette's Mount() exactly like any other app.
  - The custom lifespan calls mcp.session_manager.run() so that the session
    manager starts and stops in lockstep with the Starlette application.

Contrast with mcp.run(transport="streamable-http") shown in intro/, which runs
MCP as a self-contained standalone process. This pattern lets you mount MCP at
a URL prefix inside a FastAPI / Starlette app that already owns its own routes,
middleware, and lifespan hooks.
--port 8000 is not required. Uvicorn defaults to port 8000 
--reload is optional too — it just watches for file changes and auto-restarts the server, which is a development convenience.
Run with:
    uvicorn 3b_starlette_mounting.server_starlette_mounting:app --port 8000
    uvicorn 3b_starlette_mounting.server_starlette_mounting:app --reload
  or from the demo directory:
    uvicorn 3b_starlette_mounting.server_starlette_mounting:app --port 8000 --reload
"""

import contextlib

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server.fastmcp import FastMCP

# json_response=True: responses are JSON objects rather than SSE streams,
# which works with any HTTP client (no event-stream reader required).
mcp = FastMCP("My App", json_response=True)


@mcp.tool()
def hello() -> str:
    """A simple hello tool."""
    return "Hello from MCP!"


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back to the caller."""
    return f"Echo: {message}"


@mcp.resource("info://server")
def server_info() -> str:
    """Static resource describing this server instance."""
    return "Starlette ASGI mounting example — FastMCP mounted via mcp.streamable_http_app()"


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Drive the MCP session manager for the full lifetime of the Starlette app.

    mcp.session_manager.run() is an async context manager that must be active
    while the server handles requests. Placing it inside the Starlette lifespan
    guarantees it starts before the first request and stops on graceful shutdown.
    """
    async with mcp.session_manager.run():
        yield


# Mount the MCP ASGI sub-app at "/" so the protocol endpoint is at /mcp.
# To co-exist with other Starlette routes, mount MCP at a prefix and add your
# own routes before it, e.g.:
#   Route("/health", health_handler),
#   Mount("/mcp", app=mcp.streamable_http_app()),
app = Starlette(
    routes=[
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
