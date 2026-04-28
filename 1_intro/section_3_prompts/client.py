"""Section 3 client: Prompts."""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_here = os.path.dirname(os.path.abspath(__file__))
_venv_root = os.path.dirname(os.path.dirname(_here))
_python = os.path.join(
    _venv_root, ".venv",
    "Scripts" if sys.platform == "win32" else "bin",
    "python.exe" if sys.platform == "win32" else "python",
)
server_params = StdioServerParameters(
    command=_python,
    args=[os.path.join(_here, "server.py")],
)


async def run():
    # --- TRANSPORT: uncomment one line ---
    # STDIO — server launched as subprocess, run client only:
    async with stdio_client(server_params) as (read, write):
    # ↕ TOGGLE
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available prompts
            print("\n" + "=" * 50)
            print("LIST PROMPTS")
            print("=" * 50)
            prompts = await session.list_prompts()
            print(json.dumps(prompts.model_dump(), indent=2, default=str))
            print("-" * 50)

            # --- Invocation 1: cooking_instructions ---
            # Prompt (string): returns a plain string — FastMCP wraps it in a single UserMessage
            print("\n" + "=" * 50)
            print("INVOCATION 1: cooking_instructions")
            print("=" * 50)
            prompt = await session.get_prompt(
                "cooking_instructions",
                arguments={"dish": "pancakes", "skill_level": "beginner"},
            )
            print(f"[raw result] {prompt}")
            print("-" * 50)
            messages = []
            for msg in prompt.messages:
                if isinstance(msg.content, types.TextContent):
                    messages.append(f"[{msg.role}]: {msg.content.text}")
            print(f"[string prompt] {messages}")

            # --- Invocation 2: troubleshoot_dish ---
            # Prompt (messages): returns a list of Message objects — seeds a multi-turn conversation
            print("\n" + "=" * 50)
            print("INVOCATION 2: troubleshoot_dish")
            print("=" * 50)
            prompt = await session.get_prompt(
                "troubleshoot_dish",
                arguments={"dish": "pancakes", "problem": "they came out flat and rubbery"},
            )
            print(f"[raw result] {prompt}")
            print("-" * 50)
            messages = []
            for msg in prompt.messages:
                if isinstance(msg.content, types.TextContent):
                    messages.append(f"[{msg.role}]: {msg.content.text}")
            print(f"[multi-turn messages] {messages}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
