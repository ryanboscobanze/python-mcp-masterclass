"""Client to test the server_sqlite.py server.

Run from the demo directory:
    python 2b_lifespan_sqlite/client_sqlite.py

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
    args=[os.path.join(_here, "server_sqlite.py")],
)


async def main():
    async with stdio_client(server_params) as (read, write):              # spawns the server as a subprocess
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):  # connects to a running server; note the extra _
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to SQLite server\n")

            # List tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            print()

            # List tables
            print("Calling list_tables...")
            result = await session.call_tool("list_tables", {})
            print(f"   Result: {result.content[0].text}\n")

            # List all users
            print("Listing all users...")
            result = await session.call_tool("list_users", {})
            print(f"   Result:\n{result.content[0].text}\n")

            # Query developers only
            print("Querying developers...")
            result = await session.call_tool("query_db", {"sql": "SELECT name, email FROM users WHERE role = 'developer'"})
            print(f"   Result: {result.content[0].text}\n")

            # Query active projects
            print("Querying active projects...")
            result = await session.call_tool("query_db", {"sql": "SELECT * FROM projects WHERE status = 'active'"})
            print(f"   Result: {result.content[0].text}\n")

            # Demonstrate lifespan shared state: add a user, then list to prove it persists
            print("Adding a new user (Eve)...")
            result = await session.call_tool("add_user", {"name": "Eve", "email": "eve@example.com", "role": "manager"})
            print(f"   Result: {result.content[0].text}\n")

            print("Listing all users (Eve should now appear — same DB connection, shared via lifespan)...")
            result = await session.call_tool("list_users", {})
            print(f"   Result:\n{result.content[0].text}\n")

            print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
