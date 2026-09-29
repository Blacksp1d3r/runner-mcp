from __future__ import annotations

import json

import pytest

from runner_mcp.aifordable_transport import (
    AIFORDABLE_RELAY_ENV_KEYS,
    AIfordableClaim,
    AIfordableControlOperation,
    AIfordableEnvelope,
    AIfordableRelayClient,
    AIfordableRelayConfig,
    AIfordableResponse,
    AIfordableTransportError,
)

CREDENTIAL = "c" * 48
ORIGIN = "https://control.example.invalid"
SUBJECT = "runner:primary"


class FakeExchange:
    def __init__(self, responses: list[AIfordableResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, bytes, float]] = []

    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> AIfordableResponse:
        self.calls.append((route, body, timeout_seconds))
        return self.responses.pop(0)


def config() -> AIfordableRelayConfig:
    return AIfordableRelayConfig(
        origin=ORIGIN,
        subject=SUBJECT,
        credential=CREDENTIAL,
    )


def envelope() -> AIfordableEnvelope:
    return AIfordableEnvelope(
        request_id="cmd:test",
        target_subject=SUBJECT,
        operation=AIfordableControlOperation.RUNTIME_STATUS,
        issued_at=1_000,
        expires_at=1_300,
        attempt=0,
        payload={},
    )


def wire_claim() -> bytes:
    request = envelope()
    return json.dumps(
        {
            "envelope": {
                "schema_version": "aifordable.control/v1",
                "request_id": request.request_id,
                "target_subject": request.target_subject,
                "operation": request.operation.value,
                "issued_at": request.issued_at,
                "expires_at": request.expires_at,
                "attempt": request.attempt,
                "payload": {},
            },
            "fingerprint": request.fingerprint,
            "version": 2,
            "owner_generation": 1,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def test_private_config_is_https_only_and_secret_safe() -> None:
    values = {
        AIFORDABLE_RELAY_ENV_KEYS[0]: ORIGIN,
        AIFORDABLE_RELAY_ENV_KEYS[1]: SUBJECT,
        AIFORDABLE_RELAY_ENV_KEYS[2]: CREDENTIAL,
    }

    loaded = AIfordableRelayConfig.from_mapping(values)

    assert loaded.origin == ORIGIN
    assert loaded.subject == SUBJECT
    assert CREDENTIAL not in repr(loaded)


@pytest.mark.parametrize(
    "origin",
    [
        "http://control.example.invalid",
        "https://user:pass@control.example.invalid",
        "https://control.example.invalid/private",
        "https://control.example.invalid?runner=other",
    ],
)
def test_config_rejects_endpoint_authority_broadening(origin: str) -> None:
    with pytest.raises(ValueError, match="configuration"):
        AIfordableRelayConfig(
            origin=origin,
            subject=SUBJECT,
            credential=CREDENTIAL,
        )


def test_claim_matches_exact_aifordable_runner_api() -> None:
    exchange = FakeExchange(
        [AIfordableResponse(status=200, body=wire_claim())]
    )
    client = AIfordableRelayClient(config(), exchange)

    claim = client.claim_once(now=1_100)

    assert claim == AIfordableClaim(
        envelope=envelope(),
        fingerprint=envelope().fingerprint,
        version=2,
        owner_generation=1,
    )
    route, body, timeout = exchange.calls[0]
    assert route == "/internal/control-relay/claim?wait_seconds=15"
    assert body == b""
    assert timeout == 30.0


def test_empty_queue_is_204() -> None:
    exchange = FakeExchange([AIfordableResponse(status=204, body=b"")])

    assert AIfordableRelayClient(config(), exchange).claim_once(now=1_100) is None


def test_wrong_target_and_expired_claim_fail_closed() -> None:
    payload = json.loads(wire_claim())
    payload["envelope"]["target_subject"] = "runner:other"
    wrong_target = FakeExchange(
        [
            AIfordableResponse(
                status=200,
                body=json.dumps(payload).encode(),
            )
        ]
    )

    with pytest.raises(AIfordableTransportError):
        AIfordableRelayClient(config(), wrong_target).claim_once(now=1_100)

    payload = json.loads(wire_claim())
    payload["envelope"]["expires_at"] = 1_100
    expired = FakeExchange(
        [
            AIfordableResponse(
                status=200,
                body=json.dumps(payload).encode(),
            )
        ]
    )
    with pytest.raises(AIfordableTransportError, match="expired"):
        AIfordableRelayClient(config(), expired).claim_once(now=1_100)


def test_terminal_result_uses_exact_result_api() -> None:
    exchange = FakeExchange([AIfordableResponse(status=204, body=b"")])
    client = AIfordableRelayClient(config(), exchange)

    client.submit_terminal_result(
        request_id="cmd:test",
        expected_version=2,
        owner_generation=1,
        action="complete",
        result_code="ok",
        result_payload={"result": {"mode": "operational"}},
    )

    route, body, _timeout = exchange.calls[0]
    assert route == "/internal/control-relay/cmd:test/complete"
    assert json.loads(body) == {
        "expected_version": 2,
        "owner_generation": 1,
        "result_code": "ok",
        "result_payload": {
            "result": {
                "mode": "operational",
            }
        },
    }
    assert CREDENTIAL.encode() not in body
    assert ORIGIN.encode() not in body


def test_state_conflict_retains_bounded_http_status() -> None:
    exchange = FakeExchange([AIfordableResponse(status=409, body=b"{}")])

    with pytest.raises(AIfordableTransportError) as caught:
        AIfordableRelayClient(config(), exchange).submit_terminal_result(
            request_id="cmd:test",
            expected_version=2,
            owner_generation=1,
            action="complete",
            result_code="ok",
            result_payload={"result": {}},
        )

    assert caught.value.status == 409
    assert "conflicted" in str(caught.value)


def test_result_payload_rejects_secret_fields() -> None:
    client = AIfordableRelayClient(config(), FakeExchange([]))

    with pytest.raises(AIfordableTransportError, match="result payload"):
        client.submit_terminal_result(
            request_id="cmd:test",
            expected_version=2,
            owner_generation=1,
            action="complete",
            result_code="ok",
            result_payload={"credential": "forbidden"},
        )
