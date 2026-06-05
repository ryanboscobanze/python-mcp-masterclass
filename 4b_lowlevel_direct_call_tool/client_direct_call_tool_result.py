"""Client for the direct-CallToolResult low-level server (stdio transport).

Shows how a standard ClientSession receives a CallToolResult:

  result.content           — list of content items visible to the model
  result.structuredContent — machine-readable dict set by the server
  result.meta              — the _meta dict the server attached
                             (server sets _meta, client reads .meta)
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_direct_call_tool_result.py")],
)


async def run() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # Discover — inspect the tool's input schema
            # =========================================================
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  name       : {tool.name}")
                print(f"  description: {tool.description}")
                print(f"  inputSchema: {tool.inputSchema}")
            print()

            # =========================================================
            # Call — inspect all three result layers
            # =========================================================
            print("Calling advanced_tool(message='Hello from client'):")
            result = await session.call_tool(
                "advanced_tool",
                arguments={"message": "Hello from client"},
            )

            print(f"  content count    : {len(result.content)}")
            for item in result.content:
                if hasattr(item, "text"):
                    print(f"  content[0].text  : {item.text}")

            print(f"  structuredContent: {result.structuredContent}")
            print(f"  meta             : {result.meta}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
