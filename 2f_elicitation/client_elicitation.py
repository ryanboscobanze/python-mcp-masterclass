"""MCP elicitation client example (stdio transport).
2f_elicitation/client_elicitation.py

Demonstrates how a client handles elicitation requests sent by the server:

1. Form mode  — elicitation_callback receives mode="form" with a JSON schema;
   the client returns ElicitResult(action="accept", content={...}),
   action="decline", or action="cancel".

2. URL mode   — elicitation_callback receives mode="url" with a URL and
   elicitation_id; the client inspects them and returns action="accept" /
   "decline" / "cancel".

3. Error-raise pattern — the server raises UrlElicitationRequiredError which
   arrives as McpError with code URL_ELICITATION_REQUIRED (-32042).
   The client catches it, unpacks the elicitation list, and handles each URL.

4. Completion notification (error-raise path) — after catching -32042 the
   client calls oauth_complete(elicitation_id), triggering
   notifications/elicitation/complete observed via message_handler.

5. Completion notification (elicit_url path) — MutableCallback captures
   params.elicitationId during the url-mode request; after secure_payment
   returns the client calls payment_webhook(elicitation_id), triggering
   the same notification.
   NOTE: ClientSession handles ElicitCompleteNotification with a bare pass
   (no dedicated callback); message_handler is the only hook today.
   PR #1611 will add elicit_complete_callback.

All scenarios are scripted (no interactive prompts) via a MutableCallback
that can be swapped between test cases without restarting the session.

Run from the mcp_revamp directory:
    python 2f_elicitation/client_elicitation.py
"""

import asyncio
import os
import sys
from typing import Any
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.context import RequestContext
from mcp.shared.exceptions import McpError, UrlElicitationRequiredError
from mcp.types import URL_ELICITATION_REQUIRED

_here = os.path.dirname(os.path.abspath(__file__))
_ALLOWED_SCHEMES = {"http", "https"}

server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(_here, "server_elicitation.py")],
)



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

# ---------------------------------------------------------------------------
# Scripted callback
# ---------------------------------------------------------------------------

class MutableCallback:
    """Elicitation callback whose response can be swapped between scenarios.

    Holds a single ElicitResult that is returned for every incoming request.
    Prints the mode and message so test output remains readable.

    __call__ takes (context, params) because that is the signature required by
    the ElicitationFnT Protocol — ClientSession passes both arguments every time
    it invokes the callback.  context is unused here; params carries the mode,
    message, and (for url mode) the url and elicitationId.
    """

    def __init__(self, response: types.ElicitResult | None = None) -> None:
        self.response: types.ElicitResult = response or types.ElicitResult(action="cancel")
        self.last_url_elicitation_id: str | None = None
        self.error_response: types.ErrorData | None = None

    def set(self, response: types.ElicitResult) -> None:
        self.response = response

    def set_error(self, error: types.ErrorData) -> None:
        """Configure callback to return ErrorData on the next invocation."""
        self.error_response = error

    def clear_error(self) -> None:
        self.error_response = None

    async def __call__(
        self,
        context: RequestContext[ClientSession, Any],
        params: types.ElicitRequestParams,
    ) -> types.ElicitResult | types.ErrorData:
        url = getattr(params, "url", None)
        if params.mode == "url":
            # Security gate: reject non-http/https schemes before doing anything else
            parsed = urlparse(str(url or ""))
            if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
                print(f"    [callback] SECURITY: rejecting url with scheme {parsed.scheme!r}")
                return types.ElicitResult(action="decline")
            self.last_url_elicitation_id = getattr(params, "elicitationId", None)
        # ErrorData path: callback signals that it cannot handle this request
        if self.error_response is not None:
            print(f"    [callback] mode={params.mode!r} msg={params.message!r}")
            print(f"    [callback] returning ErrorData: {self.error_response.message!r}")
            return self.error_response
        extra = f" url={url!r}" if url else ""
        print(f"    [callback] mode={params.mode!r} msg={params.message!r}{extra}")
        labels = {
            "accept": "User accepted",
            "decline": "User declined",
            "cancel": "Request interrupted by user",
        }
        print(f"    [callback] {labels.get(self.response.action, self.response.action)}")
        if self.response.content:
            print(f"    [callback] content={self.response.content}")
        return self.response


async def run() -> None:
    """Run all elicitation scenarios against a single server session."""
    cb = MutableCallback()

    async with stdio_client(server_params) as (read, write):
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(
            read, write,
            elicitation_callback=cb,
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
            cb.set(types.ElicitResult(
                action="accept",
                content={"checkAlternative": True, "alternativeDate": "2024-12-27"},
            ))
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 3: checkAlternative=False — boolean false path → CANCELLED
            print("\n[3] book_table — form elicitation, accept checkAlternative=False")
            cb.set(types.ElicitResult(
                action="accept",
                content={"checkAlternative": False, "alternativeDate": ""},
            ))
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 4: checkAlternative=True but no date provided → CANCELLED
            print("\n[4] book_table — form elicitation, accept checkAlternative=True with no date")
            cb.set(types.ElicitResult(
                action="accept",
                content={"checkAlternative": True, "alternativeDate": ""},
            ))
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 5: user declines the entire elicitation
            print("\n[5] book_table — form elicitation, user declines")
            cb.set(types.ElicitResult(action="decline"))
            result = await call_tool(
                session, "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )
            print(f"    result: {result}")

            # Scenario 6: user cancels the elicitation
            print("\n[6] book_table — form elicitation, user cancels")
            cb.set(types.ElicitResult(action="cancel"))
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
            cb.set(types.ElicitResult(
                action="accept",
                content={"color": "blue"},
            ))
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")

            # Scenario 8: user declines the color picker
            print("\n[8] pick_color — form elicitation with enum field, user declines")
            cb.set(types.ElicitResult(action="decline"))
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")

            # =================================================================
            # URL elicitation via ctx.elicit_url() — secure_payment
            # MutableCallback stores params.elicitationId (captured in __call__)
            # for use in scenario 16.
            # =================================================================

            # Scenario 9: user accepts the payment URL
            print("\n[9] secure_payment — URL elicitation, user accepts")
            cb.set(types.ElicitResult(action="accept"))
            result = await call_tool(
                session, "secure_payment",
                {"amount": 99.99},
            )
            print(f"    result: {result}")

            # Scenario 10: user declines the payment URL
            print("\n[10] secure_payment — URL elicitation, user declines")
            cb.set(types.ElicitResult(action="decline"))
            result = await call_tool(
                session, "secure_payment",
                {"amount": 99.99},
            )
            print(f"    result: {result}")

            # Scenario 11: user cancels the payment URL
            print("\n[11] secure_payment — URL elicitation, user cancels")
            cb.set(types.ElicitResult(action="cancel"))
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
            #   [16]    elicit_url   → elicitation_id from MutableCallback.last_url_elicitation_id
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
            # elicitation_id comes from MutableCallback.last_url_elicitation_id,
            # which was set during the url-mode elicitation request in scenario 9-11.
            print("\n[16] secure_payment + payment_webhook — send_elicit_complete via elicit_url")
            cb.set(types.ElicitResult(action="accept"))
            cb.last_url_elicitation_id = None
            result = await call_tool(
                session, "secure_payment",
                {"amount": 49.99},
            )
            print(f"    result: {result}")
            if cb.last_url_elicitation_id:
                print(f"    captured elicitation_id={cb.last_url_elicitation_id!r}")
                wh_result = await session.call_tool(
                    "payment_webhook",
                    {"elicitation_id": cb.last_url_elicitation_id},
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
            cb.set_error(types.ErrorData(
                code=types.INVALID_REQUEST,
                message="Client does not support form-mode elicitation",
            ))
            result = await call_tool(session, "pick_color", {})
            print(f"    result: {result}")
            cb.clear_error()

            # =================================================================
            # URL scheme validation — Plan E
            # Callback validates urlparse(url).scheme before accepting.
            # test_scheme_validation sends ftp:// to trigger the security gate.
            # =================================================================

            # Scenario 18: server sends ftp:// URL — callback declines
            print("\n[18] test_scheme_validation — callback rejects ftp:// scheme")
            cb.set(types.ElicitResult(action="accept"))  # would accept if scheme valid
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
            cb.set(types.ElicitResult(
                action="accept",
                content={"guest_count": 6, "max_budget": 75.5},
            ))
            result = await call_tool(
                session, "adjust_booking",
                {"booking_ref": "BK-001"},
            )
            print(f"    result: {result}")

            # Scenario 21: user declines
            print("\n[21] adjust_booking — form elicitation with int + float fields, decline")
            cb.set(types.ElicitResult(action="decline"))
            result = await call_tool(
                session, "adjust_booking",
                {"booking_ref": "BK-001"},
            )
            print(f"    result: {result}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
