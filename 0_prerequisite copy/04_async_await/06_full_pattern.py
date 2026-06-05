import asyncio


# ─── FULL PATTERN ───────────────────────────────────────────────────────────
# This file combines all five async concepts into the shape of a real
# MCP client interaction. Nothing here is simulated differently from
# what you'll write when building against an actual MCP server.
#
# Concepts used:
#   async def      — every handler and helper is a coroutine
#   await          — used to call tools and wait for results
#   asyncio.run()  — the single entry point that starts everything
#   async with     — opens and closes the session safely
#   async for      — iterates the tool list from the server


# ─── Simulated MCP server tool ──────────────────────────────────────────────

async def weather_tool(city: str) -> dict:
    await asyncio.sleep(0.2)            # simulate HTTP call to weather API
    return {"city": city, "temp": 72, "condition": "sunny"}


# ─── Simulated MCP session ──────────────────────────────────────────────────

class FakeSession:
    async def __aenter__(self):
        await asyncio.sleep(0.05)
        print("[Session] open")
        return self

    async def __aexit__(self, *args):
        await asyncio.sleep(0.05)
        print("[Session] closed")

    async def call_tool(self, name: str, args: dict):
        if name == "weather":
            return await weather_tool(args["city"])

    async def list_tools(self):
        for tool in ["weather", "calculator"]:
            await asyncio.sleep(0.05)
            yield tool


# ─── Main client logic ──────────────────────────────────────────────────────

async def main():
    async with FakeSession() as session:            # async with: safe open/close

        # async for: iterate tools as they arrive from the server
        print("Available tools:")
        async for tool_name in session.list_tools():
            print(f"  - {tool_name}")

        # asyncio.gather: call multiple tools concurrently
        cities = ["New York", "London", "Tokyo"]
        results = await asyncio.gather(
            *[session.call_tool("weather", {"city": c}) for c in cities]
        )

        print("\nWeather results:")
        for r in results:
            print(f"  {r['city']}: {r['temp']}F, {r['condition']}")


# ─── Entry point ────────────────────────────────────────────────────────────
# asyncio.run() creates the event loop, runs main(), then shuts it down.
# Every MCP server and client script ends this way.

if __name__ == "__main__":
    asyncio.run(main())
