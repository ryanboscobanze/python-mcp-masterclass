import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


# ─── CREATING async context managers ────────────────────────────────────────
# 04_async_with.py taught you to USE async context managers (async with).
# 05_async_for.py  will teach you async generators    (async def + yield).
#
# This file sits between them: @asynccontextmanager combines both ideas.
# It turns an async generator function into an async context manager —
# everything before yield is __aenter__, everything after is __aexit__.
#
# In MCP, every server defines a lifespan this way.


# ─── WITHOUT @asynccontextmanager ────────────────────────────────────────────
# You already know this from 04_async_with.py — a class with __aenter__ / __aexit__.
# It works, but it is verbose for simple setup/teardown.

class DatabaseClass:
    async def __aenter__(self):
        print("[DB] connecting...")
        await asyncio.sleep(0.05)
        self.connected = True
        return self

    async def __aexit__(self, *args):
        print("[DB] closing...")
        await asyncio.sleep(0.02)
        self.connected = False


# ─── WITH @asynccontextmanager ────────────────────────────────────────────────
# Same behaviour, half the code.
# Rule: everything before yield = setup (__aenter__)
#       yield value               = what gets bound to `as db`
#       everything after yield    = teardown (__aexit__)

@asynccontextmanager
async def database() -> AsyncIterator[dict]:
    print("[DB] connecting...")
    await asyncio.sleep(0.05)
    conn = {"status": "open"}           # the object bound to `as db`
    yield conn                          # control passes to the `async with` body
    print("[DB] closing...")            # runs after the body exits
    await asyncio.sleep(0.02)
    conn["status"] = "closed"


async def compare():
    print("=== class-based ===")
    async with DatabaseClass() as db:
        print(f"  connected: {db.connected}")

    print("\n=== @asynccontextmanager ===")
    async with database() as db:
        print(f"  status: {db['status']}")


# ─── AsyncIterator[T] — the return type ──────────────────────────────────────
# An @asynccontextmanager function is an async generator under the hood.
# The correct type annotation for its return value is AsyncIterator[T]
# from collections.abc.
#
# You will see this on every lifespan function in the MCP course:
#
#   from collections.abc import AsyncIterator
#
#   @asynccontextmanager
#   async def app_lifespan(server) -> AsyncIterator[AppContext]:
#       ...
#       yield AppContext(db=db)
#       ...
#
# AsyncIterator[AppContext] tells the type checker:
# "this async generator yields AppContext objects".
# Without it the code still runs — it is a type hint, not runtime behaviour.


# ─── try / finally — guaranteed teardown even on errors ───────────────────────
# If the body of `async with` raises an exception, the code after yield
# still runs — but only if it is inside a finally block.

@asynccontextmanager
async def safe_connection(host: str) -> AsyncIterator[dict]:
    print(f"[{host}] connecting...")
    await asyncio.sleep(0.05)
    conn = {"host": host}
    try:
        yield conn                      # body runs here
    finally:
        print(f"[{host}] closing (always runs)")   # runs even if body raises
        await asyncio.sleep(0.02)


async def show_guaranteed_cleanup():
    print("\n=== cleanup runs even when body raises ===")
    try:
        async with safe_connection("localhost") as conn:
            print(f"  connected to {conn['host']}")
            raise ValueError("something went wrong")
    except ValueError as e:
        print(f"  caught: {e}")
    # [localhost] closing still printed above — teardown was guaranteed


# ─── MCP lifespan shape ───────────────────────────────────────────────────────
# This is the exact pattern every MCP server uses.
# The lifespan hook runs once at startup (before the server accepts any tool
# calls) and once at shutdown (after the last connection closes).
#
#   from collections.abc import AsyncIterator
#   from contextlib import asynccontextmanager
#   from dataclasses import dataclass
#   from mcp.server.fastmcp import FastMCP
#
#   @dataclass
#   class AppContext:
#       db: Database
#
#   @asynccontextmanager
#   async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
#       db = await Database.connect()   # startup
#       try:
#           yield AppContext(db=db)     # context available to every tool via ctx
#       finally:
#           await db.disconnect()       # shutdown — always runs
#
#   mcp = FastMCP("my_server", lifespan=app_lifespan)


async def main():
    await compare()
    await show_guaranteed_cleanup()


if __name__ == "__main__":
    asyncio.run(main())
