import asyncio


# ─── WHAT IS async for? ─────────────────────────────────────────────────────
# A regular `for` loop calls __next__() synchronously — it expects each item to be available immediately.
# `async for` is used when each item requires waiting to arrive
# — like reading a stream of responses from a server one at a time.
#
# In MCP, async for appears when iterating paginated tool lists
# or reading streamed output from a model.


async def stream_tools():
    """Simulates an MCP server sending tool definitions one at a time."""
    tools = ["weather", "calculator", "file_reader"]
    for tool in tools:
        await asyncio.sleep(0.2)        # simulate each item arriving over the network
        yield {"name": tool, "status": "ok"}


async def main():
    print("Receiving tools from server:")
    async for tool in stream_tools():   # waits for each item before continuing
        print(f"  Got: {tool}")

    # Real MCP usage:
    #
    # async for tools_page in session.list_tools():
    #     for tool in tools_page:
    #         print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())
