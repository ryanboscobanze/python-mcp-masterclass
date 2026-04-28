"""Section 3: Prompts — string and multi-turn message prompts.

Covers:
- prompt (string): cooking_instructions — returns a single string message
- prompt (messages): troubleshoot_dish — returns a list of user/assistant messages

Run with:
    python server.py
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("RecipeHelper-Prompts")


# Prompt (string): returns a plain string — FastMCP wraps it in a single UserMessage
@mcp.prompt()
def cooking_instructions(dish: str, skill_level: str = "beginner") -> str:
    """Generate a prompt for writing recipe instructions at a given skill level"""
    tone = {
        "beginner": "Use simple language and explain each step in detail",
        "intermediate": "Assume basic kitchen knowledge and focus on technique",
        "advanced": "Use culinary terminology and emphasize precision and timing",
    }
    guidance = tone.get(skill_level, tone["beginner"])
    return f"{guidance}. Write clear, step-by-step cooking instructions for {dish}."


# Prompt (messages): returns a list of Message objects — seeds a multi-turn conversation
@mcp.prompt()
def troubleshoot_dish(dish: str, problem: str) -> list[base.Message]:
    """Start a multi-turn troubleshooting conversation for a dish that went wrong"""
    return [
        base.UserMessage(f"My {dish} didn't turn out right. Here's what happened: {problem}"),
        base.AssistantMessage("I can help troubleshoot that. Can you walk me through your process step by step?"),
    ]


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
