"""Client to test the server_sqlite_lowlevel.py server.

Run from the demo directory:
    python 5b_lifespan_sqlite_lowlevel/client_sqlite_lowlevel.py
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_sqlite_lowlevel.py")],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to LOW-LEVEL SQLite server\n")

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            print()

            print("Calling list_tables...")
            result = await session.call_tool("list_tables", {})
            print(f"   Result: {result.content[0].text}\n")

            print("Querying all users...")
            result = await session.call_tool("query_db", {"sql": "SELECT * FROM users"})
            print(f"   Result: {result.content[0].text}\n")

            print("Querying developers...")
            result = await session.call_tool("query_db", {"sql": "SELECT name, email FROM users WHERE role = 'developer'"})
            print(f"   Result: {result.content[0].text}\n")

            print("Querying active projects...")
            result = await session.call_tool("query_db", {"sql": "SELECT * FROM projects WHERE status = 'active'"})
            print(f"   Result: {result.content[0].text}\n")

            print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
