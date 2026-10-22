"""Fixed Black runtime-status issuer evidence boundary (#341).

Runner-MCP does not own the relay or operator authentication. Fabric must route
through the existing AIfordable MFA operator issuer; these validators only
correlate and sanitize its authenticated response, never manufacture identity.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping

_TARGET = "runner:black"
_OPERATION = "runtime_status"
_ID = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_STATES = frozenset({"queued", "claimed", "completed", "failed"})
_FORBIDDEN = ("authorization", "credential", "password", "private_key", "secret", "token")


class BlackControlEvidenceError(ValueError):
    """Malformed or mismatched first-party issuer proof, without private data."""


def _ident(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _digest(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _bounded_result(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise BlackControlEvidenceError("invalid terminal result")
    seen = 0
    stack: list[tuple[object, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        seen += 1
        if seen > 256 or depth > 8:
            raise BlackControlEvidenceError("invalid terminal result")
        if isinstance(item, dict):
            for key, child in item.items():
                if type(key) is not str or len(key) > 128:
                    raise BlackControlEvidenceError("invalid terminal result")
                if any(part in key.casefold() for part in _FORBIDDEN):
                    raise BlackControlEvidenceError("invalid terminal result")
                stack.append((child, depth + 1))
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif item is not None and type(item) not in (str, int, float, bool):
            raise BlackControlEvidenceError("invalid terminal result")
    try:
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise BlackControlEvidenceError("invalid terminal result") from exc
    if len(raw) > 16384:
        raise BlackControlEvidenceError("invalid terminal result")
    return value


def validate_black_record(
    raw: object,
    *,
    request_id: str | None = None,
    fingerprint: str | None = None,
    requester_subject: str | None = None,
) -> dict[str, object]:
    """Validate existing operator REST/Fabric evidence and original receipt binding.

    A caller's expected requester is a correlation check, not authentication.
    The Fabric adapter MUST enforce the authenticating MFA issuer at the relay.
    """
    if not isinstance(raw, Mapping):
        raise BlackControlEvidenceError("invalid control evidence")
    needed = {
        "request_id", "target_subject", "operation", "fingerprint", "state",
        "version", "owner_generation", "result_digest", "requester_acknowledged",
        "result_code", "result_payload", "requested_by_subject",
        "requested_by_auth_strength",
    }
    if not needed.issubset(raw):
        raise BlackControlEvidenceError("incomplete control evidence")
    rid, sub, fp = raw["request_id"], raw["requested_by_subject"], raw["fingerprint"]
    if (
        not _ident(rid) or raw["target_subject"] != _TARGET
        or raw["operation"] != _OPERATION or not _digest(fp)
        or type(sub) is not str or not 1 <= len(sub) <= 255
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in sub)
        or raw["requested_by_auth_strength"] != "mfa"
        or type(raw["state"]) is not str or raw["state"] not in _STATES
        or type(raw["version"]) is not int or raw["version"] < 1
        or type(raw["owner_generation"]) is not int or raw["owner_generation"] < 0
        or type(raw["requester_acknowledged"]) is not bool
    ):
        raise BlackControlEvidenceError("invalid control evidence")
    if (
        (request_id is not None and rid != request_id)
        or (fingerprint is not None and fp != fingerprint)
        or (requester_subject is not None and sub != requester_subject)
    ):
        raise BlackControlEvidenceError("original issuer receipt mismatch")
    state = raw["state"]
    generation = raw["owner_generation"]
    # The real relay has no worker claim while queued. Claimed/terminal
    # commands MUST have a positively fenced target-worker generation.
    # A fabricated terminal result with generation=0 is not proof of Black.
    if (state == "queued" and generation != 0) or (
        state != "queued" and generation < 1
    ):
        raise BlackControlEvidenceError("incoherent worker claim generation")
    terminal = state in {"completed", "failed"}
    code, payload, digest = raw["result_code"], raw["result_payload"], raw["result_digest"]
    if terminal:
        if not _ident(code) or not _digest(digest):
            raise BlackControlEvidenceError("invalid terminal digest")
        clean_result = _bounded_result(payload)
    else:
        if code is not None or payload is not None or digest is not None:
            raise BlackControlEvidenceError("premature terminal data")
        if raw["requester_acknowledged"]:
            raise BlackControlEvidenceError("premature acknowledgement")
        clean_result = None
    return {
        "request_id": rid,
        "target_subject": _TARGET,
        "operation": _OPERATION,
        "fingerprint": fp,
        "requested_by_subject": sub,
        "requested_by_auth_strength": "mfa",
        "state": raw["state"],
        "version": raw["version"],
        "owner_generation": raw["owner_generation"],
        "result_code": code,
        "result_payload": clean_result,
        "result_digest": digest,
        "requester_acknowledged": raw["requester_acknowledged"],
    }


def validate_black_ack(raw: object, *, status: Mapping[str, object]) -> dict[str, object]:
    """Check the explicit requester ACK receipt against the proven terminal result."""
    if not isinstance(raw, Mapping):
        raise BlackControlEvidenceError("invalid control acknowledgement")
    if (
        raw.get("state") != "authenticated-requester-ack"
        or raw.get("request_id") != status["request_id"]
        or raw.get("result_digest") != status["result_digest"]
        or type(raw.get("result_version")) is not int
        or raw["result_version"] != status["version"]
        or type(raw.get("acknowledged_at")) is not str
        or not 1 <= len(raw["acknowledged_at"]) <= 64
    ):
        raise BlackControlEvidenceError("control acknowledgement mismatch")
    return {
        "request_id": status["request_id"],
        "target_subject": _TARGET,
        "operation": _OPERATION,
        "fingerprint": status["fingerprint"],
        "requested_by_subject": status["requested_by_subject"],
        "result_digest": status["result_digest"],
        "result_version": status["version"],
        "state": "authenticated-requester-ack",
    }
