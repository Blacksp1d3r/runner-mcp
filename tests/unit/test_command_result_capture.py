from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from runner_mcp.aifordable_relay import AIfordableRelayConfig
from runner_mcp.command_result_capture import (
    CommandResultCapture,
    CommandResultCaptureError,
    CommandResultCaptureMiddleware,
    CommandResultFlushReport,
    CommandResultUploadResponse,
    build_command_result_capture,
)

NOW = datetime(2026, 11, 7, 10, 0, tzinfo=UTC)
CUSTOMER = "AF-CUSTOMER-0001"
HOST = "AF-VM-0001"
SERVICE = "AF-SVC-0003"
PROJECT = "runner-mcp"
SUBJECT = "runner:aifordable-lab"
TOKEN = "l" * 48


def config(**overrides: str) -> AIfordableRelayConfig:
    values = {
        "base_url": "https://control.example.test",
        "runner_subject": SUBJECT,
        "credential": TOKEN,
    }
    values.update(overrides)
    return AIfordableRelayConfig(**values)


def expected_ack(payload: dict[str, object], **overrides: object) -> bytes:
    ack: dict[str, object] = {
        "evidence_ref": payload["evidence_ref"],
        "source_subject": SUBJECT,
        "credential_generation": 4,
        "customer_id": CUSTOMER,
        "asset_id": HOST,
        "service_id": SERVICE,
        "authority_revision": "infra:" + "a" * 64,
        "accepted": True,
        "replayed": False,
    }
    ack.update(overrides)
    started = datetime.fromisoformat(str(payload["started_at"]))
    finished = datetime.fromisoformat(str(payload["finished_at"]))
    canonical = {
        "evidence_ref": payload["evidence_ref"],
        "customer_id": ack["customer_id"],
        "asset_id": ack["asset_id"],
        "service_id": ack["service_id"],
        "source_subject": ack["source_subject"],
        "credential_generation": ack["credential_generation"],
        "authority_revision": ack["authority_revision"],
        "project_id": payload["project_id"],
        "chat_id": payload["chat_id"],
        "connector": payload["connector"],
        "command_label": payload["command_label"],
        "started_at": started.astimezone(UTC).isoformat(),
        "finished_at": finished.astimezone(UTC).isoformat(),
        "exit_code": payload["exit_code"],
        "status": payload["status"],
        "error_code": payload["error_code"],
        "event": payload["event"],
        "visibility": payload["visibility"],
        "output_preview": payload["output_preview"],
    }
    encoded = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    ack["result_digest"] = hashlib.sha256(encoded).hexdigest()
    return json.dumps(ack, separators=(",", ":"), sort_keys=True).encode()


class FakeExchange:
    def __init__(self, *, ack_overrides: dict[str, object] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, object], float]] = []
        self.ack_overrides = ack_overrides or {}
        self.failure: CommandResultCaptureError | None = None

    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> CommandResultUploadResponse:
        payload = json.loads(body)
        self.calls.append((route, payload, timeout_seconds))
        if self.failure is not None:
            raise self.failure
        return CommandResultUploadResponse(
            status=200,
            body=expected_ack(payload, **self.ack_overrides),
        )


def add_record(
    capture: CommandResultCapture,
    *,
    command_label: str = "fabric_continuity_status",
    failed: bool = False,
):
    return capture.capture_completed(
        chat_id="mcp:" + "b" * 48,
        command_label=command_label,
        started_at=NOW,
        finished_at=NOW + timedelta(seconds=1),
        failed=failed,
    )


def test_capture_uploads_only_safe_metadata_with_the_existing_lab_identity() -> None:
    exchange = FakeExchange()
    capture = CommandResultCapture(config(), exchange=exchange)
    row = add_record(capture)

    report = capture.flush_pending(limit=1)

    assert report == CommandResultFlushReport(1, 1, 0, None)
    assert row.evidence_ref.startswith("cmd:")
    route, payload, timeout = exchange.calls[0]
    assert route == "/internal/control-relay/command-results"
    assert timeout == 2.0
    assert payload["customer_id"] == CUSTOMER
    assert payload["host_id"] == HOST
    assert payload["project_id"] == PROJECT
    assert payload["connector"] == "runner_mcp"
    assert payload["command_label"] == "fabric_continuity_status"
    assert payload["event"] == "tool_result"
    assert payload["status"] == "completed"
    assert payload["error_code"] is None
    assert payload["exit_code"] is None
    assert payload["visibility"] == "status_only"
    assert payload["output_preview"] is None
    assert not {
        "source_subject",
        "service_id",
        "credential_generation",
        "authority_revision",
        "arguments",
        "stdout",
        "stderr",
        "result",
        "credential",
    }.intersection(payload)
    assert TOKEN not in repr(payload)


def test_primary_runner_subject_is_not_misreported_as_the_lab_service() -> None:
    values = {
        "RUNNER_MCP_AIFORDABLE_RELAY_URL": "https://control.example.test",
        "RUNNER_MCP_AIFORDABLE_RUNNER_SUBJECT": "runner:control",
        "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL": TOKEN,
    }

    assert build_command_result_capture(values) is None


def test_missing_or_non_https_relay_configuration_fails_closed() -> None:
    assert build_command_result_capture({}) is None
    values = {
        "RUNNER_MCP_AIFORDABLE_RELAY_URL": "http://control.example.test",
        "RUNNER_MCP_AIFORDABLE_RUNNER_SUBJECT": SUBJECT,
        "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL": TOKEN,
    }
    assert build_command_result_capture(values) is None


def test_transport_failure_retains_safe_record_and_applies_backoff() -> None:
    exchange = FakeExchange()
    exchange.failure = CommandResultCaptureError("transport_unavailable")
    clock = [100.0]
    capture = CommandResultCapture(
        config(),
        exchange=exchange,
        monotonic=lambda: clock[0],
    )
    add_record(capture)

    first = capture.flush_pending(limit=1)
    second = capture.flush_pending(limit=1)

    assert first.failure_code == "transport_unavailable"
    assert first.pending_remaining == 1
    assert second.failure_code == "retry_backoff"
    assert second.pending_remaining == 1
    assert len(exchange.calls) == 1

    exchange.failure = None
    clock[0] += 1.0
    third = capture.flush_pending(limit=1)
    assert third.accepted == 1
    assert third.pending_remaining == 0


def test_wrong_server_digest_never_discards_local_safe_record() -> None:
    exchange = FakeExchange(ack_overrides={"result_digest": "0" * 64})
    capture = CommandResultCapture(config(), exchange=exchange)
    add_record(capture)

    report = capture.flush_pending(limit=1)

    assert report.accepted == 0
    assert report.failure_code == "source_rejected"
    assert report.pending_remaining == 1


def test_middleware_does_not_forward_tool_arguments_or_result_content() -> None:
    exchange = FakeExchange()
    capture = CommandResultCapture(config(), exchange=exchange)
    middleware = CommandResultCaptureMiddleware(capture)
    ctx = SimpleNamespace(
        method="tools/call",
        request_id=77,
        params={
            "name": "fabric_continuity_status",
            "arguments": {"api_token": "NEVER_FORWARD_THIS"},
        },
        request=SimpleNamespace(headers={"mcp-session-id": "session-secret"}),
    )
    tool_result = {
        "isError": False,
        "content": [{"type": "text", "text": "PRIVATE_TOOL_OUTPUT"}],
    }

    async def call_next(_ctx):
        return tool_result

    async def exercise():
        result = await middleware(ctx, call_next)
        if middleware._flush_task is not None:
            await middleware._flush_task
        return result

    result = asyncio.run(exercise())

    assert result is tool_result
    assert capture.pending_count == 0
    assert len(exchange.calls) == 1
    route, payload, _timeout = exchange.calls[0]
    assert route == "/internal/control-relay/command-results"
    assert payload["chat_id"].startswith("mcp:")
    assert "session-secret" not in payload["chat_id"]
    assert payload["command_label"] == "fabric_continuity_status"
    assert payload["status"] == "completed"
    assert payload["output_preview"] is None
    assert "NEVER_FORWARD_THIS" not in repr(payload)
    assert "PRIVATE_TOOL_OUTPUT" not in repr(payload)


def test_middleware_records_failed_tool_result_without_inventing_exit_code() -> None:
    exchange = FakeExchange()
    capture = CommandResultCapture(config(), exchange=exchange)
    middleware = CommandResultCaptureMiddleware(capture)
    ctx = SimpleNamespace(
        method="tools/call",
        request_id=78,
        params={"name": "fabric_continuity_status"},
        request=SimpleNamespace(headers={"mcp-session-id": "session-two"}),
    )

    async def call_next(_ctx):
        return {"isError": True, "content": [{"type": "text", "text": "private"}]}

    async def exercise():
        await middleware(ctx, call_next)
        if middleware._flush_task is not None:
            await middleware._flush_task

    asyncio.run(exercise())

    payload = exchange.calls[0][1]
    assert payload["status"] == "failed"
    assert payload["error_code"] == "command_failed"
    assert payload["exit_code"] is None
    assert payload["output_preview"] is None


def test_middleware_ignores_non_tool_requests() -> None:
    exchange = FakeExchange()
    capture = CommandResultCapture(config(), exchange=exchange)
    middleware = CommandResultCaptureMiddleware(capture)
    ctx = SimpleNamespace(
        method="tools/list",
        request_id=79,
        params={},
        request=SimpleNamespace(headers={}),
    )

    async def call_next(_ctx):
        return {"tools": []}

    result = asyncio.run(middleware(ctx, call_next))

    assert result == {"tools": []}
    assert capture.pending_count == 0
    assert exchange.calls == []
