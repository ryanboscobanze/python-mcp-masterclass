"""Client for the low-level pagination server (stdio transport).

Pages through all three list endpoints using PaginatedRequestParams(cursor=cursor),
then demonstrates jumping directly to a specific page without following the sequence.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import PaginatedRequestParams

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_pagination_lowlevel.py")],
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # 1. Tools — 25 total, 5 per page → 5 pages
            # =========================================================
            print("Paging through tools (5/page, 25 total):")
            all_tools = []
            cursor = None
            page_num = 0
            while True:
                page_num += 1
                result = await session.list_tools(
                    params=PaginatedRequestParams(cursor=cursor)
                )
                all_tools.extend(result.tools)
                print(
                    f"  Page {page_num}: {len(result.tools)} tools,"
                    f" nextCursor={result.nextCursor!r}"
                )
                if result.nextCursor is None:
                    break
                cursor = result.nextCursor
            print(f"  Total tools: {len(all_tools)}\n")

            # =========================================================
            # 2. Resources — 100 total, 10 per page → 10 pages
            # =========================================================
            print("Paging through resources (10/page, 100 total):")
            all_resources = []
            cursor = None
            page_num = 0
            while True:
                page_num += 1
                result = await session.list_resources(
                    params=PaginatedRequestParams(cursor=cursor)
                )
                all_resources.extend(result.resources)
                print(
                    f"  Page {page_num}: {len(result.resources)} resources,"
                    f" nextCursor={result.nextCursor!r}"
                )
                if result.nextCursor is None:
                    break
                cursor = result.nextCursor
            print(f"  Total resources: {len(all_resources)}\n")

            # =========================================================
            # 3. Prompts — 20 total, 7 per page → 3 pages
            # =========================================================
            print("Paging through prompts (7/page, 20 total):")
            all_prompts = []
            cursor = None
            page_num = 0
            while True:
                page_num += 1
                result = await session.list_prompts(
                    params=PaginatedRequestParams(cursor=cursor)
                )
                all_prompts.extend(result.prompts)
                print(
                    f"  Page {page_num}: {len(result.prompts)} prompts,"
                    f" nextCursor={result.nextCursor!r}"
                )
                if result.nextCursor is None:
                    break
                cursor = result.nextCursor
            print(f"  Total prompts: {len(all_prompts)}")

            # =========================================================
            # 4. Direct cursor jumps — resources endpoint
            # =========================================================
            print("\nDirect cursor jumps (resources):")

            result = await session.list_resources(
                params=PaginatedRequestParams(cursor=None)
            )
            print(f"  First page (cursor=None):  {[r.name for r in result.resources]}, nextCursor={result.nextCursor!r}")

            result = await session.list_resources(
                params=PaginatedRequestParams(cursor="50")
            )
            print(f"  Mid-dataset (cursor='50'): {[r.name for r in result.resources]}, nextCursor={result.nextCursor!r}")

            result = await session.list_resources(
                params=PaginatedRequestParams(cursor="90")
            )
            print(f"  Last page (cursor='90'):   {[r.name for r in result.resources]}, nextCursor={result.nextCursor!r}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
