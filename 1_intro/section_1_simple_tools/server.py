"""Section 1: Simple Tools — primitive return types.

Covers:
- tool (text): double the number of servings
- tool (primitive - list[str]): list available dishes
- tool (title): get_display_name() with and without a title
- tool (Field descriptions): scale_recipe with per-param docs and defaults

Run with:
    python server.py
"""

from pydantic import Field

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RecipeHelper-SimpleTools")


# Tool (text): returns int → serialized as TextContent on the wire
@mcp.tool()
def double_servings(servings: int) -> int:
    """Double the number of servings for a recipe"""
    return servings * 2


# Tool (primitive - list[str]): FastMCP expands list into multiple TextContent items, one per element
@mcp.tool()
def list_dishes() -> list[str]:
    """List all available dishes - returns list[str]"""
    return ["pancakes", "omelette", "pasta"]


# Tool (title): title="Wine Pairing Suggester" overrides the function name in get_display_name()
@mcp.tool(title="Wine Pairing Suggester")
def suggest_wine(dish: str) -> str:
    """Suggest a wine that pairs well with a dish"""
    pairings = {
        "pancakes": "Sparkling Moscato",
        "omelette": "Sauvignon Blanc",
        "pasta": "Chianti or Pinot Grigio",
    }
    return pairings.get(dish.lower(), "Chardonnay — a safe all-rounder")


# Tool (Field descriptions): Field adds per-param description and default to the tool schema.
# Without Field, FastMCP infers parameter names only — no per-param docs or defaults appear.
# - dish has no default → required in the schema
# - servings and unit have defaults → optional in the schema
@mcp.tool()
def scale_recipe(
    dish: str = Field(description="Name of the dish to scale"),
    servings: int = Field(description="Target number of servings", default=4),
    unit: str = Field(description="Unit system: 'metric' or 'imperial'", default="metric"),
) -> str:
    """Scale a recipe to a target number of servings"""
    return f"Scaled '{dish}' to {servings} servings ({unit})"


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
