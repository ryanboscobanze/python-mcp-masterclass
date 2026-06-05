"""MCP elicitation client — closure variant (stdio transport).
2f_elicitation/client_elicitation_closure.py

Same scenarios as client_elicitation.py but without the MutableCallback class.
Instead, a single async closure captures a `response` variable via `nonlocal`,
which each scenario reassigns before calling the tool.

Both styles satisfy ClientSession's ElicitationFnT Protocol through Python's
structural subtyping — any async callable with signature (context, params) and
the correct return type qualifies, whether it is a class instance (__call__) or
a plain async function. No inheritance or explicit registration required.

ClientSession takes elicitation_callback once at construction — you cannot swap
it after the session is open.  The nonlocal variable is the simplest way to give
each scenario its own response without a helper class.

Also demonstrates:
- Observing notifications/elicitation/complete via the generic message_handler
  constructor param (PR #1611 will add a dedicated elicit_complete_callback).
- Capturing params.elicitationId inside the closure for the elicit_url +
  send_elicit_complete round-trip (scenario 16).

Run from the mcp_revamp directory:
    python 2f_elicitation/client_elicitation_closure.py
"""

import asyncio
import os
import sys
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError, UrlElicitationRequiredError
from mcp.types import URL_ELICITATION_REQUIRED

_here = os.path.dirname(os.path.abspath(__file__))

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_elicitation.py")],
)

_ALLOWED_SCHEMES = {"http", "https"}

_LABELS = {
    "accept": "User accepted",
    "decline": "User declined",
    "cancel": "Request interrupted by user",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def call_tool(session: ClientSession, tool_name: str, arguments: dict) -> str:
    """Call a tool and return its text output.

    Handles two distinct error paths:
    - result.isError = True: tool-level error embedded in a successful response
      (e.g. ctx.elicit() raised because the callback returned ErrorData).
      NOTE: result.isError uses camelCase in v1.x; main branch uses is_error.
    - McpError thrown with URL_ELICITATION_REQUIRED (-32042): the error-raise
      pattern where the server signals elicitation is required via an exception.
    """
    try:
        result = await session.call_tool(tool_name, arguments)
        if result.isError:
            texts = [c.text for c in result.content if isinstance(c, types.TextContent)]
            return f"[ToolError] {' | '.join(texts) if texts else '(no detail)'}"
        texts = [c.text for c in result.content if isinstance(c, types.TextContent)]
        return " | ".join(texts) if texts else "(no text content)"
    except McpError as e:
        if e.error.code == URL_ELICITATION_REQUIRED:
            url_error = UrlElicitationRequiredError.from_error(e.error)
            parts = [
                f"url={getattr(el, 'url', '?')!r} msg={el.message!r}"
                for el in url_error.elicitations
            ]
            return f"[UrlElicitationRequired {URL_ELICITATION_REQUIRED}] {'; '.join(parts)}"
        return f"[McpError {e.error.code}] {e.error.message}"


async def on_message(message: types.ServerNotification) -> None:
    """Generic server-notification handler.

    Used to observe notifications/elicitation/complete — the only way to
    intercept ElicitCompleteNotification today (no dedicated callback exists).
    """
    if isinstance(message.root, types.ElicitCompleteNotification):
        eid = message.root.params.elicitationId
        print(f"    [notification] notifications/elicitation/complete — id={eid!r}")


async def run() -> None:
    # The closure captures these variables; each scenario reassigns them.
    response = types.ElicitResult(action="cancel")
    last_url_elicitation_id: str | None = None
    error_response: types.ErrorData | None = None

    # (context, params) matches the ElicitationFnT Protocol signature.
    # ClientSession passes both arguments; context is unused here, params
    # carries the mode, message, and (for url mode) url and elicitationId.
    async def callback(context, params):
        nonlocal response, last_url_elicitation_id, error_response
        url = getattr(params, "url", None)
        if params.mode == "url":
            # Security gate: reject non-http/https schemes before anything else
            parsed = urlparse(str(url or ""))
            if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
                print(f"    [callback] SECURITY: rejecting url with scheme {parsed.scheme!r}")
                return types.ElicitResult(action="decline")
            last_url_elicitation_id = getattr(params, "elicitationId", None)
        # ErrorData path: callback signals it cannot handle this request
        if error_response is not None:
            print(f"    [callback] mode={params.mode!r} msg={params.message!r}")
            print(f"    [callback] returning ErrorData: {error_response.message!r}")
            return error_response
        extra = f" url={url!r}" if url else ""
        print(f"    [callback] mode={params.mode!r} msg={params.message!r}{extra}")
        print(f"    [callback] {_LABELS.get(response.action, response.action)}")
        if response.content:
            print(f"    [callback] content={response.content}")
        return response

    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(
            read, write,
            elicitation_callback=callback,
            message_handler=on_message,
        ) as session:
            await session.initialize()

            # =================================================================
            # Form elicitation via ctx.elicit() — book_table
            # Two-field schema: bool (checkAlternative) + str (alternativeDate)
            # =================================================================

            # Scenario 1: available date — elicitation never fires
            print("\n[1] book_table — available date (no elicitation)")
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-26", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 2: checkAlternative=True + valid date → SUCCESS
            print("\n[2] book_table — form elicitation, accept checkAlternative=True with date")
            response = types.ElicitResult(action="accept", content={"checkAlternative": True, "alternativeDate": "2024-12-27"})
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 3: checkAlternative=False — boolean false path → CANCELLED
            print("\n[3] book_table — form elicitation, accept checkAlternative=False")
            response = types.ElicitResult(action="accept", content={"checkAlternative": False, "alternativeDate": ""})
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 4: checkAlternative=True but no date provided → CANCELLED
            print("\n[4] book_table — form elicitation, accept checkAlternative=True with no date")
            response = types.ElicitResult(action="accept", content={"checkAlternative": True, "alternativeDate": ""})
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 5: user declines the entire elicitation
            print("\n[5] book_table — form elicitation, user declines")
            response = types.ElicitResult(action="decline")
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 6: user cancels the elicitation
            print("\n[6] book_table — form elicitation, user cancels")
            response = types.ElicitResult(action="cancel")
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # =================================================================
            # Enum field in form mode — pick_color
            # json_schema_extra={"enum": [...]} sends enum constraints in
            # requestedSchema; clients can render as dropdown / radio buttons.
            # =================================================================

            # Scenario 7: accept a valid enum value
            print("\n[7] pick_color — form elicitation with enum field, accept 'blue'")
            response = types.ElicitResult(action="accept", content={"color": "blue"})
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")

            # Scenario 8: user declines the color picker
            print("\n[8] pick_color — form elicitation with enum field, user declines")
            response = types.ElicitResult(action="decline")
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")

            # =================================================================
            # URL elicitation via ctx.elicit_url() — secure_payment
            # The closure captures params.elicitationId into last_url_elicitation_id
            # for use in scenario 16.
            # =================================================================

            # Scenario 9: user accepts the payment URL
            print("\n[9] secure_payment — URL elicitation, user accepts")
            response = types.ElicitResult(action="accept")
            result = await call_tool(
                session, "secure_payment",
                {"amount": 99.99},
            )
            print(f"    result: {result}")

            # Scenario 10: user declines the payment URL
            print("\n[10] secure_payment — URL elicitation, user declines")
            response = types.ElicitResult(action="decline")
            result = await call_tool(
                session, "secure_payment",
                {"amount": 99.99},
            )
            print(f"    result: {result}")

            # Scenario 11: user cancels the payment URL
            print("\n[11] secure_payment — URL elicitation, user cancels")
            response = types.ElicitResult(action="cancel")
            result = await call_tool(
                session, "secure_payment",
                {"amount": 99.99},
            )
            print(f"    result: {result}")

            # =================================================================
            # URL elicitation via UrlElicitationRequiredError — connect_service
            # The server raises an exception; it arrives as McpError -32042.
            # The elicitation_callback is NOT invoked for this pattern.
            # =================================================================

            # Scenario 12: github — error-raise pattern caught by call_tool()
            print("\n[12] connect_service — UrlElicitationRequiredError (github)")
            result = await call_tool(
                session, "connect_service",
                {"service_name": "github"},
            )
            print(f"    result: {result}")

            # Scenario 13: stripe — same pattern, different service name
            print("\n[13] connect_service — UrlElicitationRequiredError (stripe)")
            result = await call_tool(
                session, "connect_service",
                {"service_name": "stripe"},
            )
            print(f"    result: {result}")

            # =================================================================
            # Completion notification — send_elicit_complete
            # Two pairings:
            #   [14-15] error-raise  → elicitation_id from McpError data
            #   [16]    elicit_url   → elicitation_id from last_url_elicitation_id
            # Both trigger notifications/elicitation/complete observed via on_message.
            # =================================================================

            # Scenario 14: error-raise + completion — github OAuth round-trip
            print("\n[14] connect_service + oauth_complete — send_elicit_complete via error-raise (github)")
            try:
                await session.call_tool("connect_service", {"service_name": "github"})
            except McpError as e:
                if e.error.code == URL_ELICITATION_REQUIRED:
                    url_error = UrlElicitationRequiredError.from_error(e.error)
                    elicitation_id = url_error.elicitations[0].elicitationId
                    print(f"    [McpError -32042] captured elicitation_id={elicitation_id!r}")
                    cb_result = await session.call_tool(
                        "oauth_complete",
                        {"service_name": "github", "elicitation_id": elicitation_id},
                    )
                    texts = [c.text for c in cb_result.content if isinstance(c, types.TextContent)]
                    print(f"    result: {' | '.join(texts)}")
                else:
                    print(f"    [McpError {e.error.code}] {e.error.message}")

            # Scenario 15: error-raise + completion — stripe OAuth round-trip
            print("\n[15] connect_service + oauth_complete — send_elicit_complete via error-raise (stripe)")
            try:
                await session.call_tool("connect_service", {"service_name": "stripe"})
            except McpError as e:
                if e.error.code == URL_ELICITATION_REQUIRED:
                    url_error = UrlElicitationRequiredError.from_error(e.error)
                    elicitation_id = url_error.elicitations[0].elicitationId
                    print(f"    [McpError -32042] captured elicitation_id={elicitation_id!r}")
                    cb_result = await session.call_tool(
                        "oauth_complete",
                        {"service_name": "stripe", "elicitation_id": elicitation_id},
                    )
                    texts = [c.text for c in cb_result.content if isinstance(c, types.TextContent)]
                    print(f"    result: {' | '.join(texts)}")
                else:
                    print(f"    [McpError {e.error.code}] {e.error.message}")

            # Scenario 16: elicit_url + completion — payment webhook round-trip
            # last_url_elicitation_id is set inside the callback closure when the
            # url-mode ElicitRequest arrives (params.elicitationId).
            print("\n[16] secure_payment + payment_webhook — send_elicit_complete via elicit_url")
            response = types.ElicitResult(action="accept")
            last_url_elicitation_id = None
            result = await call_tool(
                session, "secure_payment",
                {"amount": 49.99},
            )
            print(f"    result: {result}")
            if last_url_elicitation_id:
                print(f"    captured elicitation_id={last_url_elicitation_id!r}")
                wh_result = await session.call_tool(
                    "payment_webhook",
                    {"elicitation_id": last_url_elicitation_id},
                )
                texts = [c.text for c in wh_result.content if isinstance(c, types.TextContent)]
                print(f"    webhook result: {' | '.join(texts)}")

            # =================================================================
            # ErrorData return from callback — Plan D
            # Callback returns ErrorData instead of ElicitResult to signal it
            # cannot handle the request.  ctx.elicit() raises on the server;
            # FastMCP catches it and returns result.isError = True.
            # call_tool now detects result.isError (distinct from thrown McpError).
            # NOTE: result.isError is camelCase in v1.x; main branch uses is_error.
            # =================================================================

            # Scenario 17: callback returns ErrorData → result.isError = True
            print("\n[17] pick_color — callback returns ErrorData (unsupported mode)")
            error_response = types.ErrorData(
                code=types.INVALID_REQUEST,
                message="Client does not support form-mode elicitation",
            )
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")
            error_response = None

            # =================================================================
            # URL scheme validation — Plan E
            # Callback validates urlparse(url).scheme before accepting.
            # test_scheme_validation sends ftp:// to trigger the security gate.
            # =================================================================

            # Scenario 18: server sends ftp:// URL — callback declines
            print("\n[18] test_scheme_validation — callback rejects ftp:// scheme")
            response = types.ElicitResult(action="accept")  # would accept if scheme valid
            result = await call_tool(session, "test_scheme_validation", {})
            print(f"    result: {result}")

            # =================================================================
            # Multiple ElicitRequestURLParams in error-raise
            # UrlElicitationRequiredError takes list[ElicitRequestURLParams].
            # connect_multi_service passes two items; call_tool iterates
            # url_error.elicitations (all items, not just [0]).
            # =================================================================

            # Scenario 19: two services — both elicitations reported
            print("\n[19] connect_multi_service — multiple ElicitRequestURLParams in error-raise")
            result = await call_tool(session, "connect_multi_service", {})
            print(f"    result: {result}")

            # =================================================================
            # Numeric fields in form schema
            # ElicitResult.content supports: str | int | float | bool | list[str] | None
            # adjust_booking uses int (guest_count) and float (max_budget).
            # =================================================================

            # Scenario 20: accept with int and float values
            print("\n[20] adjust_booking — form elicitation with int + float fields, accept")
            response = types.ElicitResult(
                action="accept",
                content={"guest_count": 6, "max_budget": 75.5},
            )
            result = await call_tool(
                session, "adjust_booking",
                {"booking_ref": "BK-001"},
            )
            print(f"    result: {result}")

            # Scenario 21: user declines
            print("\n[21] adjust_booking — form elicitation with int + float fields, decline")
            response = types.ElicitResult(action="decline")
            result = await call_tool(
                session, "adjust_booking",
                {"booking_ref": "BK-001"},
            )
            print(f"    result: {result}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
