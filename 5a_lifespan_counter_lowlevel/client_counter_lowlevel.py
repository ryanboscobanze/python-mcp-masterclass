"""Client for the counter low-level server (stdio transport).

Identical to the FastMCP counter client — the client has no knowledge of
which server layer it is talking to.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_counter_lowlevel.py")],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to LOW-LEVEL server\n")

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            print()

            print("Calling status...")
            result = await session.call_tool("status", {})
            print(f"   Result: {result.content[0].text}\n")

            for i in range(3):
                print(f"Calling increment ({i+1}/3)...")
                result = await session.call_tool("increment", {})
                print(f"   Result: {result.content[0].text}")
            print()

            print("Calling status again...")
            result = await session.call_tool("status", {})
            print(f"   Result: {result.content[0].text}\n")

            print("Demo complete! Notice the counter persisted and startup time stayed the same.")


if __name__ == "__main__":
    asyncio.run(main())
