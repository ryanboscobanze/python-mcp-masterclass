"""Example showing lifespan support for startup/shutdown with strong typing."""

import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession


class AppState:
    """Simple state that persists across tool calls."""
    
    def __init__(self):
        self.counter = 0
        self.startup_time = time.strftime("%H:%M:%S")
        print(f"[STARTUP] AppState initialized at {self.startup_time}", file=sys.stderr)
    
    def increment(self) -> int:
        self.counter += 1
        return self.counter
    
    def get_status(self) -> str:
        return f"Counter: {self.counter}, Server started at: {self.startup_time}"
    
    def cleanup(self):
        print(f"[CLEANUP] AppState cleanup. Final counter value: {self.counter}", file=sys.stderr)


@dataclass
class AppContext:
    """Application context with typed dependencies."""
    state: AppState


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    state = AppState()
    try:
        yield AppContext(state=state)
    finally:
        state.cleanup()


mcp = FastMCP("Lifespan Demo", lifespan=app_lifespan)


@mcp.tool()
def increment(ctx: Context[ServerSession, AppContext]) -> str:
    """Increment the counter and return the new value."""
    state = ctx.request_context.lifespan_context.state
    count = state.increment()
    return f"Counter incremented to: {count}"


@mcp.tool()
def status(ctx: Context[ServerSession, AppContext]) -> str:
    """Get current server status showing counter and startup time."""
    state = ctx.request_context.lifespan_context.state
    return state.get_status()


if __name__ == "__main__":
    mcp.run(transport="stdio")
    # mcp.run(transport="streamable-http")
