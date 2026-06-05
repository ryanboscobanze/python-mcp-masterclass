# ─── MOUNTING ────────────────────────────────────────────────────────────────
# Mounting embeds one ASGI app inside another at a path prefix.
# This is how you add a FastMCP server to a larger app without losing your own routes:
#
#   app = Starlette(routes=[
#       Route("/", my_homepage),
#       Mount("/", app=mcp.sse_app()),  # Claude connects to /sse
#   ])

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.testclient import TestClient


# ─── TWO SEPARATE SUB-APPS ────────────────────────────────────────────────────

async def api_status(request: Request) -> JSONResponse:
    return JSONResponse({"api": "running"})

async def api_version(request: Request) -> JSONResponse:
    return JSONResponse({"version": "1.0"})

api_app = Starlette(routes=[
    Route("/status",  api_status),
    Route("/version", api_version),
])


async def admin_dashboard(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Admin dashboard")

admin_app = Starlette(routes=[
    Route("/", admin_dashboard),
])


# ─── COMBINED APP ─────────────────────────────────────────────────────────────

async def homepage(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Main app — tools at /api, admin at /admin")


app = Starlette(routes=[
    Route("/",       homepage),
    Mount("/api",    app=api_app),     # api_app handles /api/status, /api/version
    Mount("/admin",  app=admin_app),   # admin_app handles /admin/
])


# ─── TEST ─────────────────────────────────────────────────────────────────────
# Run with uvicorn: uvicorn 04_mounting:app --reload

client = TestClient(app)

print(client.get("/").text)
print(client.get("/api/status").json())
print(client.get("/api/version").json())
print(client.get("/admin/").text)


# ─── WITH A REAL FASTMCP SERVER ───────────────────────────────────────────────
#
# from mcp.server.fastmcp import FastMCP
# import contextlib
# mcp = FastMCP("my_server")
#
# SSE (v1.x default — being superseded, no lifespan needed):
# app = Starlette(routes=[
#     Route("/", homepage),
#     Mount("/", app=mcp.sse_app()),   # Claude connects to /sse
# ])
#
# Streamable HTTP (current — requires lifespan):
# @contextlib.asynccontextmanager
# async def lifespan(app):
#     async with mcp.session_manager.run():
#         yield
#
# app = Starlette(
#     routes=[Route("/", homepage), Mount("/", app=mcp.streamable_http_app())],
#     lifespan=lifespan,               # Claude connects to /mcp
# )


# ─── KEY MENTAL MODEL ────────────────────────────────────────────────────────
#
# Mount("/prefix", app=sub_app)
#   — strips the prefix before forwarding to sub_app
#   — sub_app sees /status, not /api/status
#
# Route("/path", handler)
#   — exact match only (with optional path params)
