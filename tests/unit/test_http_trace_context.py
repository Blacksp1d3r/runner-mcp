from __future__ import annotations

import asyncio

from runner_mcp.http_middleware import (
    RequestIdMiddleware,
    TraceContext,
    current_trace_id,
    parse_traceparent,
)

TRACE_ID = "0123456789abcdef0123456789abcdef"
PARENT_ID = "0123456789abcdef"


def test_parse_traceparent_canonicalizes_valid_v00_context() -> None:
    context = parse_traceparent(
        f"00-{TRACE_ID.upper()}-{PARENT_ID.upper()}-01"
    )

    assert context == TraceContext(
        trace_id=TRACE_ID,
        parent_id=PARENT_ID,
        trace_flags="01",
    )
    assert context.traceparent == f"00-{TRACE_ID}-{PARENT_ID}-01"


def test_parse_traceparent_rejects_zero_or_non_v00_context() -> None:
    assert parse_traceparent(f"00-{'0' * 32}-{PARENT_ID}-00") is None
    assert parse_traceparent(f"00-{TRACE_ID}-{'0' * 16}-00") is None
    assert parse_traceparent(f"01-{TRACE_ID}-{PARENT_ID}-00") is None
    assert parse_traceparent(f"00-{TRACE_ID}-{PARENT_ID}-00-extra") is None


def _run_request(headers: list[tuple[bytes, bytes]]) -> tuple[str, list[dict]]:
    observed_trace_id = ""
    sent: list[dict] = []

    async def app(scope, receive, send) -> None:
        nonlocal observed_trace_id
        del scope, receive
        observed_trace_id = current_trace_id()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/mcp",
        "headers": headers,
    }
    asyncio.run(RequestIdMiddleware(app)(scope, receive, send))
    return observed_trace_id, sent


def _response_headers(sent: list[dict]) -> dict[bytes, bytes]:
    start = next(message for message in sent if message["type"] == "http.response.start")
    return dict(start["headers"])


def test_request_middleware_keeps_inbound_trace_id_and_returns_child_traceparent() -> None:
    inbound = f"00-{TRACE_ID}-{PARENT_ID}-01"
    observed_trace_id, sent = _run_request(
        [(b"traceparent", inbound.encode("ascii"))]
    )

    headers = _response_headers(sent)
    response = headers[b"traceparent"].decode("ascii")
    parsed = parse_traceparent(response)

    assert observed_trace_id == TRACE_ID
    assert parsed is not None
    assert parsed.trace_id == TRACE_ID
    assert parsed.parent_id != PARENT_ID
    assert parsed.trace_flags == "01"
    assert b"x-request-id" in headers


def test_invalid_or_duplicate_traceparent_is_non_authoritative() -> None:
    observed_trace_id, sent = _run_request(
        [
            (b"traceparent", b"invalid"),
            (b"traceparent", f"00-{TRACE_ID}-{PARENT_ID}-01".encode("ascii")),
        ]
    )

    headers = _response_headers(sent)
    parsed = parse_traceparent(headers[b"traceparent"].decode("ascii"))

    assert parsed is not None
    assert observed_trace_id == parsed.trace_id
    assert parsed.trace_id != TRACE_ID
    assert parsed.trace_flags == "00"
