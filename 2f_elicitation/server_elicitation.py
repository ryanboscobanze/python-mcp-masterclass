"""MCP elicitation server example (stdio transport).
2f_elicitation/server_elicitation.py

Demonstrates the two elicitation patterns servers can use:

1. Form mode  — ctx.elicit(message, schema=PydanticModel)
   Sends a structured JSON-schema form to the client and waits for the
   user to fill it in.  Used for non-sensitive, structured input.

2. URL mode   — ctx.elicit_url(message, url, elicitation_id)
   Directs the client to open an external URL (OAuth, payment, etc.)
   and waits for the user to complete the out-of-band flow.

3. Error-raise pattern — raise UrlElicitationRequiredError(...)
   Alternative to ctx.elicit_url(): the server raises an exception that
   the MCP framework converts to a -32042 JSON-RPC error.  The client
   catches it via McpError and handles the elicitation manually.

4. Completion notification — ctx.session.send_elicit_complete(elicitation_id)
   After a URL-mode elicitation (pattern 2 or 3) finishes out-of-band,
   a separate tool call notifies the client via
   notifications/elicitation/complete so it can retry or update UI.

Tools:
  book_table             — form elicitation; two-field schema (bool + str)
  pick_color             — form elicitation; enum-constrained field via json_schema_extra
  adjust_booking         — form elicitation; int + float numeric fields
  secure_payment         — URL elicitation via ctx.elicit_url()
  connect_service        — URL elicitation via UrlElicitationRequiredError (single)
  connect_multi_service  — URL elicitation via UrlElicitationRequiredError (multiple)
  oauth_complete         — send_elicit_complete paired with error-raise pattern
  payment_webhook        — send_elicit_complete paired with elicit_url pattern
  test_scheme_validation — sends ftp:// URL to trigger client scheme validation

Run from the mcp_revamp directory:
    python 2f_elicitation/server_elicitation.py
"""

import uuid

from pydantic import BaseModel, Field

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.shared.exceptions import UrlElicitationRequiredError
from mcp.types import ElicitRequestURLParams

mcp = FastMCP(name="Elicitation Example")


class BookingPreferences(BaseModel):
    """Schema for collecting user preferences — two-field form (bool + str)."""

    checkAlternative: bool = Field(description="Would you like to check another date?")
    alternativeDate: str = Field(
        default="",
        description="Alternative date to book (YYYY-MM-DD), leave blank if not checking",
    )


@mcp.tool()
async def book_table(date: str, time: str, party_size: int, ctx: Context[ServerSession, None]) -> str:
    """Book a table with date availability check.

    Demonstrates form mode elicitation (ctx.elicit) for collecting
    non-sensitive structured user input when the requested date is
    unavailable.
    """
    if date == "2024-12-25":
        result = await ctx.elicit(
            message=(f"No tables available for {party_size} on {date}. Would you like to try another date?"),
            schema=BookingPreferences,
        )

        if result.action == "accept" and result.data:
            if result.data.checkAlternative and result.data.alternativeDate:
                return f"[SUCCESS] Booked for {result.data.alternativeDate}"
            return "[CANCELLED] No booking made"
        return "[CANCELLED] Booking cancelled"

    return f"[SUCCESS] Booked for {date} at {time}"


class ColorPreference(BaseModel):
    """Schema for a constrained choice — demonstrates enum fields in form mode."""

    color: str = Field(
        description="Pick your favourite color",
        json_schema_extra={"enum": ["red", "green", "blue", "yellow"]},
    )


@mcp.tool()
async def pick_color(ctx: Context[ServerSession, None]) -> str:
    """Pick a color from a constrained list.

    Demonstrates json_schema_extra={"enum": [...]} in a Pydantic field.
    The client receives enum constraints in requestedSchema and can render
    them as a dropdown or radio buttons rather than a free-text input.
    """
    result = await ctx.elicit(message="Choose a color:", schema=ColorPreference)
    if result.action == "accept" and result.data:
        return f"You picked: {result.data.color}"
    return "No color selected"


class BudgetPreferences(BaseModel):
    """Schema demonstrating int and float fields in form mode.

    ElicitResult.content type union: str | int | float | bool | list[str] | None.
    """

    guest_count: int = Field(
        default=2,
        description="Number of guests (1-10)",
    )
    max_budget: float = Field(
        default=50.0,
        description="Maximum budget per person in USD",
    )


@mcp.tool()
async def adjust_booking(booking_ref: str, ctx: Context[ServerSession, None]) -> str:
    """Adjust a booking by eliciting updated guest count and budget.

    Demonstrates int and float fields in form-mode elicitation schema.
    The client sends numeric values in ElicitResult.content; the server
    accesses them via result.data (Pydantic model) with correct Python types.
    """
    result = await ctx.elicit(
        message=f"Update booking {booking_ref}: enter guest count and max budget per person",
        schema=BudgetPreferences,
    )
    if result.action == "accept" and result.data:
        return f"[UPDATED] {result.data.guest_count} guests @ ${result.data.max_budget:.2f}/person"
    return "[CANCELLED] Booking not updated"


@mcp.tool()
async def secure_payment(amount: float, ctx: Context[ServerSession, None]) -> str:
    """Process a secure payment requiring URL confirmation.

    Demonstrates URL mode elicitation via ctx.elicit_url() for operations
    that require out-of-band user interaction (e.g. payment confirmation).
    """
    elicitation_id = str(uuid.uuid4())

    result = await ctx.elicit_url(
        message=f"Please confirm payment of ${amount:.2f}",
        url=f"https://payments.example.com/confirm?amount={amount}&id={elicitation_id}",
        elicitation_id=elicitation_id,
    )

    if result.action == "accept":
        return f"Payment of ${amount:.2f} initiated - check your browser to complete"
    elif result.action == "decline":
        return "Payment declined by user"
    return "Payment cancelled"


@mcp.tool()
async def connect_service(service_name: str) -> str:
    """Connect to a third-party service requiring OAuth authorization.

    Demonstrates the error-raise pattern: the server raises
    UrlElicitationRequiredError instead of calling ctx.elicit_url().
    The MCP framework converts this to a -32042 JSON-RPC error that
    the client catches via McpError.
    """
    elicitation_id = str(uuid.uuid4())

    raise UrlElicitationRequiredError(
        [
            ElicitRequestURLParams(
                mode="url",
                message=f"Authorization required to connect to {service_name}",
                url=f"https://{service_name}.example.com/oauth/authorize?elicit={elicitation_id}",
                elicitationId=elicitation_id,
            )
        ]
    )


@mcp.tool()
async def connect_multi_service() -> str:
    """Connect to multiple services requiring OAuth simultaneously.

    Demonstrates passing multiple ElicitRequestURLParams to UrlElicitationRequiredError.
    The client receives all elicitations in url_error.elicitations and must
    handle each — not just the first.  Compare with connect_service which
    passes a single-item list.
    """
    github_id = str(uuid.uuid4())
    slack_id = str(uuid.uuid4())

    raise UrlElicitationRequiredError(
        [
            ElicitRequestURLParams(
                mode="url",
                message="Authorization required: connect GitHub",
                url=f"https://github.example.com/oauth/authorize?elicit={github_id}",
                elicitationId=github_id,
            ),
            ElicitRequestURLParams(
                mode="url",
                message="Authorization required: connect Slack",
                url=f"https://slack.example.com/oauth/authorize?elicit={slack_id}",
                elicitationId=slack_id,
            ),
        ]
    )


@mcp.tool()
async def oauth_complete(service_name: str, elicitation_id: str, ctx: Context[ServerSession, None]) -> str:
    """Signal that an out-of-band OAuth flow has completed.

    Demonstrates send_elicit_complete: the server sends a
    notifications/elicitation/complete notification to the client so it
    knows the URL-mode elicitation identified by elicitation_id is done
    and may retry any requests that were waiting on it.

    In a real app this would be called by an OAuth redirect/webhook handler
    after the user finishes authorising the third-party service.
    """
    await ctx.session.send_elicit_complete(elicitation_id)
    return f"[COMPLETE] OAuth for {service_name} finished — elicitation {elicitation_id} resolved"


@mcp.tool()
async def payment_webhook(elicitation_id: str, ctx: Context[ServerSession, None]) -> str:
    """Called when payment confirmation completes out-of-band.

    Demonstrates send_elicit_complete paired with ctx.elicit_url() (not
    error-raise).  In a real app this would be your payment provider's
    webhook endpoint, called after the user confirms in the browser.

    The client captures elicitation_id from ElicitRequestURLParams.elicitationId
    inside its elicitation_callback, then passes it here once the out-of-band
    flow is complete.
    """
    await ctx.session.send_elicit_complete(elicitation_id)
    return f"[WEBHOOK] Payment confirmed — elicitation {elicitation_id} resolved"


@mcp.tool()
async def test_scheme_validation(ctx: Context[ServerSession, None]) -> str:
    """Send a url-mode elicitation with a non-http/https scheme.

    Exists solely to trigger URL scheme validation in the client callback.
    A security-conscious client should reject any URL whose scheme is not
    in {http, https} and return action="decline" without opening it.
    """
    elicitation_id = str(uuid.uuid4())
    result = await ctx.elicit_url(
        message="Access resource via FTP (scheme validation demo)",
        url=f"ftp://files.example.com/data?id={elicitation_id}",
        elicitation_id=elicitation_id,
    )
    return f"Elicitation result: {result.action}"


if __name__ == "__main__":
    # mcp.run(transport="stdio")
    mcp.run(transport="streamable-http")
