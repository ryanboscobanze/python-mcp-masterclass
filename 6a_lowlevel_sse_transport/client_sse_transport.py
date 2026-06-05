"""Client for the legacy SSE transport server (server_sse_transport.py).

Uses sse_client: opens a persistent GET /sse stream to receive events,
sends requests via POST /messages/.

Start the server first, then:
    python 6a_lowlevel_sse_transport/client_sse_transport.py
"""

import asyncio

from mcp import ClientSession, types
from mcp.client.sse import sse_client


async def run() -> None:
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            print("\nCalling fetch('https://example.com')...")
            result = await session.call_tool("fetch", {"url": "https://example.com"})

            for content in result.content:
                if isinstance(content, types.TextContent):
                    # Print just the first 200 chars — the page can be large
                    print(f"Result (first 200 chars):\n{content.text[:200]}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
