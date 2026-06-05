# ─── FULL STACK — PYDANTIC + STARLETTE + UVICORN ────────────────────────────
#
# This file shows the complete HTTP stack in the shape of a real MCP tool
# endpoint: Pydantic validates data, Starlette handles routing, uvicorn serves.
#
# Run with: uvicorn 06_full_stack:app --reload
# Test with: curl -X POST http://localhost:8080/weather \
#              -H "Content-Type: application/json" \
#              -d '{"city": "London", "units": "celsius"}'

from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


# ─── PYDANTIC MODELS ─────────────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    city:  str = Field(description="City to get weather for")
    units: str = Field(default="celsius", description="celsius or fahrenheit")


class WeatherResponse(BaseModel):
    city:        str
    temperature: float
    units:       str
    condition:   str


# ─── TOOL LOGIC ───────────────────────────────────────────────────────────────

async def get_weather_logic(city: str, units: str) -> WeatherResponse:
    # In production: async HTTP call to a weather API
    temp = 65.3 if units == "fahrenheit" else 18.5
    return WeatherResponse(city=city, temperature=temp, units=units, condition="cloudy")


# ─── STARLETTE ROUTE HANDLERS ─────────────────────────────────────────────────

async def weather_endpoint(request: Request) -> JSONResponse:
    body = await request.json()

    # Pydantic validates the incoming JSON — returns 422 if invalid
    try:
        params = WeatherRequest.model_validate(body)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=422)

    result = await get_weather_logic(params.city, params.units)

    # Pydantic serialises the response to a dict
    return JSONResponse(result.model_dump())


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ─── STARLETTE APP ────────────────────────────────────────────────────────────

app = Starlette(
    routes=[
        Route("/weather", weather_endpoint, methods=["POST"]),
        Route("/health",  health),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    ],
)


# ─── TEST WITHOUT UVICORN ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    client = TestClient(app)

    # Valid request
    response = client.post("/weather", json={"city": "London", "units": "celsius"})
    print("Status:", response.status_code)
    print("Body:  ", json.dumps(response.json(), indent=2))

    # Missing required field — Pydantic catches it
    response2 = client.post("/weather", json={"units": "celsius"})
    print("\nMissing city — Status:", response2.status_code)
    print("Error:", response2.json()["error"][:80])

    # Health check
    print("\nHealth:", client.get("/health").json())

    print("\nTo run with uvicorn:")
    print("  uvicorn 06_full_stack:app --reload --port 8080")


# ─── HOW THIS MAPS TO AN ACTUAL FASTMCP SERVER ───────────────────────────────
#
# In FastMCP you don't write any of the Starlette or routing code by hand.
# FastMCP generates it for you from your tool functions:
#
#   from mcp.server.fastmcp import FastMCP
#
#   mcp = FastMCP("weather_server", host="0.0.0.0", port=8080)
#
#   @mcp.tool()
#   async def get_weather(city: str, units: str = "celsius") -> WeatherResponse:
#       return await get_weather_logic(city, units)
#
#   if __name__ == "__main__":
#       mcp.run(transport="sse")
#
# FastMCP does:
#   1. Uses Pydantic to validate inputs before calling your function
#   2. Creates a Starlette app with /sse and /messages/ routes
#   3. Serves it with uvicorn (via uvicorn.Config + uvicorn.Server)
