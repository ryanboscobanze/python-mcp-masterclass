# ─── UVICORN ─────────────────────────────────────────────────────────────────
# Uvicorn is an ASGI server — it binds to a port, accepts TCP connections,
# speaks HTTP, and calls your ASGI app for each request.
# In the MCP stack: [ uvicorn ] → [ Starlette ] → [ FastMCP ] → [ your tools ]
#
#
# ─── RUNNING FROM THE COMMAND LINE ───────────────────────────────────────────
#
# Basic:
#   uvicorn 05_uvicorn_run:app --port 8080
#
# Dev — auto-reload on file changes:
#   uvicorn 05_uvicorn_run:app --reload
#
# "05_uvicorn_run:app" means:
#   05_uvicorn_run  — the Python module (this file)
#   app             — the variable name of the ASGI app inside it
#
#
# ─── KEY OPTIONS ─────────────────────────────────────────────────────────────
#
#   --host    default 127.0.0.1   use 0.0.0.0 to accept external connections
#   --port    default 8000        TCP port to listen on
#   --reload  off                 restart on code changes (dev only)

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


# ─── THE APP ─────────────────────────────────────────────────────────────────

async def homepage(request: Request) -> JSONResponse:
    return JSONResponse({"status": "running", "transport": "http"})


app = Starlette(routes=[Route("/", homepage)])


# ─── RUN AND TEST ─────────────────────────────────────────────────────────────
# Terminal 1 — start the server:
#   python 05_uvicorn_run.py
#
# Terminal 2 — test it:
#   curl.exe http://localhost:8080/        (Windows — avoids PowerShell alias)
#   curl http://localhost:8080/            (Mac/Linux)
#   → {"status":"running","transport":"http"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)


# ─── HOW FASTMCP USES UVICORN ────────────────────────────────────────────────
# host and port are set on the constructor, not on run().
#
# from mcp.server.fastmcp import FastMCP
# mcp = FastMCP("my_server", host="0.0.0.0", port=8080)
#
# if __name__ == "__main__":
#     mcp.run()                             # stdio (default) — no uvicorn
#     mcp.run(transport="sse")              # SSE — calls uvicorn.Config + uvicorn.Server
#     mcp.run(transport="streamable-http")  # streamable HTTP — same
