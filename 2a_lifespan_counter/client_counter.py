"""Client to test the server_counter.py server.

Run from the demo directory:
    python 2a_lifespan_counter/client_counter.py

Transport:
    stdio (default)       — client spawns the server; run this file only
    streamable-http       — start the server first, then run this file
                            Uncomment the streamable_http_client line below
                            and comment out the stdio_client line.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_counter.py")],
)


async def main():
    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to server\n")

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            print()

            # Call status first - should show Counter: 0
            print("Calling status...")
            result = await session.call_tool("status", {})
            print(f"   Result: {result.content[0].text}\n")

            # Increment three times
            for i in range(3):
                print(f"Calling increment ({i+1}/3)...")
                result = await session.call_tool("increment", {})
                print(f"   Result: {result.content[0].text}")
            print()

            # Call status again - should show Counter: 3, same startup time
            print("Calling status again...")
            result = await session.call_tool("status", {})
            print(f"   Result: {result.content[0].text}\n")

            print("Demo complete! Notice the counter persisted and startup time stayed the same.")


if __name__ == "__main__":
    asyncio.run(main())
