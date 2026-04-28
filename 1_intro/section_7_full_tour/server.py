"""Section 7: Full Tour — all six concept sections in one server.

Combines every concept from sections 1–6 into a single server file:

Section 1 — Simple Tools (primitive return types):
- tool (text): double_servings
- tool (primitive - list[str]): list_dishes
- tool (title): suggest_wine
- tool (Field descriptions): scale_recipe

Section 2 — Resources:
- static resource: kitchen://conversions
- dynamic resource: recipe://{dish}

Section 3 — Prompts:
- prompt (string): cooking_instructions
- prompt (messages): troubleshoot_dish

Section 4 — Structured Return Types:
- tool (structured - Pydantic): get_nutrition
- tool (structured - TypedDict): get_cooking_time
- tool (structured - dict[str, float]): get_macro_ratios
- tool (structured - class with type hints): get_substitute
- tool (structured - class WITHOUT type hints): get_recipe_note

Section 5 — CallToolResult Patterns:
- tool (error): check_pantry
- tool (embedded resource): get_recipe_card
- tool (image - CallToolResult): generate_serving_chart
- tool (image - FastMCP Image): create_recipe_label
- tool (CallToolResult + _meta): get_dish_info
- tool (empty CallToolResult): clear_added_dishes
- tool (Annotated[CallToolResult, Model]): get_validated_macros

Section 6 — Async + Context:
- tool (progress): generate_shopping_list
- tool (notification): add_dish

Run with:
    python server.py
"""

import base64
import io

from PIL import Image as PILImage, ImageDraw
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP, Image, Context
from mcp.server.session import ServerSession
from mcp.server.fastmcp.prompts import base
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
    TextResourceContents,
)

# STDIO (default): no extra flags needed
mcp = FastMCP("RecipeHelper-FullTour")
# HTTP: add json_response=True so the server returns JSON bodies instead of SSE streams.
# Required when the client uses streamable_http_client — without it the client cannot parse responses.
# mcp = FastMCP("RecipeHelper-FullTour", json_response=True)

recipes: dict[str, str] = {
    "pancakes": "flour, eggs, milk, butter, baking powder, salt, sugar",
    "omelette": "eggs, butter, salt, pepper, cheese",
    "pasta": "pasta, olive oil, garlic, tomatoes, basil, parmesan",
}


# =============================================================================
# Section 1: Simple Tools
# =============================================================================

@mcp.tool()
def double_servings(servings: int) -> int:
    """Double the number of servings for a recipe"""
    return servings * 2


@mcp.tool()
def list_dishes() -> list[str]:
    """List all available dishes - returns list[str]"""
    return ["pancakes", "omelette", "pasta"]


@mcp.tool(title="Wine Pairing Suggester")
def suggest_wine(dish: str) -> str:
    """Suggest a wine that pairs well with a dish"""
    pairings = {
        "pancakes": "Sparkling Moscato",
        "omelette": "Sauvignon Blanc",
        "pasta": "Chianti or Pinot Grigio",
    }
    return pairings.get(dish.lower(), "Chardonnay — a safe all-rounder")


@mcp.tool()
def scale_recipe(
    dish: str = Field(description="Name of the dish to scale"),
    servings: int = Field(description="Target number of servings", default=4),
    unit: str = Field(description="Unit system: 'metric' or 'imperial'", default="metric"),
) -> str:
    """Scale a recipe to a target number of servings"""
    return f"Scaled '{dish}' to {servings} servings ({unit})"


# =============================================================================
# Section 2: Resources
# =============================================================================

@mcp.resource("kitchen://conversions")
def get_conversions() -> str:
    """Get common cooking measurement conversions"""
    return """Common Cooking Conversions:
    - 1 cup = 240 ml
    - 1 tablespoon = 15 ml
    - 1 teaspoon = 5 ml
    - 1 ounce = 28 g
    - 1 pound = 450 g
    - 350°F = 175°C (moderate oven)
    - 400°F = 200°C (hot oven)
    """


@mcp.resource("recipe://{dish}")
def get_ingredients(dish: str) -> str:
    """Look up the core ingredients for a dish"""
    ingredients = recipes.get(dish.lower())
    if ingredients:
        return f"Ingredients for {dish}: {ingredients}"
    return f"No recipe found for '{dish}'. Try: pancakes, omelette, or pasta."


# =============================================================================
# Section 3: Prompts
# =============================================================================

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


@mcp.prompt()
def troubleshoot_dish(dish: str, problem: str) -> list[base.Message]:
    """Start a multi-turn troubleshooting conversation for a dish that went wrong"""
    return [
        base.UserMessage(f"My {dish} didn't turn out right. Here's what happened: {problem}"),
        base.AssistantMessage("I can help troubleshoot that. Can you walk me through your process step by step?"),
    ]


# =============================================================================
# Section 4: Structured Return Types
# =============================================================================

class NutritionInfo(BaseModel):
    dish: str
    calories: int
    protein_g: int
    carbs_g: int


@mcp.tool()
def get_nutrition(dish: str) -> NutritionInfo:
    """Get basic nutrition info for a dish"""
    data = {
        "pancakes": NutritionInfo(dish="pancakes", calories=350, protein_g=8, carbs_g=45),
        "omelette": NutritionInfo(dish="omelette", calories=220, protein_g=15, carbs_g=2),
        "pasta": NutritionInfo(dish="pasta", calories=450, protein_g=14, carbs_g=68),
    }
    return data.get(dish.lower(), NutritionInfo(dish=dish, calories=0, protein_g=0, carbs_g=0))


class CookingTime(TypedDict):
    prep_minutes: int
    cook_minutes: int
    total_minutes: int


@mcp.tool()
def get_cooking_time(dish: str) -> CookingTime:
    """Get estimated cooking time for a dish - returns TypedDict"""
    times = {
        "pancakes": CookingTime(prep_minutes=5, cook_minutes=15, total_minutes=20),
        "omelette": CookingTime(prep_minutes=3, cook_minutes=5, total_minutes=8),
        "pasta": CookingTime(prep_minutes=5, cook_minutes=20, total_minutes=25),
    }
    return times.get(dish.lower(), CookingTime(prep_minutes=0, cook_minutes=0, total_minutes=0))


@mcp.tool()
def get_macro_ratios(dish: str) -> dict[str, float]:
    """Get macronutrient ratio percentages for a dish - returns dict[str, float]"""
    data = {
        "pancakes": {"carbs_pct": 0.51, "protein_pct": 0.09, "fat_pct": 0.40},
        "omelette": {"carbs_pct": 0.04, "protein_pct": 0.27, "fat_pct": 0.69},
        "pasta": {"carbs_pct": 0.60, "protein_pct": 0.12, "fat_pct": 0.28},
    }
    return data.get(dish.lower(), {"carbs_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0})


class IngredientSubstitute:
    original: str
    substitute: str
    ratio: str

    def __init__(self, original: str, substitute: str, ratio: str):
        self.original = original
        self.substitute = substitute
        self.ratio = ratio


@mcp.tool()
def get_substitute(ingredient: str) -> IngredientSubstitute:
    """Get a baking substitute for an ingredient - returns class with type hints"""
    substitutes = {
        "butter": IngredientSubstitute(original="butter", substitute="coconut oil", ratio="1:1"),
        "eggs": IngredientSubstitute(original="eggs", substitute="flax egg", ratio="1 tbsp flaxseed + 3 tbsp water per egg"),
        "milk": IngredientSubstitute(original="milk", substitute="oat milk", ratio="1:1"),
    }
    return substitutes.get(
        ingredient.lower(),
        IngredientSubstitute(original=ingredient, substitute="no substitute found", ratio="N/A"),
    )


class RecipeNote:
    def __init__(self, dish, note):
        self.dish = dish
        self.note = note


@mcp.tool()
def get_recipe_note(dish: str) -> RecipeNote:
    """Get a note for a dish — class WITHOUT type hints returns unstructured output"""
    notes = {
        "pancakes": RecipeNote("pancakes", "Best served immediately with maple syrup"),
        "omelette": RecipeNote("omelette", "Use a non-stick pan for best results"),
        "pasta": RecipeNote("pasta", "Salt the water generously before boiling"),
    }
    return notes.get(dish.lower(), RecipeNote(dish, "No note available"))


# =============================================================================
# Section 5: CallToolResult Patterns
# =============================================================================

@mcp.tool()
def check_pantry(ingredient: str) -> CallToolResult:
    """Check if an ingredient is available in the pantry"""
    pantry = {"flour", "eggs", "butter", "salt", "pepper", "olive oil", "garlic"}
    if ingredient.lower() not in pantry:
        return CallToolResult(
            content=[TextContent(type="text", text=f"'{ingredient}' is not in the pantry!")],
            isError=True,
        )
    return CallToolResult(
        content=[TextContent(type="text", text=f"'{ingredient}' is available in the pantry.")]
    )


@mcp.tool()
def get_recipe_card(dish: str) -> CallToolResult:
    """Return a recipe card as an embedded resource"""
    cards = {
        "pancakes": "Mix flour, eggs, milk. Cook on hot griddle until bubbles form. Flip once.",
        "omelette": "Whisk eggs with salt. Melt butter in pan. Add eggs, fold over filling.",
        "pasta": "Boil salted water. Cook pasta al dente. Toss with sauce and parmesan.",
    }
    text = cards.get(dish.lower(), f"No recipe card found for {dish}.")
    return CallToolResult(
        content=[
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=f"file:///recipes/{dish}.txt",
                    mimeType="text/plain",
                    text=text,
                ),
            )
        ]
    )

@mcp.tool()
def generate_serving_chart(servings: int) -> CallToolResult:
    """Generate a placeholder chart image for the given number of servings"""
    minimal_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return CallToolResult(
        content=[
            ImageContent(
                type="image",
                data=base64.b64encode(minimal_png).decode("utf-8"),
                mimeType="image/png",
            )
        ]
    )


@mcp.tool()
def create_recipe_label(dish: str) -> Image:
    """Create a simple recipe label image for a dish using the FastMCP Image class"""
    width, height = 200, 80
    img = PILImage.new("RGB", (width, height), color="darkgreen")
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, width - 5, height - 5], outline="white", width=2)
    draw.text((width // 2 - len(dish) * 4, height // 2 - 8), dish.upper(), fill="white")
    draw.text((width // 2 - 30, height // 2 + 6), "Recipe Label", fill="lightyellow")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return Image(data=buffer.getvalue(), format="png")


@mcp.tool()
def get_dish_info(dish: str) -> CallToolResult:
    """Return dish description; _meta carries client-only metadata not visible to the model."""
    info = {
        "pancakes": ("A classic breakfast stack", "breakfast", "easy"),
        "omelette": ("A fluffy egg dish", "breakfast", "easy"),
        "pasta": ("An Italian staple", "dinner", "medium"),
    }
    description, category, difficulty = info.get(
        dish.lower(), (f"No info found for '{dish}'", "unknown", "unknown")
    )
    return CallToolResult(
        content=[TextContent(type="text", text=description)],
        _meta={"category": category, "difficulty": difficulty, "source": "recipe_db"},
    )


@mcp.tool()
def clear_added_dishes() -> CallToolResult:
    """Remove all dynamically added dishes and return empty content as a completion signal."""
    base_dishes = {"pancakes", "omelette", "pasta"}
    removed = [dish for dish in list(recipes.keys()) if dish not in base_dishes]
    for dish in removed:
        del recipes[dish]
    return CallToolResult(content=[])


class MacroSummary(BaseModel):
    dish: str
    dominant_macro: str
    balance_score: float


@mcp.tool()
def get_validated_macros(dish: str) -> Annotated[CallToolResult, MacroSummary]:
    """Return macro summary; FastMCP validates structuredContent against MacroSummary."""
    summaries = {
        "pancakes": ("carbs", 0.62),
        "omelette": ("fat", 0.78),
        "pasta": ("carbs", 0.71),
    }
    dominant, score = summaries.get(dish.lower(), ("unknown", 0.0))
    return CallToolResult(
        content=[TextContent(type="text", text=f"{dish} is dominated by {dominant} ({score:.0%})")],
        structuredContent={"dish": dish, "dominant_macro": dominant, "balance_score": score},
        _meta={"computed_from": "get_macro_ratios"},
    )


# =============================================================================
# Section 6: Async + Context
# =============================================================================

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
