"""Low-level MCP server: basic prompts (stdio transport).

Demonstrates the foundational low-level server API — the boilerplate every
low-level server shares:

  - Server("name")                   create the server instance
  - @server.list_prompts()           register the list-prompts handler
  - @server.get_prompt()             register the get-prompt handler
  - InitializationOptions / NotificationOptions  capability negotiation
  - stdio_server() + server.run()    wire up the transport

FastMCP is built on top of this layer. Everything FastMCP does automatically
— schema generation, dispatch, capability negotiation — you write by hand here.
"""

import asyncio

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("basic-lowlevel-server")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """Return available prompt templates with their argument definitions."""
    return [
        types.Prompt(
            name="example-prompt",
            description="An example prompt template",
            arguments=[
                types.PromptArgument(
                    name="arg1",
                    description="Example argument",
                    required=False,
                )
            ],
        )
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """Render a prompt by name, substituting provided arguments."""
    if name != "example-prompt":
        raise ValueError(f"Unknown prompt: {name}")

    arg1_value = (arguments or {}).get("arg1", "default")

    return types.GetPromptResult(
        description="Example prompt",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Example prompt text with argument: {arg1_value}",
                ),
            )
        ],
    )


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="basic-lowlevel-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
