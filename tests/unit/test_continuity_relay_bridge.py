import hashlib
import json

from runner_mcp.aifordable_relay import _parse_claim
from runner_mcp.bridge_mcp_executor import (
    LocalMCPBridgeExecutor,
    LocalMCPConfig,
)
from runner_mcp.bridge_protocol import bridge_tool_call, parse_bridge_request


def _fingerprint(envelope: dict[str, object]) -> str:
    encoded = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_continuity_bridge_action_is_argument_free() -> None:
    request = parse_bridge_request(
        json.dumps(
            {
                "request_id": "continuity-1",
                "action": "fabric_continuity_status",
            }
        )
    )
    assert bridge_tool_call(request) == ("fabric_continuity_status", {})


def test_aifordable_relay_accepts_only_empty_continuity_claim() -> None:
    envelope = {
        "schema_version": "aifordable.control/v1",
        "request_id": "continuity-2",
        "target_subject": "runner:aifordable-lab",
        "operation": "fabric_continuity_status",
        "issued_at": 100,
        "expires_at": 200,
        "attempt": 0,
        "payload": {},
    }
    raw = json.dumps(
        {
            "envelope": envelope,
            "fingerprint": _fingerprint(envelope),
            "version": 2,
            "owner_generation": 1,
        }
    ).encode()

    claim = _parse_claim(
        raw,
        expected_subject="runner:aifordable-lab",
        now_epoch=150,
    )

    assert claim.operation == "fabric_continuity_status"
    assert claim.payload == {}
    bridge = claim.bridge_request()
    assert bridge_tool_call(bridge) == ("fabric_continuity_status", {})


def test_local_bridge_executor_uses_fixed_continuity_tool() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls = []

        def _call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return {
                "schemaVersion": "runner.fabric/continuity-status/v1",
                "mode": "blocked",
            }

    executor = LocalMCPBridgeExecutor(
        LocalMCPConfig(
            endpoint="http://127.0.0.1:8000/mcp",
            bearer_token="x" * 32,
        )
    )
    fake = FakeClient()
    executor._local.client = fake

    result = executor.fabric_continuity_status()

    assert result["mode"] == "blocked"
    assert fake.calls == [("fabric_continuity_status", {})]
