"""MCP sampling server example (stdio transport).

Demonstrates server-initiated sampling: the server uses ctx.session.create_message()
to request an LLM completion from the client, then returns the result as a tool
response.  The client supplies a sampling callback — in production this would call
a real LLM; in these examples it returns a simulated reply.

Two tools are registered to exercise different sampling scenarios:
- generate_poem(topic)      single user message, max_tokens=100
- translate(text, language) single user message, max_tokens=50
                            shows that the token budget is tool-controlled

"""

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import SamplingMessage, TextContent

mcp = FastMCP(name="SamplingExample")


@mcp.tool()
async def generate_poem(topic: str, ctx: Context[ServerSession, None]) -> str:
    """Generate a poem about the given topic using LLM sampling."""
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=f"Write a short poem about {topic}"),
            )
        ],
        max_tokens=100,
    )
    if result.content.type == "text":
        return result.content.text
    return str(result.content)


@mcp.tool()
async def translate(text: str, language: str, ctx: Context[ServerSession, None]) -> str:
    """Translate text into the given language using LLM sampling."""
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Translate the following text to {language}: {text}",
                ),
            )
        ],
        max_tokens=50,
    )
    if result.content.type == "text":
        return result.content.text
    return str(result.content)


if __name__ == "__main__":
    mcp.run(transport="stdio")
    # mcp.run(transport="streamable-http")
