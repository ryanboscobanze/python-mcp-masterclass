# ─── MIDDLEWARE ──────────────────────────────────────────────────────────────
# Middleware wraps every request before it reaches a route handler.
# First in the list = outermost wrapper (runs first in, last out).
#
# FastMCP does not add CORSMiddleware — you add it yourself.

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.types import ASGIApp, Receive, Scope, Send


# ─── CUSTOM MIDDLEWARE ────────────────────────────────────────────────────────
# A middleware class wraps the next app in the chain.

class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "")
            print(f"[LOG] {method} {path}")
        await self.app(scope, receive, send)


# ─── APP WITH MIDDLEWARE ──────────────────────────────────────────────────────

async def homepage(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[Route("/", homepage)],
    middleware=[
        # CORS — allow any origin (use specific origins in production)
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        # Custom logging — runs on every request
        Middleware(LoggingMiddleware),
    ],
)


# ─── TEST ─────────────────────────────────────────────────────────────────────
# Run with uvicorn: uvicorn 03_middleware:app --reload

client = TestClient(app)

response = client.get("/")
print("Status:", response.status_code)

preflight = client.options(
    "/",
    headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
)
print("CORS preflight status:", preflight.status_code)
print("Allow-Origin header:", preflight.headers.get("access-control-allow-origin"))
