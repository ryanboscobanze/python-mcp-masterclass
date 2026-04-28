"""Section 4: Structured Return Types.

Every tool result has two layers: content (the text wire representation) and
structuredContent (a typed dict). FastMCP populates structuredContent whenever
it can derive a JSON schema from the return type annotation. When it can't,
structuredContent is None and content degrades to a memory address string.

Six tools demonstrate exactly when each layer works and when it doesn't:
- NutritionInfo (BaseModel)            → schema from field annotations, both layers populated
- CookingTime (TypedDict)              → schema from field annotations, both layers populated
- get_macro_ratios (dict[str, float])  → generic schema, both layers populated
- DishRating (plain class + annotations) → schema generated, structuredContent works, content is a memory address
- IngredientSubstitute (@dataclass)    → schema generated, both layers populated (content is proper JSON)
- RecipeNote (plain class, no annotations) → no schema, structuredContent=None, content is a memory address

Run with:
    python server.py
"""

from dataclasses import dataclass
from typing import TypedDict

from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RecipeHelper-StructuredReturns")


# Tool (structured - Pydantic): BaseModel → FastMCP generates JSON schema, populates structuredContent
class NutritionInfo(BaseModel):
    dish: str
    calories: float
    protein_g: float
    carbs_g: float


@mcp.tool()
def get_nutrition(dish: str) -> NutritionInfo:
    """Get basic nutrition info for a dish"""
    data = {
        "pancakes": NutritionInfo(dish="pancakes", calories=350, protein_g=8, carbs_g=45),
        "omelette": NutritionInfo(dish="omelette", calories=220, protein_g=15, carbs_g=2),
        "pasta": NutritionInfo(dish="pasta", calories=450, protein_g=14, carbs_g=68),
    }
    return data.get(dish.lower(), NutritionInfo(dish=dish, calories=0, protein_g=0, carbs_g=0))


# Tool (structured - TypedDict): TypedDict → FastMCP generates JSON schema, populates structuredContent
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


# Tool (structured - dict[str, float]): typed dict → FastMCP generates JSON schema, populates structuredContent
@mcp.tool()
def get_macro_ratios(dish: str) -> dict[str, float]:
    """Get macronutrient ratio percentages for a dish - returns dict[str, float]"""
    data = {
        "pancakes": {"carbs_pct": 0.51, "protein_pct": 0.09, "fat_pct": 0.40},
        "omelette": {"carbs_pct": 0.04, "protein_pct": 0.27, "fat_pct": 0.69},
        "pasta": {"carbs_pct": 0.60, "protein_pct": 0.12, "fat_pct": 0.28},
    }
    return data.get(dish.lower(), {"carbs_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0})


# Tool (plain class + annotations): class-level annotations → FastMCP generates schema, structuredContent populated
# pydantic_core cannot serialize a plain class instance → content falls back to a memory address string
class DishRating:
    dish: str
    score: int
    reviewer: str

    def __init__(self, dish: str, score: int, reviewer: str):
        self.dish = dish
        self.score = score
        self.reviewer = reviewer


@mcp.tool()
def get_dish_rating(dish: str) -> DishRating:
    """Get a crowd-sourced rating for a dish — returns plain class with class-level annotations"""
    ratings = {
        "pancakes": DishRating(dish="pancakes", score=8, reviewer="chef_ai"),
        "omelette": DishRating(dish="omelette", score=9, reviewer="chef_ai"),
        "pasta": DishRating(dish="pasta", score=7, reviewer="chef_ai"),
    }
    return ratings.get(dish.lower(), DishRating(dish=dish, score=0, reviewer="unknown"))


# Tool (dataclass): @dataclass generates __init__ from class annotations
# FastMCP uses those same annotations to generate the schema — both layers populated
# pydantic_core natively serializes dataclasses → content is proper JSON (unlike plain class above)
@dataclass
class IngredientSubstitute:
    original: str
    substitute: str
    ratio: str


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


# Tool (structured - class WITHOUT type hints): only __init__ params, no class-level annotations
# FastMCP cannot build a JSON schema → structuredContent=None, falls back to TextContent only.
# str() of the object gives the default memory address representation.
class RecipeNote:
    def __init__(self, dish, note):
        self.dish = dish
        self.note = note


@mcp.tool()
def get_recipe_note(dish: str) -> RecipeNote:
    """Get a note for a dish — class WITHOUT type hints returns unstructured output, no schema generated"""
    notes = {
        "pancakes": RecipeNote("pancakes", "Best served immediately with maple syrup"),
        "omelette": RecipeNote("omelette", "Use a non-stick pan for best results"),
        "pasta": RecipeNote("pasta", "Salt the water generously before boiling"),
    }
    return notes.get(dish.lower(), RecipeNote(dish, "No note available"))


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
