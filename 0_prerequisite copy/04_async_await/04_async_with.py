import asyncio
import os


# ─── WHAT IS a context manager? ──────────────────────────────────────────────
# A context manager handles setup and teardown around a block of code —
# guaranteeing cleanup even if an error occurs.
#
# Syntax: `with resource as name:`


# The classic example — open() is a context manager built into Python.
# It opens the file on enter and closes it on exit, no matter what.

with open("example.txt", "w") as f:
    f.write("hello")
# file is guaranteed closed here, even if an exception was raised inside
os.remove("example.txt")


# Without a context manager you have to manage cleanup manually:

f = open("example.txt", "w")
try:
    f.write("hello")
finally:
    f.close()   # easy to forget; and easy to miss if an early return appears
os.remove("example.txt")


# ─── HOW context managers work internally ─────────────────────────────────────
# A class with __enter__ and __exit__ is a context manager.
# __enter__ runs on entering the `with` block — return value binds to `as name`.
# __exit__  runs on leaving — always, even if the body raised an exception.

class DatabaseConnection:
    def __enter__(self):
        print("DB: connecting...")
        return self             # what gets bound to `as conn`

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("DB: closing connection")
        if exc_type:
            print(f"DB: rolling back due to {exc_type.__name__}")
        return False            # False = let the exception propagate

with DatabaseConnection() as conn:
    print("DB: running query")
    # __exit__ is called here — connection always closed


# ─── WHAT IS async with? ──────────────────────────────────────────────────────
# `async with` does the same as `with` but when opening or closing the resource
# itself requires async work — like a network handshake or a graceful shutdown.
# Use __aenter__ and __aexit__ instead of __enter__ and __exit__.
#
# In MCP, every client session is opened and closed this way.


class MCPSession:
    async def __aenter__(self):
        print("[Session] Connecting...")
        await asyncio.sleep(0.1)        # simulate network handshake
        print("[Session] Connected.")
        return self

    async def __aexit__(self, *args):
        print("[Session] Closing...")
        await asyncio.sleep(0.05)       # simulate graceful shutdown
        print("[Session] Closed.")

    async def call_tool(self, name: str, args: dict) -> str:
        await asyncio.sleep(0.1)        # simulate round-trip
        return f"{name} returned: {args}"


async def main():
    # The session is guaranteed to close even if an exception is raised inside
    async with MCPSession() as session:
        result = await session.call_tool("weather", {"city": "Tokyo"})
        print(result)

    # Real MCP client code looks exactly like this:
    #
    # async with stdio_client(server_params) as (read, write):
    #     async with ClientSession(read, write) as session:
    #         await session.initialize()
    #         result = await session.call_tool("my_tool", {"input": "hello"})
    #
    # The nesting is intentional — two separate layers of cleanup:
    #   Outer: manages the raw byte stream (stdin/stdout pipe to the server)
    #   Inner: manages the MCP protocol session built on top of that stream
    # Both layers are guaranteed closed even if an exception occurs inside.


if __name__ == "__main__":
    asyncio.run(main())
