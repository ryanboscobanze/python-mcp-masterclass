"""Client for the basic low-level server (stdio transport).

demo/lowlevel_basic/client_basic.py

Exercises the two prompt protocol endpoints that server_basic.py exposes:

  session.list_prompts()              → ListPromptsResult with .prompts
  session.get_prompt(name, arguments) → GetPromptResult with .messages

Sections:
  1. Discover — list all available prompt templates and their argument metadata
  2. Render    — call get_prompt with a provided argument value
  3. Default   — call get_prompt without arguments to confirm the server default

Run from the demo directory:
    python lowlevel_basic/client_basic.py
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client

from mcp.client.stdio import stdio_client

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_basic.py")],
)


async def run() -> None:
    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://127.0.0.1:3000/mcp") as (read, write, _):    
        async with ClientSession(read, write) as session:
            await session.initialize()

            # =========================================================
            # 1. Discover available prompt templates
            # =========================================================
            prompts = await session.list_prompts()
            print("Available prompts:")
            for prompt in prompts.prompts:
                print(f"  name       : {prompt.name}")
                print(f"  description: {prompt.description}")
                if prompt.arguments:
                    for arg in prompt.arguments:
                        print(
                            f"  argument   : {arg.name!r} "
                            f"(required={arg.required}) — {arg.description}"
                        )
            print()

            # =========================================================
            # 2. Render the prompt with an explicit argument value
            # =========================================================
            print("get_prompt('example-prompt', arg1='hello'):")
            result = await session.get_prompt(
                "example-prompt", arguments={"arg1": "hello"}
            )
            print(f"  description: {result.description}")
            for msg in result.messages:
                print(f"  role       : {msg.role}")
                print(f"  text       : {msg.content.text}")
            print()

            # =========================================================
            # 3. Render with no arguments — server falls back to default
            # =========================================================
            print("get_prompt('example-prompt', no arguments):")
            result = await session.get_prompt("example-prompt")
            for msg in result.messages:
                print(f"  text: {msg.content.text}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
