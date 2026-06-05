"""Low-level MCP server demonstrating SEP-1699 SSE polling (streamable HTTP).

The server closes the SSE stream at checkpoints during a long-running tool call.
The client reconnects with Last-Event-ID and the server replays missed events.

    python 6b_lowlevel_sse_polling/server_sse_polling.py
"""

import contextlib
import logging
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import anyio
import mcp.types as types
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.streamable_http import EventCallback, EventId, EventMessage, EventStore, StreamId
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import JSONRPCMessage
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# InMemoryEventStore — copied from SDK examples/servers/sse-polling-demo
# ---------------------------------------------------------------------------

@dataclass
class EventEntry:
    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage | None  # None for priming events


class InMemoryEventStore(EventStore):
    """Simple in-memory EventStore for SSE resumability (examples/testing only)."""

    def __init__(self, max_events_per_stream: int = 100):
        self.max_events_per_stream = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}

    async def store_event(self, stream_id: StreamId, message: JSONRPCMessage | None) -> EventId:
        event_id = str(uuid4())
        entry = EventEntry(event_id=event_id, stream_id=stream_id, message=message)

        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)

        if len(self.streams[stream_id]) == self.max_events_per_stream:
            oldest = self.streams[stream_id][0]
            self.event_index.pop(oldest.event_id, None)

        self.streams[stream_id].append(entry)
        self.event_index[event_id] = entry
        return event_id

    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback: EventCallback,
    ) -> StreamId | None:
        if last_event_id not in self.event_index:
            logger.warning(f"Event ID {last_event_id} not found in store")
            return None

        last_entry = self.event_index[last_event_id]
        stream_id = last_entry.stream_id
        stream_events = self.streams.get(stream_id, deque())

        found_last = False
        for entry in stream_events:
            if found_last:
                if entry.message is not None:
                    await send_callback(EventMessage(entry.message, entry.event_id))
            elif entry.event_id == last_event_id:
                found_last = True

        return stream_id


# ---------------------------------------------------------------------------
# Low-level MCP server
# ---------------------------------------------------------------------------

app = Server("sse-polling-demo")


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    ctx = app.request_context  # access session + request metadata

    if name == "process_batch":
        items = arguments.get("items", 6)
        checkpoint_every = arguments.get("checkpoint_every", 3)

        await ctx.session.send_log_message(
            level="info",
            data=f"Starting batch of {items} items...",
            logger="process_batch",
            related_request_id=ctx.request_id,
        )

        for i in range(1, items + 1):
            await anyio.sleep(0.5)

            await ctx.session.send_log_message(
                level="info",
                data=f"[{i}/{items}] processed",
                logger="process_batch",
                related_request_id=ctx.request_id,
            )

            # Checkpoint: close the SSE stream → client reconnects with Last-Event-ID
            if i % checkpoint_every == 0 and i < items:
                await ctx.session.send_log_message(
                    level="info",
                    data=f"Checkpoint at item {i} — closing SSE stream",
                    logger="process_batch",
                    related_request_id=ctx.request_id,
                )
                if ctx.close_sse_stream:
                    logger.info(f"Closing SSE stream at checkpoint {i}")
                    await ctx.close_sse_stream()
                await anyio.sleep(0.2)  # allow client to reconnect

        return [
            types.TextContent(
                type="text",
                text=f"Done: processed {items} items (checkpoint every {checkpoint_every})",
            )
        ]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="process_batch",
            description="Process items with periodic SSE stream checkpoints.",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "integer",
                        "description": "Number of items to process (1-100)",
                        "default": 6,
                    },
                    "checkpoint_every": {
                        "type": "integer",
                        "description": "Close stream after this many items (1-20)",
                        "default": 3,
                    },
                },
            },
        )
    ]


# ---------------------------------------------------------------------------
# Starlette ASGI app with StreamableHTTPSessionManager
# ---------------------------------------------------------------------------

event_store = InMemoryEventStore()

session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=event_store,
    retry_interval=100,  # ms — how soon the client retries after stream close
)


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
    async with session_manager.run():
        logger.info("SSE polling server started on http://localhost:3000/mcp/")
        yield


starlette_app = Starlette(
    debug=True,
    routes=[Mount("/mcp", app=handle_streamable_http)],
    lifespan=lifespan,
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(starlette_app, host="127.0.0.1", port=3000)
