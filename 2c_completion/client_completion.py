"""MCP completion client example.

Run from the demo directory:
    python 2c_completion/client_completion.py

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
from mcp.types import PromptReference, ResourceTemplateReference

# Resolve server path relative to this file so it works regardless of cwd
_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_completion.py")],
)


async def run():
    """Run the completion client example."""
    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()
            print("Available prompts:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}")

            # List available resource templates
            templates = await session.list_resource_templates()
            print("\nAvailable resource templates:")
            for template in templates.resourceTemplates:
                print(f"  - {template.uriTemplate}")

            # =========================================================
            # Prompt argument completions
            # =========================================================

            if prompts.prompts:
                prompt_name = prompts.prompts[0].name
                print(f"\nCompleting arguments for prompt: {prompt_name}")

                # Complete 'language' with empty value — returns all supported languages
                result = await session.complete(
                    ref=PromptReference(type="ref/prompt", name=prompt_name),
                    argument={"name": "language", "value": ""},
                )
                print(f"  language (empty prefix): {result.completion.values}")

                # Complete 'language' with prefix "p" — filters to matching languages
                result = await session.complete(
                    ref=PromptReference(type="ref/prompt", name=prompt_name),
                    argument={"name": "language", "value": "p"},
                )
                print(f"  language starting with 'p': {result.completion.values}")

            # =========================================================
            # Resource template completions
            # =========================================================

            if templates.resourceTemplates:
                template = templates.resourceTemplates[0]
                print(f"\nCompleting arguments for resource template: {template.uriTemplate}")

                # Complete 'owner' without context — no handler matches, expect empty
                result = await session.complete(
                    ref=ResourceTemplateReference(type="ref/resource", uri=template.uriTemplate),
                    argument={"name": "owner", "value": "model"},
                )
                print(f"  owner starting with 'model' (no context): {result.completion.values}")

                # Complete 'repo' with context owner="modelcontextprotocol" — handler returns known repos
                result = await session.complete(
                    ref=ResourceTemplateReference(type="ref/resource", uri=template.uriTemplate),
                    argument={"name": "repo", "value": ""},
                    context_arguments={"owner": "modelcontextprotocol"},
                )
                print(f"  repo with owner='modelcontextprotocol': {result.completion.values}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
