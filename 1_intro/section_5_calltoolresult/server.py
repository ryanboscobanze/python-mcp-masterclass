"""Section 5: CallToolResult Patterns.

CallToolResult is the protocol-level envelope every tool response is wrapped in.
It holds a list of content items (TextContent, ImageContent, EmbeddedResource)
plus optional flags: isError, _meta, structuredContent.

Covers:
- tool (error): check_pantry — isError=True when ingredient not found
- tool (embedded resource): get_recipe_card — EmbeddedResource bundled inside the tool response
- tool (image - CallToolResult): generate_serving_chart — ImageContent via raw CallToolResult
- tool (image - FastMCP Image): create_recipe_label — Image return type (simpler server API)
- tool (CallToolResult + _meta): get_dish_info — client-only metadata in _meta
- tool (empty CallToolResult): clear_added_dishes — empty content list as acknowledgment
- tool (Annotated[CallToolResult, Model]): get_validated_macros — FastMCP validates structuredContent

Run with:
    python server.py
"""

import base64
import io
from typing import Annotated

from PIL import Image as PILImage, ImageDraw
from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
    TextResourceContents,
)

mcp = FastMCP("RecipeHelper-CallToolResult")

recipes: dict[str, str] = {
    "pancakes": "flour, eggs, milk, butter, baking powder, salt, sugar",
    "omelette": "eggs, butter, salt, pepper, cheese",
    "pasta": "pasta, olive oil, garlic, tomatoes, basil, parmesan",
}


# Tool (error): return isError=True to signal a tool-level error without raising an exception
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


# Tool (embedded resource): bundle a full resource (URI + mimeType + data) inside the tool response.
# The client receives the resource content directly — no separate read_resource fetch needed.
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


# Tool (image - CallToolResult): manually wrap ImageContent in CallToolResult
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


# Tool (image - FastMCP Image): return Image directly — FastMCP serializes to ImageContent.
# Simpler server API than manually wrapping ImageContent in CallToolResult.
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


# Tool (CallToolResult + _meta): _meta is client-only — not fed to the AI model.
# Use it for UI hints, caching keys, audit info — anything the app needs but the model shouldn't see.
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


# Tool (empty CallToolResult): empty content list signals acknowledgment with no data to return
@mcp.tool()
def clear_added_dishes() -> CallToolResult:
    """Remove all dynamically added dishes and return empty content as a completion signal."""
    base_dishes = {"pancakes", "omelette", "pasta"}
    removed = [dish for dish in list(recipes.keys()) if dish not in base_dishes]
    for dish in removed:
        del recipes[dish]
    return CallToolResult(content=[])


# Pydantic model used to validate structuredContent in get_validated_macros
class MacroSummary(BaseModel):
    dish: str
    dominant_macro: str
    balance_score: float


# Tool (Annotated[CallToolResult, Model]): FastMCP validates structuredContent against MacroSummary
@mcp.tool()
def get_validated_macros(dish: str) -> Annotated[CallToolResult, MacroSummary]:
    """Return macro summary; FastMCP validates structuredContent against MacroSummary at the schema level."""
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


if __name__ == "__main__":
    # STDIO — client launches this as a subprocess (default):
    mcp.run(transport="stdio")
    # HTTP — run this in a separate terminal, then run the client:
    # mcp.run(transport="streamable-http")
