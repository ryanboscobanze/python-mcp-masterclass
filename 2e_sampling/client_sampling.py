"""MCP sampling client example.

Demonstrates the client-side sampling callback: when a tool on the server calls
ctx.session.create_message(), MCP routes the request back to this process via the
sampling_callback.  In production the callback would forward the prompt to a real
LLM; here we return a simulated reply so the demo runs without API keys.

Run from the demo directory:
    python 2e_sampling/client_sampling.py

Transport:
    stdio (default)       — client spawns the server; run this file only
    streamable-http       — start the server first, then run this file
                            Uncomment the streamable_http_client line below
                            and comment out the stdio_client line.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CreateMessageResult, TextContent

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_sampling.py")],
)


async def sampling_handler(context, params) -> CreateMessageResult:
    """Handle sampling requests from the server.

    Receives the prompt the server assembled, simulates an LLM response, and
    returns a CreateMessageResult.  In production, replace the body with a call
    to your real LLM (e.g. anthropic.messages.create).
    """
    prompt_text = ""
    for msg in params.messages:
        if hasattr(msg.content, "text"):
            prompt_text = msg.content.text
            break

    print(f"  [sampling_handler] prompt   : {prompt_text!r}")
    print(f"  [sampling_handler] max_tokens: {params.maxTokens}")

    simulated_response = (
        "[Simulated LLM reply]\n"
        "Roses are red,\n"
        "Violets are blue,\n"
        "Sampling works,\n"
        "And so do you!"
    )

    return CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text=simulated_response),
        model="simulated-model",
        stopReason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write, sampling_callback=sampling_handler) as session:
            await session.initialize()

            # =========================================================
            # Discover available tools
            # =========================================================
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # =========================================================
            # generate_poem — basic sampling round-trip
            # =========================================================
            print("\n--- generate_poem('autumn') ---")
            result = await session.call_tool("generate_poem", {"topic": "autumn"})
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

            print("\n--- generate_poem('the ocean') ---")
            result = await session.call_tool("generate_poem", {"topic": "the ocean"})
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

            # =========================================================
            # translate — shows a different tool using its own token budget
            # =========================================================
            print("\n--- translate('Hello, world!', 'Spanish') ---")
            result = await session.call_tool(
                "translate", {"text": "Hello, world!", "language": "Spanish"}
            )
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
