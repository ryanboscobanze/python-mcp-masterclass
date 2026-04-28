"""Section 2: Resources — static and dynamic resources.

Covers:
- static resource: fixed cooking measurement conversions (kitchen://conversions)
- dynamic resource: fetch ingredient list by dish name (recipe://{dish})

Run with:
    python server.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RecipeHelper-Resources")

recipes: dict[str, str] = {
    "pancakes": "flour, eggs, milk, butter, baking powder, salt, sugar",
    "omelette": "eggs, butter, salt, pepper, cheese",
    "pasta": "pasta, olive oil, garlic, tomatoes, basil, parmesan",
}


# Static resource: fixed URI, no parameters — always returns the same content
@mcp.resource("kitchen://conversions")
def cooking_conversions() -> str:
    """Common cooking measurement conversions"""
    return """Common Cooking Conversions:
    - 1 cup = 240 ml
    - 1 tablespoon = 15 ml
    - 1 teaspoon = 5 ml
    - 1 ounce = 28 g
    - 1 pound = 450 g
    - 350°F = 175°C (moderate oven)
    - 400°F = 200°C (hot oven)
    """


# Dynamic resource: URI template with {dish} parameter — content varies by dish
@mcp.resource("recipe://{dish}")
def get_ingredients(dish: str) -> str:
    """Look up the core ingredients for a dish"""
    ingredients = recipes.get(dish.lower())
    if ingredients:
        return f"Ingredients for {dish}: {ingredients}"
    return f"No recipe found for '{dish}'. Try: pancakes, omelette, or pasta."


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
