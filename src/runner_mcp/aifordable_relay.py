from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bridge_processor import (
    BridgeProcessor,
    BridgeProcessOutcome,
    BridgeProcessState,
    BridgeResultSink,
    BridgeResultSinkError,
)
from .bridge_protocol import (
    REQUEST_ID_RE,
    BridgeAction,
    BridgeRequest,
    BridgeResultState,
    parse_bridge_result,
)
from .bridge_replay import BridgeReplayLedger

RELAY_ENV_KEYS = frozenset(
    {
        "RUNNER_MCP_AIFORDABLE_RELAY_URL",
        "RUNNER_MCP_AIFORDABLE_RUNNER_SUBJECT",
        "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL",
    }
)
_MAX_HTTP_BYTES = 128 * 1024
_MAX_TTL_SECONDS = 3_600
_RUNNER_SUBJECT_RE = re.compile(r"^runner:[a-z0-9][a-z0-9._:-]{0,119}$")
_CONTROL_SCHEMA = "aifordable.control/v1"
_ALLOWED_OPERATIONS = {
    "runtime_status": BridgeAction.RUNTIME_STATUS,
    "runtime_doctor": BridgeAction.RUNTIME_DOCTOR,
    "fabric_operational_snapshot": BridgeAction.FABRIC_OPERATIONAL_SNAPSHOT,
    "fabric_continuity_status": BridgeAction.FABRIC_CONTINUITY_STATUS,
}


class AIfordableRelayError(RuntimeError):
    """Safe relay failure without endpoint, credential or response-body detail."""


class AIfordableRelayProtocolError(AIfordableRelayError):
    """Remote relay data failed strict validation."""


@dataclass(frozen=True, slots=True)
class AIfordableRelayConfig:
    base_url: str
    runner_subject: str
    credential: str
    poll_wait_seconds: int = 15
    request_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        _validate_base_url(self.base_url)
        if _RUNNER_SUBJECT_RE.fullmatch(self.runner_subject) is None:
            raise ValueError("AIfordable relay runner subject is invalid")
        _validate_credential(self.credential)
        if isinstance(self.poll_wait_seconds, bool) or not isinstance(
            self.poll_wait_seconds,
            int,
        ):
            raise TypeError("AIfordable relay poll wait must be an integer")
        if not 0 <= self.poll_wait_seconds <= 20:
            raise ValueError("AIfordable relay poll wait is outside supported range")
        if not 1 <= self.request_timeout_seconds <= 60:
            raise ValueError("AIfordable relay timeout is outside supported range")

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> AIfordableRelayConfig:
        required = {
            "base_url": values.get("RUNNER_MCP_AIFORDABLE_RELAY_URL", ""),
            "runner_subject": values.get(
                "RUNNER_MCP_AIFORDABLE_RUNNER_SUBJECT",
                "",
            ),
            "credential": values.get(
                "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL",
                "",
            ),
        }
        if not all(required.values()):
            raise ValueError("AIfordable relay configuration is incomplete")
        return cls(**required)


@dataclass(frozen=True, slots=True)
class RelayClaim:
    request_id: str
    target_subject: str
    operation: str
    fingerprint: str
    version: int
    owner_generation: int
    issued_at: int
    expires_at: int
    attempt: int
    payload: dict[str, object]

    def __post_init__(self) -> None:
        if REQUEST_ID_RE.fullmatch(self.request_id) is None:
            raise AIfordableRelayProtocolError("relay request identifier is invalid")
        if _RUNNER_SUBJECT_RE.fullmatch(self.target_subject) is None:
            raise AIfordableRelayProtocolError("relay target subject is invalid")
        if self.operation not in _ALLOWED_OPERATIONS:
            raise AIfordableRelayProtocolError("relay operation is unsupported")
        if (
            not isinstance(self.fingerprint, str)
            or len(self.fingerprint) != 64
            or any(char not in "0123456789abcdef" for char in self.fingerprint)
        ):
            raise AIfordableRelayProtocolError("relay fingerprint is invalid")
        for value, label in (
            (self.version, "version"),
            (self.owner_generation, "owner generation"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise AIfordableRelayProtocolError(f"relay {label} is invalid")
        for value, label in (
            (self.issued_at, "issued_at"),
            (self.expires_at, "expires_at"),
            (self.attempt, "attempt"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise AIfordableRelayProtocolError(f"relay {label} is invalid")
        if self.expires_at <= self.issued_at:
            raise AIfordableRelayProtocolError("relay expiry is invalid")
        if self.expires_at - self.issued_at > _MAX_TTL_SECONDS:
            raise AIfordableRelayProtocolError("relay ttl exceeds supported maximum")
        if not isinstance(self.payload, dict) or self.payload:
            raise AIfordableRelayProtocolError(
                "initial relay inspection operation requires an empty payload"
            )

    def bridge_request(self) -> BridgeRequest:
        return BridgeRequest(
            request_id=self.request_id,
            action=_ALLOWED_OPERATIONS[self.operation],
        )


@dataclass(frozen=True, slots=True)
class PendingRelayResult:
    request_id: str
    version: int
    owner_generation: int
    result_json: str

    def __post_init__(self) -> None:
        if REQUEST_ID_RE.fullmatch(self.request_id) is None:
            raise AIfordableRelayProtocolError("pending result request id is invalid")
        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
            or self.version < 1
        ):
            raise AIfordableRelayProtocolError("pending result version is invalid")
        if (
            isinstance(self.owner_generation, bool)
            or not isinstance(self.owner_generation, int)
            or self.owner_generation < 1
        ):
            raise AIfordableRelayProtocolError(
                "pending result owner generation is invalid"
            )
        parse_bridge_result(self.result_json)


class RelayPendingResultStore:
    """Private single-flight durable result spool for crash-safe result delivery."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("relay pending result path must be absolute")
        self._path = path

    def load(self) -> PendingRelayResult | None:
        if not self._path.exists():
            return None
        if self._path.is_symlink() or not self._path.is_file():
            raise AIfordableRelayError("relay pending result file is unsafe")
        try:
            raw = self._path.read_bytes()
        except OSError as exc:
            raise AIfordableRelayError("relay pending result is unavailable") from exc
        if len(raw) > _MAX_HTTP_BYTES:
            raise AIfordableRelayError("relay pending result exceeds size limit")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AIfordableRelayError("relay pending result is corrupt") from exc
        if not isinstance(payload, dict) or set(payload) != {
            "request_id",
            "version",
            "owner_generation",
            "result_json",
        }:
            raise AIfordableRelayError("relay pending result shape is invalid")
        try:
            return PendingRelayResult(**payload)
        except (TypeError, ValueError) as exc:
            raise AIfordableRelayError("relay pending result is invalid") from exc

    def save(self, pending: PendingRelayResult) -> None:
        if self.load() is not None:
            raise AIfordableRelayError("relay pending result already exists")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.parent.is_symlink():
            raise AIfordableRelayError("relay pending result directory is unsafe")
        raw = json.dumps(
            {
                "request_id": pending.request_id,
                "version": pending.version,
                "owner_generation": pending.owner_generation,
                "result_json": pending.result_json,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(raw) > _MAX_HTTP_BYTES:
            raise AIfordableRelayError("relay pending result exceeds size limit")
        fd = -1
        temp = Path()
        try:
            fd, name = tempfile.mkstemp(prefix=".relay-result-", dir=self._path.parent)
            temp = Path(name)
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb", closefd=False) as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self._path)
            os.chmod(self._path, 0o600)
            _fsync_directory(self._path.parent)
        except OSError as exc:
            raise AIfordableRelayError(
                "relay pending result could not be persisted"
            ) from exc
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    def clear(self) -> None:
        if not self._path.exists():
            return
        if self._path.is_symlink() or not self._path.is_file():
            raise AIfordableRelayError("relay pending result file is unsafe")
        try:
            self._path.unlink()
            _fsync_directory(self._path.parent)
        except OSError as exc:
            raise AIfordableRelayError(
                "relay pending result could not be cleared"
            ) from exc


class AIfordableRelayTransport:
    def __init__(self, config: AIfordableRelayConfig) -> None:
        if not isinstance(config, AIfordableRelayConfig):
            raise TypeError("config must be AIfordableRelayConfig")
        self._config = config
        self._base = config.base_url.rstrip("/")

    def claim_next(self) -> RelayClaim | None:
        status_code, raw = self._request(
            method="POST",
            path=(
                "/internal/control-relay/claim"
                f"?wait_seconds={self._config.poll_wait_seconds}"
            ),
            payload=None,
        )
        if status_code == 204:
            return None
        if status_code != 200:
            raise AIfordableRelayError("relay claim request was rejected")
        return _parse_claim(
            raw,
            expected_subject=self._config.runner_subject,
            now_epoch=int(time.time()),
        )

    def publish(self, pending: PendingRelayResult) -> None:
        result = parse_bridge_result(pending.result_json)
        failed = result.state is BridgeResultState.FAILED
        suffix = "fail" if failed else "complete"
        result_code = "bridge_failed" if failed else "completed"
        path = (
            "/internal/control-relay/"
            f"{urllib.parse.quote(pending.request_id, safe='')}/{suffix}"
        )
        payload = {
            "expected_version": pending.version,
            "owner_generation": pending.owner_generation,
            "result_code": result_code,
            "result_payload": result.model_dump(mode="json", exclude_none=False),
        }
        status_code, _ = self._request(
            method="POST",
            path=path,
            payload=payload,
        )
        if status_code != 204:
            raise AIfordableRelayError("relay result acknowledgement was rejected")

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, object] | None,
    ) -> tuple[int, bytes]:
        body = None
        headers = {
            "Accept": "application/json",
            "X-AIfordable-Runner-Credential": self._config.credential,
            "User-Agent": "runner-mcp-aifordable-relay",
        }
        if payload is not None:
            body = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            if len(body) > _MAX_HTTP_BYTES:
                raise AIfordableRelayError("relay request exceeds size limit")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self._base + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._config.request_timeout_seconds,
            ) as response:
                raw = response.read(_MAX_HTTP_BYTES + 1)
                if len(raw) > _MAX_HTTP_BYTES:
                    raise AIfordableRelayError("relay response exceeds size limit")
                return response.status, raw
        except urllib.error.HTTPError as exc:
            raw = exc.read(_MAX_HTTP_BYTES + 1)
            if len(raw) > _MAX_HTTP_BYTES:
                raise AIfordableRelayError("relay response exceeds size limit") from None
            return exc.code, raw
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AIfordableRelayError("AIfordable relay is unavailable") from exc


class AIfordableRelayResultSink(BridgeResultSink):
    def __init__(
        self,
        *,
        transport: AIfordableRelayTransport,
        pending_store: RelayPendingResultStore,
        claim: RelayClaim,
    ) -> None:
        self._transport = transport
        self._pending_store = pending_store
        self._claim = claim

    def persist_result(self, request_id: str, result_json: str) -> None:
        if request_id != self._claim.request_id:
            raise BridgeResultSinkError("relay result request identity mismatch")
        pending = PendingRelayResult(
            request_id=request_id,
            version=self._claim.version,
            owner_generation=self._claim.owner_generation,
            result_json=result_json,
        )
        try:
            existing = self._pending_store.load()
            if existing is None:
                self._pending_store.save(pending)
            elif existing != pending:
                raise AIfordableRelayError("relay pending result conflict")
            self._transport.publish(pending)
        except AIfordableRelayError as exc:
            raise BridgeResultSinkError("relay result could not be persisted") from exc


class AIfordableRelayWorker:
    """Single-flight outbound relay worker backed by the existing BridgeProcessor."""

    def __init__(
        self,
        *,
        transport: AIfordableRelayTransport,
        ledger: BridgeReplayLedger,
        executor: Any,
        pending_store: RelayPendingResultStore,
    ) -> None:
        self._transport = transport
        self._ledger = ledger
        self._executor = executor
        self._pending_store = pending_store

    def once(self) -> BridgeProcessOutcome | None:
        pending = self._pending_store.load()
        if pending is not None:
            self._transport.publish(pending)
            result = parse_bridge_result(pending.result_json)
            request = BridgeRequest(
                request_id=pending.request_id,
                action=result.action,
            )
            self._ledger.complete(request)
            self._pending_store.clear()
            return None

        claim = self._transport.claim_next()
        if claim is None:
            return None
        request = claim.bridge_request()
        sink = AIfordableRelayResultSink(
            transport=self._transport,
            pending_store=self._pending_store,
            claim=claim,
        )
        processor = BridgeProcessor(
            ledger=self._ledger,
            executor=self._executor,
            result_sink=sink,
        )
        outcome = processor.process(
            request.model_dump_json(exclude_none=True),
        )
        if outcome.state is BridgeProcessState.COMPLETED:
            self._pending_store.clear()
        return outcome


def _parse_claim(
    raw: bytes,
    *,
    expected_subject: str,
    now_epoch: int,
) -> RelayClaim:
    if len(raw) > _MAX_HTTP_BYTES:
        raise AIfordableRelayProtocolError("relay claim exceeds size limit")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AIfordableRelayProtocolError("relay claim is invalid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "envelope",
        "fingerprint",
        "version",
        "owner_generation",
    }:
        raise AIfordableRelayProtocolError("relay claim shape is invalid")
    envelope = payload["envelope"]
    if not isinstance(envelope, dict) or set(envelope) != {
        "schema_version",
        "request_id",
        "target_subject",
        "operation",
        "issued_at",
        "expires_at",
        "attempt",
        "payload",
    }:
        raise AIfordableRelayProtocolError("relay envelope shape is invalid")
    if envelope["schema_version"] != _CONTROL_SCHEMA:
        raise AIfordableRelayProtocolError("relay schema is unsupported")
    if envelope["target_subject"] != expected_subject:
        raise AIfordableRelayProtocolError("relay target subject mismatch")

    claim = RelayClaim(
        request_id=envelope["request_id"],
        target_subject=envelope["target_subject"],
        operation=envelope["operation"],
        fingerprint=payload["fingerprint"],
        version=payload["version"],
        owner_generation=payload["owner_generation"],
        issued_at=envelope["issued_at"],
        expires_at=envelope["expires_at"],
        attempt=envelope["attempt"],
        payload=envelope["payload"],
    )
    if claim.expires_at <= now_epoch:
        raise AIfordableRelayProtocolError("relay claim is expired")
    expected_fingerprint = _control_fingerprint(envelope)
    if claim.fingerprint != expected_fingerprint:
        raise AIfordableRelayProtocolError("relay fingerprint mismatch")
    return claim


def _control_fingerprint(envelope: dict[str, object]) -> str:
    encoded = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_base_url(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("AIfordable relay URL must be a string")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("AIfordable relay URL must use HTTP or HTTPS")
    if not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("AIfordable relay URL is invalid")
    if parsed.query or parsed.fragment:
        raise ValueError("AIfordable relay URL must not contain query or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("AIfordable relay URL must not contain an API path")
    loopback = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
    if parsed.scheme != "https" and not loopback:
        raise ValueError("AIfordable relay URL must use HTTPS")


def _validate_credential(value: str) -> None:
    if (
        not isinstance(value, str)
        or not 32 <= len(value) <= 4_096
        or not value.isascii()
        or any(ord(char) < 33 or ord(char) == 127 for char in value)
    ):
        raise ValueError("AIfordable relay credential is invalid")


def _fsync_directory(path: Path) -> None:
    try:
        metadata = path.stat()
        if not stat.S_ISDIR(metadata.st_mode):
            raise AIfordableRelayError("relay result directory is unsafe")
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise AIfordableRelayError("relay result directory could not be synced") from exc
