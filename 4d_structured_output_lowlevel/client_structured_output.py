"""Client for the structured-output low-level server (stdio transport).

Exercises two low-level capabilities the server exposes:

  tool.outputSchema        — visible on the Tool object from list_tools(),
                             tells the client the result shape before calling
  result.structuredContent — the validated dict returned by the server
                             (also serialised into result.content for backward compatibility)
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_structured_output.py")],
)


async def run() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # 1. Discover — inspect inputSchema and outputSchema
            # =========================================================
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  name        : {tool.name}")
                print(f"  description : {tool.description}")
                print(
                    f"  inputSchema : {json.dumps(tool.inputSchema, indent=4)}"
                )
                print(
                    f"  outputSchema: {json.dumps(tool.outputSchema, indent=4)}"
                )
            print()

            # =========================================================
            # 2. Call — inspect content (backward-compat) and
            #           structuredContent (validated dict)
            # =========================================================
            print("Calling get_weather(city='London'):")
            result = await session.call_tool(
                "get_weather", arguments={"city": "London"}
            )

            print(f"  content count    : {len(result.content)}")
            for item in result.content:
                if hasattr(item, "text"):
                    print(f"  content[0].text  : {item.text}")

            print(f"  structuredContent: {result.structuredContent}")
            print()

            # =========================================================
            # 3. Second call with a different city
            # =========================================================
            print("Calling get_weather(city='Tokyo'):")
            result = await session.call_tool(
                "get_weather", arguments={"city": "Tokyo"}
            )
            print(f"  structuredContent: {result.structuredContent}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
