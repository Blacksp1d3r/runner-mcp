"""#590: local MCP bearer must never follow a proxy or HTTP redirect.

All tests run against in-memory urllib handles; no real socket or remote host.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from email.message import Message

import pytest

from runner_mcp.bridge_mcp_executor import (
    LocalMCPClient,
    LocalMCPConfig,
    _NoLocalMCPRedirects,
    _open_local_mcp_request,
    _private_loopback_opener,
)
from runner_mcp.bridge_processor import BridgeExecutionAdapterError


def test_fixed_local_mcp_opener_ignores_hostile_proxy_environment(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://intermediary.example.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://intermediary.example.invalid:8443")
    monkeypatch.setenv("ALL_PROXY", "http://intermediary.example.invalid:3128")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(
        urllib.request, "getproxies",
        lambda: pytest.fail("Local MCP must never read default environment proxies"),
    )
    opener = _private_loopback_opener()
    active = opener.handlers
    assert any(isinstance(h, _NoLocalMCPRedirects) for h in active)
    assert not any(
        isinstance(h, urllib.request.HTTPRedirectHandler)
        and not isinstance(h, _NoLocalMCPRedirects)
        for h in active
    )
    # urllib may omit an empty ProxyHandler from its active handlers.
    assert all(
        h.proxies == {}
        for h in active
        if isinstance(h, urllib.request.ProxyHandler)
    )


@pytest.mark.parametrize(
    "destination",
    [
        "http://127.0.0.1:8000/another-path",
        "http://localhost:8000/mcp",
        "http://[::1]:8000/mcp",
        "http://outside.example.invalid/leak",
        "https://outside.example.invalid/leak",
    ],
)
@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_no_redirect_handler_never_forwards_authorized_mcp_request(
    destination, code,
) -> None:
    request = urllib.request.Request(
        "http://127.0.0.1:8000/mcp",
        data=b'{"jsonrpc":"2.0"}',
        headers={"Authorization": "Bearer synthetic-example"},
        method="POST",
    )
    assert _NoLocalMCPRedirects().redirect_request(
        request, None, code, "redirect", Message(), destination,
    ) is None
    assert request.full_url == "http://127.0.0.1:8000/mcp"
    assert request.get_header("Authorization") == "Bearer synthetic-example"


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_local_mcp_rejects_30x_before_follow_or_token_egress(
    monkeypatch, code,
) -> None:
    calls = []
    sentinel_token = "token-private-must-not-leak"

    class SimulatedPrivateOpener:
        def open(self, request, timeout):
            calls.append(request)
            assert timeout > 0
            assert request.full_url == "http://127.0.0.1:8000/mcp"
            assert request.get_header("Authorization") == f"Bearer {sentinel_token}"
            raise urllib.error.HTTPError(
                request.full_url,
                code,
                "redirect",
                {"Location": "https://outside.example.invalid/steal"},
                None,
            )

    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor._private_loopback_opener",
        lambda: SimulatedPrivateOpener(),
    )
    client = LocalMCPClient(
        LocalMCPConfig(
            endpoint="http://127.0.0.1:8000/mcp",
            bearer_token=sentinel_token,
        ),
        allowed_tools=frozenset({"list_projects"}),
    )
    with pytest.raises(
        BridgeExecutionAdapterError,
        match="Runner MCP is unavailable or rejected the request",
    ) as caught:
        client.initialize()
    assert len(calls) == 1
    assert sentinel_token not in str(caught.value)
    assert "outside.example.invalid" not in str(caught.value)


def test_fixed_mcp_transport_routes_only_through_private_opener(monkeypatch):
    calls = []

    class TrackingOpener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            return "synthetic-local-response"

    monkeypatch.setattr(
        "runner_mcp.bridge_mcp_executor._private_loopback_opener",
        lambda: TrackingOpener(),
    )
    monkeypatch.setattr(
        urllib.request, "urlopen",
        lambda *_a, **_kw: pytest.fail("default urllib opener must not be used"),
    )
    request = urllib.request.Request("http://127.0.0.1:8000/mcp", data=b"{}")
    assert _open_local_mcp_request(request, timeout=5) == "synthetic-local-response"
    assert calls == [(request, 5)]
