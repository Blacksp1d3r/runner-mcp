"""Isolated FASTER-13 loopback transport contract tests.

Disposable HTTP fixture, NOT the real Runner-MCP server. Bind only 127.0.0.1
on an OS-assigned ephemeral port. No Fabric, credentials, or production sockets.
No latency assertions: CI scheduling is not a performance baseline.
"""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


class SyntheticHandler(BaseHTTPRequestHandler):
    """Fixed allowlisted JSON-RPC test handler, no real tool dispatch."""

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/synthetic-mcp":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 70_000:
            self.send_error(413)
            return
        try:
            request = json.loads(self.rfile.read(size))
            if (
                not isinstance(request, dict)
                or request.get("jsonrpc") != "2.0"
                or request.get("method") != "tools/call"
                or request.get("params", {}).get("name") != "synthetic_read_only"
                or not isinstance(request.get("id"), int)
                or not isinstance(
                    request["params"].get("arguments", {}).get("trace_id"), str
                )
            ):
                raise ValueError("invalid request")
            arguments = request["params"]["arguments"]
            if not isinstance(arguments.get("payload"), str):
                raise ValueError("invalid payload")
            answer = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "trace_id": arguments["trace_id"],
                    "payload_bytes": len(arguments["payload"].encode()),
                },
            }
        except (ValueError, KeyError, TypeError, AttributeError):
            self.send_error(400)
            return
        body = json.dumps(answer, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        """Avoid reporting random ephemeral port numbers in CI logs."""


@contextmanager
def synthetic_server():
    """Create and close an isolated, non-serving loopback-only fixture."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), SyntheticHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/synthetic-mcp"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


@pytest.mark.parametrize("payload_size", [128, 4096, 65536])
def test_loopback_preserves_jsonrpc_correlation(payload_size: int) -> None:
    """Check framing and trace ID, not real MCP latency or live capability."""
    trace_id = "a" * 32
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "synthetic_read_only",
                "arguments": {"payload": "x" * payload_size, "trace_id": trace_id},
            },
        }
    ).encode()
    with synthetic_server() as url:
        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=3) as response:  # noqa: S310
            assert response.status == 200
            result = json.loads(response.read())
    assert result == {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {"trace_id": trace_id, "payload_bytes": payload_size},
    }


def test_loopback_unknown_tool_fails_closed() -> None:
    """An unknown test-tool name cannot execute as an allowlisted request."""
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "not_allowlisted",
                "arguments": {"payload": "x", "trace_id": "a" * 32},
            },
        }
    ).encode()
    with synthetic_server() as url:
        with pytest.raises(HTTPError) as exc:
            urlopen(Request(url, data=body), timeout=3)  # noqa: S310
    assert exc.value.code == 400
