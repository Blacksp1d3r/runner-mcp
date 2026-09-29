from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

AIFORDABLE_RELAY_ORIGIN_ENV = "RUNNER_MCP_AIFORDABLE_RELAY_ORIGIN"
AIFORDABLE_RELAY_SUBJECT_ENV = "RUNNER_MCP_AIFORDABLE_RELAY_SUBJECT"
AIFORDABLE_RELAY_CREDENTIAL_ENV = "RUNNER_MCP_AIFORDABLE_RELAY_CREDENTIAL"
AIFORDABLE_RELAY_ENV_KEYS = (
    AIFORDABLE_RELAY_ORIGIN_ENV,
    AIFORDABLE_RELAY_SUBJECT_ENV,
    AIFORDABLE_RELAY_CREDENTIAL_ENV,
)

_CONTROL_SCHEMA = "aifordable.control/v1"
_CLAIM_PATH = "/internal/control-relay/claim"
_RESULT_ROUTE_RE = re.compile(
    r"^/internal/control-relay/"
    r"([a-z][a-z0-9._:-]{0,127})/(complete|fail)$"
)
_ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,63}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_BODY_BYTES = 64 * 1024


class AIfordableTransportError(RuntimeError):
    """Bounded transport failure without private endpoint or credential detail."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        self.status = status
        super().__init__(message)


class AIfordableControlOperation(StrEnum):
    RUNTIME_STATUS = "runtime_status"
    RUNTIME_DOCTOR = "runtime_doctor"
    FABRIC_RUN_WORK_UNIT = "fabric_run_work_unit"
    FABRIC_GET_WORK_UNIT = "fabric_get_work_unit"
    FABRIC_CANCEL_WORK_UNIT = "fabric_cancel_work_unit"


@dataclass(frozen=True, slots=True)
class AIfordableRelayConfig:
    origin: str
    subject: str
    credential: str = field(repr=False)
    wait_seconds: int = 15
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        parsed = urlsplit(self.origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("AIfordable relay configuration is invalid")
        _runner_subject(self.subject)
        if (
            not isinstance(self.credential, str)
            or not 32 <= len(self.credential) <= 4096
            or not self.credential.isascii()
            or any(ord(char) < 33 or ord(char) == 127 for char in self.credential)
        ):
            raise ValueError("AIfordable relay configuration is invalid")
        if (
            isinstance(self.wait_seconds, bool)
            or not isinstance(self.wait_seconds, int)
            or not 0 <= self.wait_seconds <= 20
        ):
            raise ValueError("AIfordable relay configuration is invalid")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or not max(1.0, float(self.wait_seconds)) < float(self.timeout_seconds) <= 60.0
        ):
            raise ValueError("AIfordable relay configuration is invalid")

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> AIfordableRelayConfig:
        try:
            return cls(
                origin=values[AIFORDABLE_RELAY_ORIGIN_ENV].strip(),
                subject=values[AIFORDABLE_RELAY_SUBJECT_ENV].strip(),
                credential=values[AIFORDABLE_RELAY_CREDENTIAL_ENV].strip(),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("AIfordable relay configuration is incomplete") from exc


@dataclass(frozen=True, slots=True)
class AIfordableEnvelope:
    request_id: str
    target_subject: str
    operation: AIfordableControlOperation
    issued_at: int
    expires_at: int
    attempt: int
    payload: Mapping[str, object]
    schema_version: str = _CONTROL_SCHEMA

    def __post_init__(self) -> None:
        _identifier(self.request_id, "request_id")
        _runner_subject(self.target_subject)
        if self.schema_version != _CONTROL_SCHEMA:
            raise AIfordableTransportError("control envelope schema is invalid")
        _nonnegative_int(self.issued_at, "issued_at")
        _nonnegative_int(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise AIfordableTransportError("control envelope lifetime is invalid")
        _nonnegative_int(self.attempt, "attempt")
        if not isinstance(self.payload, Mapping):
            raise AIfordableTransportError("control envelope payload is invalid")

    @property
    def fingerprint(self) -> str:
        raw = _json_bytes(
            {
                "schema_version": self.schema_version,
                "request_id": self.request_id,
                "target_subject": self.target_subject,
                "operation": self.operation.value,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
                "attempt": self.attempt,
                "payload": dict(self.payload),
            }
        )
        import hashlib

        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class AIfordableClaim:
    envelope: AIfordableEnvelope
    fingerprint: str
    version: int
    owner_generation: int

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, AIfordableEnvelope):
            raise AIfordableTransportError("relay claim is invalid")
        if (
            not isinstance(self.fingerprint, str)
            or _FINGERPRINT_RE.fullmatch(self.fingerprint) is None
            or self.fingerprint != self.envelope.fingerprint
        ):
            raise AIfordableTransportError("relay claim is invalid")
        _positive_int(self.version, "version")
        _positive_int(self.owner_generation, "owner_generation")


@dataclass(frozen=True, slots=True)
class AIfordableResponse:
    status: int
    body: bytes


class AIfordableExchange(Protocol):
    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> AIfordableResponse: ...


class AIfordableHttpsExchange:
    def __init__(self, config: AIfordableRelayConfig) -> None:
        self._origin = config.origin.rstrip("/")
        self._credential = config.credential

    def post(
        self,
        route: str,
        body: bytes,
        *,
        timeout_seconds: float,
    ) -> AIfordableResponse:
        _validate_route(route)
        if not isinstance(body, bytes) or len(body) > _MAX_BODY_BYTES:
            raise AIfordableTransportError("relay request is invalid")
        headers = {
            "X-AIfordable-Runner-Credential": self._credential,
            "Accept": "application/json",
        }
        if body:
            headers["Content-Type"] = "application/json"
        request = Request(
            self._origin + route,
            data=body,
            method="POST",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read(_MAX_BODY_BYTES + 1)
                if len(raw) > _MAX_BODY_BYTES:
                    raise AIfordableTransportError("relay response is invalid")
                return AIfordableResponse(response.status, raw)
        except HTTPError as exc:
            raw = exc.read(_MAX_BODY_BYTES + 1)
            if len(raw) > _MAX_BODY_BYTES:
                raise AIfordableTransportError("relay response is invalid") from None
            return AIfordableResponse(exc.code, raw)
        except AIfordableTransportError:
            raise
        except (URLError, OSError, TimeoutError) as exc:
            raise AIfordableTransportError("AIfordable relay is unavailable") from exc


class AIfordableRelayClient:
    def __init__(
        self,
        config: AIfordableRelayConfig,
        exchange: AIfordableExchange | None = None,
    ) -> None:
        self._config = config
        self._exchange = (
            AIfordableHttpsExchange(config) if exchange is None else exchange
        )

    def claim_once(self, *, now: int) -> AIfordableClaim | None:
        _nonnegative_int(now, "now")
        response = self._post(
            f"{_CLAIM_PATH}?wait_seconds={self._config.wait_seconds}",
            b"",
        )
        if response.status == 204:
            if response.body:
                raise AIfordableTransportError("relay response is invalid")
            return None
        _require_status(response, 200)
        claim = _decode_claim(response.body)
        if claim.envelope.target_subject != self._config.subject:
            raise AIfordableTransportError("relay claim target is invalid")
        if now >= claim.envelope.expires_at:
            raise AIfordableTransportError("relay claim is expired")
        return claim

    def complete(
        self,
        claim: AIfordableClaim,
        *,
        result_code: str,
        result_payload: Mapping[str, object],
    ) -> None:
        self._submit_result(
            claim,
            action="complete",
            result_code=result_code,
            result_payload=result_payload,
        )

    def fail(
        self,
        claim: AIfordableClaim,
        *,
        result_code: str,
        result_payload: Mapping[str, object],
    ) -> None:
        self._submit_result(
            claim,
            action="fail",
            result_code=result_code,
            result_payload=result_payload,
        )

    def _submit_result(
        self,
        claim: AIfordableClaim,
        *,
        action: str,
        result_code: str,
        result_payload: Mapping[str, object],
    ) -> None:
        if claim.envelope.target_subject != self._config.subject:
            raise AIfordableTransportError("relay claim target is invalid")
        self.submit_terminal_result(
            request_id=claim.envelope.request_id,
            expected_version=claim.version,
            owner_generation=claim.owner_generation,
            action=action,
            result_code=result_code,
            result_payload=result_payload,
        )

    def submit_terminal_result(
        self,
        *,
        request_id: str,
        expected_version: int,
        owner_generation: int,
        action: str,
        result_code: str,
        result_payload: Mapping[str, object],
    ) -> None:
        request_id = _identifier(request_id, "request_id")
        _positive_int(expected_version, "expected_version")
        _positive_int(owner_generation, "owner_generation")
        if action not in {"complete", "fail"}:
            raise AIfordableTransportError("terminal action is invalid")
        code = _result_code(result_code)
        payload = _safe_result_payload(result_payload)
        response = self._post(
            f"/internal/control-relay/{request_id}/{action}",
            _json_bytes(
                {
                    "expected_version": expected_version,
                    "owner_generation": owner_generation,
                    "result_code": code,
                    "result_payload": payload,
                }
            ),
        )
        _require_status(response, 204)
        if response.body:
            raise AIfordableTransportError("relay response is invalid")

    def _post(self, route: str, body: bytes) -> AIfordableResponse:
        try:
            response = self._exchange.post(
                route,
                body,
                timeout_seconds=float(self._config.timeout_seconds),
            )
        except AIfordableTransportError:
            raise
        except (OSError, TimeoutError, ValueError) as exc:
            raise AIfordableTransportError("AIfordable relay is unavailable") from exc
        if not isinstance(response, AIfordableResponse):
            raise AIfordableTransportError("relay response is invalid")
        return response


def reconnect_delay_seconds(failure_count: int) -> float:
    if (
        isinstance(failure_count, bool)
        or not isinstance(failure_count, int)
        or failure_count < 1
    ):
        raise ValueError("failure_count must be a positive integer")
    return min(60.0, 2.0 ** min(failure_count - 1, 6))


def _decode_claim(raw: bytes) -> AIfordableClaim:
    payload = _json_object(raw)
    if set(payload) != {
        "envelope",
        "fingerprint",
        "version",
        "owner_generation",
    }:
        raise AIfordableTransportError("relay response is invalid")
    envelope_raw = payload["envelope"]
    if not isinstance(envelope_raw, dict) or set(envelope_raw) != {
        "schema_version",
        "request_id",
        "target_subject",
        "operation",
        "issued_at",
        "expires_at",
        "attempt",
        "payload",
    }:
        raise AIfordableTransportError("relay response is invalid")
    try:
        envelope = AIfordableEnvelope(
            schema_version=envelope_raw["schema_version"],
            request_id=envelope_raw["request_id"],
            target_subject=envelope_raw["target_subject"],
            operation=AIfordableControlOperation(envelope_raw["operation"]),
            issued_at=envelope_raw["issued_at"],
            expires_at=envelope_raw["expires_at"],
            attempt=envelope_raw["attempt"],
            payload=envelope_raw["payload"],
        )
        return AIfordableClaim(
            envelope=envelope,
            fingerprint=payload["fingerprint"],
            version=payload["version"],
            owner_generation=payload["owner_generation"],
        )
    except (TypeError, ValueError, AIfordableTransportError) as exc:
        raise AIfordableTransportError("relay response is invalid") from exc


def _safe_result_payload(value: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise AIfordableTransportError("result payload is invalid")
    payload = dict(value)
    forbidden = {
        "token",
        "secret",
        "credential",
        "password",
        "authorization",
        "private_key",
    }
    stack: list[object] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    raise AIfordableTransportError("result payload is invalid")
                if any(fragment in key.casefold() for fragment in forbidden):
                    raise AIfordableTransportError("result payload is invalid")
                stack.append(item)
        elif isinstance(current, list):
            stack.extend(current)
        elif current is not None and not isinstance(
            current,
            (str, int, float, bool),
        ):
            raise AIfordableTransportError("result payload is invalid")
    return _json_object(_json_bytes(payload))


def _json_object(raw: bytes) -> dict[str, object]:
    if not isinstance(raw, bytes) or not raw or len(raw) > _MAX_BODY_BYTES:
        raise AIfordableTransportError("relay response is invalid")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AIfordableTransportError("relay response is invalid") from exc
    if not isinstance(payload, dict):
        raise AIfordableTransportError("relay response is invalid")
    return payload


def _json_bytes(value: object) -> bytes:
    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AIfordableTransportError("relay request is invalid") from exc
    if len(raw) > _MAX_BODY_BYTES:
        raise AIfordableTransportError("relay request is invalid")
    return raw


def _validate_route(route: str) -> None:
    if not isinstance(route, str):
        raise AIfordableTransportError("relay route is not allowed")
    prefix = f"{_CLAIM_PATH}?wait_seconds="
    if route.startswith(prefix):
        suffix = route.removeprefix(prefix)
        if suffix.isdigit() and 0 <= int(suffix) <= 20:
            return
    if _RESULT_ROUTE_RE.fullmatch(route):
        return
    raise AIfordableTransportError("relay route is not allowed")


def _require_status(response: AIfordableResponse, expected: int) -> None:
    if response.status == expected:
        return
    messages = {
        401: "AIfordable relay authentication was rejected",
        403: "AIfordable relay authorization was rejected",
        409: "AIfordable relay state conflicted",
        503: "AIfordable relay identity service is unavailable",
    }
    raise AIfordableTransportError(
        messages.get(response.status, "relay response is invalid"),
        status=response.status,
    )


def _runner_subject(value: object) -> str:
    subject = _identifier(value, "runner subject")
    if not subject.startswith("runner:"):
        raise ValueError("runner subject is invalid")
    return subject


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} is invalid")
    return value


def _result_code(value: object) -> str:
    if not isinstance(value, str) or _CODE_RE.fullmatch(value) is None:
        raise AIfordableTransportError("result code is invalid")
    return value


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be positive")
    return value


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value
