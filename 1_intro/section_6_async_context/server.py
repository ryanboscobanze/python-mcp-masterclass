"""Section 6: Async + Context (Advanced).

Covers:
- tool (progress): generate_shopping_list — ctx.info, ctx.debug, ctx.warning, ctx.error,
  and ctx.report_progress for per-dish progress reporting
- tool (notification): add_dish — ctx.session.send_resource_list_changed() notifies clients
  that the resource list has changed (recipe://{dish} becomes live)

Run with:
    python server.py
"""

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

mcp = FastMCP("RecipeHelper-AsyncContext")

recipes: dict[str, str] = {
    "pancakes": "flour, eggs, milk, butter, baking powder, salt, sugar",
    "omelette": "eggs, butter, salt, pepper, cheese",
    "pasta": "pasta, olive oil, garlic, tomatoes, basil, parmesan",
}


# Dynamic resource: needed so add_dish can make recipe://{dish} live after adding a new dish
@mcp.resource("recipe://{dish}")
def get_ingredients(dish: str) -> str:
    """Look up the core ingredients for a dish"""
    ingredients = recipes.get(dish.lower())
    if ingredients:
        return f"Ingredients for {dish}: {ingredients}"
    return f"No recipe found for '{dish}'."


# Tool (progress): ctx methods send protocol-level notifications — separate from the tool result.
# The client must register a logging_callback (for ctx.info/warning/debug/error) and a
# progress_callback on call_tool (for ctx.report_progress) to receive them.
@mcp.tool()
async def generate_shopping_list(
    dishes: list[str],
    ctx: Context[ServerSession, None],
) -> str:
    """Generate a combined, deduplicated shopping list for a set of dishes"""
    if not dishes:
        await ctx.error("No dishes provided — shopping list cannot be generated")
        return "No dishes provided."

    await ctx.info("Building shopping list...")
    total = len(dishes)
    all_ingredients: set[str] = set()

    for i, dish in enumerate(dishes):
        await ctx.report_progress(progress=(i + 1) / total, total=1.0, message=f"Processing {dish}")
        await ctx.info(f"Processing dish {i + 1}/{total}: {dish}")
        ingredients = recipes.get(dish.lower(), "")
        if ingredients:
            for item in ingredients.split(", "):
                all_ingredients.add(item.strip())
            await ctx.debug(f"Added ingredients for {dish}")
        else:
            await ctx.warning(f"'{dish}' not found in recipes — skipping")

    sorted_list = sorted(all_ingredients)
    return "Shopping list:\n" + "\n".join(f"- {item}" for item in sorted_list)


# Tool (notification): mutates the recipes dict and fires send_resource_list_changed so clients
# know to re-fetch the resource list — recipe://{dish} is now resolvable.
@mcp.tool()
async def add_dish(
    dish: str,
    ingredients: str,
    ctx: Context[ServerSession, None],
) -> str:
    """Add a new dish to the recipe collection (makes recipe://{dish} available as a resource)"""
    recipes[dish.lower()] = ingredients
    await ctx.session.send_resource_list_changed()
    return f"Added '{dish}' to the recipe collection. Resource recipe://{dish.lower()} is now available."


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
