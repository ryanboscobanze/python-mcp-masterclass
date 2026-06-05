"""MCP client for Starlette ASGI-mounted server (streamable HTTP transport).

File: 3b_starlette_mounting/client_starlette_mounting.py

Connects to server_starlette_mounting.py via the streamable HTTP transport.
Exercises all meaningful client patterns for this server: capability listing,
tool calls (success path, echo edge cases), and resource reads.

NOTE: The server must be running before starting this client (from the demo directory):
    uvicorn 3b_starlette_mounting.server_starlette_mounting:app --port 8000

Run with (from the demo directory):
    python 3b_starlette_mounting/client_starlette_mounting.py
"""

import asyncio

from pydantic import AnyUrl

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


async def run():
    """Run the starlette mounting client example."""
    async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # List capabilities
            # =========================================================

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            resources = await session.list_resources()
            print("Available resources:", [str(r.uri) for r in resources.resources])

            # =========================================================
            # Tool calls — hello
            # =========================================================

            # hello() takes no arguments and returns a fixed greeting
            result = await session.call_tool("hello", {})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"hello: {content.text}")

            # =========================================================
            # Tool calls — echo
            # =========================================================

            # Standard message — confirms round-trip text is preserved
            result = await session.call_tool("echo", {"message": "world"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"echo('world'): {content.text}")

            # Empty string — edge case: server should return "Echo: " not an error
            result = await session.call_tool("echo", {"message": ""})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"echo(''): {content.text!r}")

            # Unicode / special characters — verifies no encoding is lost
            result = await session.call_tool("echo", {"message": "héllo wörld 🌍"})
            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"echo(unicode): {content.text}")

            # =========================================================
            # Resource reads
            # =========================================================

            # Read the static info://server resource
            resource = await session.read_resource(AnyUrl("info://server"))
            for content in resource.contents:
                if isinstance(content, types.TextResourceContents):
                    print(f"resource info://server: {content.text}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
