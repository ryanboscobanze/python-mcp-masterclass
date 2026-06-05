"""Client for the SSE polling server (server_sse_polling.py).

Calls process_batch and waits for the result. Stream closes and reconnects
at checkpoints are handled automatically — the client just sees the final result.

    python 6b_lowlevel_sse_polling/client_sse_polling.py
"""

import asyncio

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


async def run() -> None:
    async with streamable_http_client("http://localhost:3000/mcp/") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            print("\nCalling process_batch(items=6, checkpoint_every=3)...")
            result = await session.call_tool(
                "process_batch",
                {"items": 6, "checkpoint_every": 3},
            )

            for content in result.content:
                if isinstance(content, types.TextContent):
                    print(f"Result: {content.text}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
