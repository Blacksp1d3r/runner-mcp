"""JSON-RPC replies may not be attributed to a different request (#590)."""

from __future__ import annotations

import json
import urllib.request
from typing import Self

import pytest

from runner_mcp.bridge_mcp_executor import (
    BridgeExecutionAdapterError,
    LocalMCPClient,
    LocalMCPConfig,
)


class _FakeResponse:
    def __init__(self, response_id: object) -> None:
        self.body = json.dumps(
            {"jsonrpc": "2.0", "id": response_id, "result": {"ok": True}}
        ).encode("utf-8")
        self.headers: dict[str, str] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, _: int) -> bytes:
        return self.body


@pytest.mark.parametrize("returned_id", [1, 3, "2", None, True, 2.0])
def test_local_mcp_rejects_wrong_response_id(
    monkeypatch: pytest.MonkeyPatch,
    returned_id: object,
) -> None:
    def fake_open(_: urllib.request.Request, **kwargs: object) -> _FakeResponse:
        del kwargs
        return _FakeResponse(returned_id)

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    client = LocalMCPClient(
        LocalMCPConfig(endpoint="http://127.0.0.1:9001/mcp", bearer_token="test-token"),
        allowed_tools=frozenset({"runtime_status"}),
    )
    with pytest.raises(BridgeExecutionAdapterError, match="mismatched JSON-RPC"):
        client._post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})


def test_local_mcp_accepts_correct_response_id(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_open(_: urllib.request.Request, **kwargs: object) -> _FakeResponse:
        del kwargs
        return _FakeResponse(2)

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    client = LocalMCPClient(
        LocalMCPConfig(endpoint="http://127.0.0.1:9001/mcp", bearer_token="test-token"),
        allowed_tools=frozenset({"runtime_status"}),
    )
    assert client._post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    ) == {"jsonrpc": "2.0", "id": 2, "result": {"ok": True}}
