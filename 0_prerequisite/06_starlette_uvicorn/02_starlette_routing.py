# ─── STARLETTE ROUTING ───────────────────────────────────────────────────────
#
# Starlette wraps the raw ASGI interface in a clean routing and
# request/response API. Instead of writing scope/receive/send by hand,
# you write async handler functions that receive a Request and return a Response.
#
# FastMCP creates a Starlette app internally when you use HTTP/SSE transport.

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient


# ─── ROUTE HANDLERS ──────────────────────────────────────────────────────────
# Each handler is an async function: Request -> Response.

async def homepage(request: Request) -> JSONResponse:
    return JSONResponse({"message": "MCP server running", "version": "1.0"})


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def echo(request: Request) -> PlainTextResponse:
    # Read a query parameter from the URL: /echo?text=hello
    text = request.query_params.get("text", "nothing")
    return PlainTextResponse(f"You said: {text}")


async def create_item(request: Request) -> JSONResponse:
    # Read a JSON body from a POST request
    body = await request.json()
    name = body.get("name", "unnamed")
    return JSONResponse({"created": name}, status_code=201)


# ─── WIRE ROUTES TO HANDLERS ─────────────────────────────────────────────────

app = Starlette(routes=[
    Route("/",        homepage),
    Route("/health",  health),
    Route("/echo",    echo),
    Route("/items",   create_item, methods=["POST"]),
])


# ─── TEST WITHOUT RUNNING UVICORN ────────────────────────────────────────────
# Run with uvicorn: uvicorn 02_starlette_routing:app --reload

client = TestClient(app)

print(client.get("/").json())
print(client.get("/health").json())
print(client.get("/echo?text=MCP").text)
print(client.post("/items", json={"name": "weather_tool"}).json())


# ─── KEY MENTAL MODEL ────────────────────────────────────────────────────────
#
# Route("/path", handler)         — GET by default
# Route("/path", handler, methods=["POST"])  — restrict to specific HTTP methods
#
# request.query_params.get("key") — ?key=value in the URL
# await request.json()            — parse the JSON request body
# JSONResponse(dict)              — serialise dict to JSON and set Content-Type
#
# FastMCP transport options (verified against FastMCP source):
#   stdio (default)    — no Starlette, no routes, no web server
#   sse                — Route("/sse", methods=["GET"])  +  Mount("/messages/", ...)
#   streamable-http    — Route("/mcp", ...)  (no method restriction, default path /mcp)
