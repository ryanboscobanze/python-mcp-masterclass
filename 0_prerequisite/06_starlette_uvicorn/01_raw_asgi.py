# Raw ASGI — the interface that Starlette and FastMCP sit on top of.
# An ASGI app is just:  async def app(scope, receive, send)
#   scope   — dict with connection info (type, method, path, headers)
#   receive — read the next event/chunk from the client
#   send    — write an event back to the client
#
# Run the demo:  python 01_raw_asgi.py
# Live server:   python -m uvicorn 01_raw_asgi:app --port 8080
# Requirements:  pip install starlette httpx uvicorn

from starlette.testclient import TestClient


# ── APP 1: ignores the body — reads scope only, never calls receive() ─────────
# Responds to any HTTP method and any path.
# The demo calls it with GET because POSTing to it is pointless — it never reads
# what you sent.

async def raw_app(scope, receive, send):
    if scope["type"] == "http":
        method = scope["method"]
        path   = scope["path"]

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": f"method={method} path={path}".encode(),
        })


# ── APP 2: reads the request body via receive(), branches on method ───────────
# Also responds to any path — there is no URL routing in raw ASGI.
# Method branching (GET vs POST) is done manually with scope["method"].

async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    method = scope["method"]

    body_chunks = []
    while True:
        event = await receive()
        if event["type"] == "http.request":
            body_chunks.append(event.get("body", b""))
            if not event.get("more_body", False):
                break
        elif event["type"] == "http.disconnect":
            break

    request_body = b"".join(body_chunks)

    if method == "POST" and request_body:
        response_body = b"You posted: " + request_body
    else:
        response_body = b"Hello from raw ASGI - try POSTing some data"

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"text/plain"]],
    })
    await send({
        "type": "http.response.body",
        "body": response_body,
    })


# ── TestClient: runs the ASGI app in-process, no live server needed ───────────

if __name__ == "__main__":
    print("=== raw_app (receive not called) ===")
    client = TestClient(raw_app)
    r = client.get("/about")
    print("Status:", r.status_code)
    print("Body:  ", r.text)

    print()
    print("=== app — GET (empty body, hits fallback) ===")
    client2 = TestClient(app)
    r = client2.get("/")
    print("GET  Status:", r.status_code)
    print("GET  Body:  ", r.text)

    print()
    print("=== app — POST single chunk ===")
    r = client2.post("/", content=b"city=London&units=celsius")
    print("POST Status:", r.status_code)
    print("POST Body:  ", r.text)

    print()
    print("=== app — POST chunked body (exercises the receive loop) ===")
    def chunked_body():
        yield b"city=London"
        yield b"&units=celsius"

    r = TestClient(app).post("/", content=chunked_body())
    print(r.text)


# ── KEY MENTAL MODEL ──────────────────────────────────────────────────────────
#
# scope   — what kind of connection, and what does it want?
# receive — read the next event from the client
# send    — write an event back (always in order: start → body)
#
# HTTP = one request → one response (two send() calls)
# SSE  = one request → many sends held open  ← MCP over HTTP works this way
# WS   = bidirectional, scope["type"] == "websocket"
#
# FastMCP handles SSE for you — this file shows what it's doing underneath.
