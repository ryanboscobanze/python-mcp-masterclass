"""Client for the simple resource low-level server (stdio transport).

Exercises the two resource protocol endpoints:

  session.list_resources()   → ListResourcesResult with .resources
  session.read_resource(uri) → ReadResourceResult with .contents
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_simple_resource.py")],
)


async def run() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # 1. Discover available resources
            # =========================================================
            resources = await session.list_resources()
            print("Available resources:")
            for r in resources.resources:
                print(f"  uri      : {r.uri}")
                print(f"  name     : {r.name}")
                print(f"  title    : {r.title}")
                print(f"  mimeType : {r.mimeType}")
            print()

            # =========================================================
            # 2. Read each resource by URI
            # =========================================================
            for r in resources.resources:
                result = await session.read_resource(r.uri)
                for content in result.contents:
                    print(f"[{r.name}] {content.text}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
