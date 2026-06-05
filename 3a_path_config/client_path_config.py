"""MCP client for the path-configured Starlette server (streamable HTTP transport).

File: 3a_path_config/client_path_config.py

Connects to server_path_config.py — a FastMCP server built with
streamable_http_path="/" and mounted at /process inside a Starlette app.

The key verification: the client connects to /process, *not* /process/mcp.
That URL only works because streamable_http_path="/" collapsed the endpoint
to the mount root.  Pointing at /process/mcp would result in a 404.

Exercises:
  - session.initialize()
  - session.list_tools()
  - session.call_tool("process_data", ...)  — normal string, numeric, empty, unicode

NOTE: The server must be running before starting this client (from the demo directory):
    uvicorn 3a_path_config.server_path_config:app --port 8000

Run with (from the demo directory):
    python 3a_path_config/client_path_config.py
"""

import asyncio

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

# /process — not /process/mcp — confirms streamable_http_path="/" is in effect.
SERVER_URL = "http://localhost:8000/process"


async def run():
    """Run the path-config client example."""
    async with streamable_http_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # List capabilities
            # =========================================================

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # =========================================================
            # Tool calls — process_data
            # =========================================================

            # Normal string — confirms the endpoint at /process is reachable
            result = await session.call_tool("process_data", {"data": "hello world"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"process_data('hello world'): {content.text}")

            # Numeric-looking string — verifies data passes through unchanged
            result = await session.call_tool("process_data", {"data": "42"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"process_data('42'): {content.text}")

            # Empty string — edge case: server returns "Processed: ", not an error
            result = await session.call_tool("process_data", {"data": ""})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"process_data(''): {content.text!r}")

            # Unicode — verifies no encoding loss through the HTTP transport
            result = await session.call_tool("process_data", {"data": "héllo 🌍"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"process_data(unicode): {content.text}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
