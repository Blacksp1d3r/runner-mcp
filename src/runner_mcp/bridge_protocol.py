from __future__ import annotations

import json
import math
import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_core import PydanticSerializationError

from .config import PROJECT_CODE_RE

MAX_BRIDGE_REQUEST_BYTES = 8_192
MAX_BRIDGE_RESULT_BYTES = 32_768
MAX_RESULT_STRING_CHARS = 2_048
MAX_RESULT_COLLECTION_ITEMS = 256
MAX_RESULT_DEPTH = 6
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
RESULT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
ERROR_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")
_SENSITIVE_RESULT_KEY_TOKENS = {
    "authorization",
    "command",
    "cookie",
    "credential",
    "credentials",
    "dsn",
    "endpoint",
    "env",
    "environment",
    "executable",
    "host",
    "hostname",
    "password",
    "path",
    "secret",
    "token",
    "unit",
    "url",
}
_SENSITIVE_RESULT_KEY_NAMES = {
    "private_key",
    "privatekey",
}


class BridgeProtocolError(ValueError):
    """Raised when a mailbox request or result fails strict protocol validation."""


class BridgeAction(StrEnum):
    LIST_PROJECTS = "list_projects"
    SAFETY_STATUS = "safety_status"
    PROJECT_STATUS = "project_status"
    PROJECT_CAPABILITIES = "project_capabilities"
    LIST_TEST_PROFILES = "list_test_profiles"
    RUN_TESTS = "run_tests"
    QUEUE_STATUS = "queue_status"
    WORKER_STATUS = "worker_status"
    JOB_STATUS = "job_status"
    CANCEL_JOB = "cancel_job"


class BridgeResultState(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class BridgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=64)
    action: BridgeAction
    project: str | None = Field(default=None, min_length=1, max_length=80)
    profile: str | None = Field(default=None, min_length=1, max_length=80)
    job_id: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_action_arguments(self) -> BridgeRequest:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id contains unsupported characters")

        if self.project is not None and not PROJECT_CODE_RE.fullmatch(self.project):
            raise ValueError("project contains unsupported characters")

        if self.profile is not None and not PROJECT_CODE_RE.fullmatch(self.profile):
            raise ValueError("profile contains unsupported characters")

        if self.job_id is not None and not JOB_ID_RE.fullmatch(self.job_id):
            raise ValueError("job_id contains unsupported characters")

        if self.action in {
            BridgeAction.LIST_PROJECTS,
            BridgeAction.SAFETY_STATUS,
            BridgeAction.QUEUE_STATUS,
            BridgeAction.WORKER_STATUS,
        }:
            if self.project is not None or self.profile is not None or self.job_id is not None:
                raise ValueError(f"{self.action.value} does not accept arguments")
            return self

        if self.action in {
            BridgeAction.PROJECT_STATUS,
            BridgeAction.PROJECT_CAPABILITIES,
            BridgeAction.LIST_TEST_PROFILES,
        }:
            if self.project is None:
                raise ValueError(f"{self.action.value} requires project")
            if self.profile is not None or self.job_id is not None:
                raise ValueError(f"{self.action.value} accepts only project")
            return self

        if self.action == BridgeAction.RUN_TESTS:
            if self.project is None or self.profile is None:
                raise ValueError("run_tests requires project and profile")
            if self.job_id is not None:
                raise ValueError("run_tests does not accept job_id")
            return self

        if self.action in {BridgeAction.JOB_STATUS, BridgeAction.CANCEL_JOB}:
            if self.job_id is None:
                raise ValueError(f"{self.action.value} requires job_id")
            if self.project is not None or self.profile is not None:
                raise ValueError(f"{self.action.value} accepts only job_id")
            return self

        raise ValueError("unsupported bridge action")



class BridgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=64)
    action: BridgeAction
    state: BridgeResultState
    data: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, min_length=1, max_length=64)
    summary: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def validate_result(self) -> BridgeResult:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id contains unsupported characters")

        if self.error_code is not None and not ERROR_CODE_RE.fullmatch(self.error_code):
            raise ValueError("error_code contains unsupported characters")

        if self.summary is not None and any(ord(char) < 32 for char in self.summary):
            raise ValueError("summary contains control characters")

        if self.state == BridgeResultState.COMPLETED:
            if self.error_code is not None:
                raise ValueError("completed result must not contain error_code")
            return self

        if self.state == BridgeResultState.FAILED:
            if self.data is not None:
                raise ValueError("failed result must not contain data")
            if self.error_code is None:
                raise ValueError("failed result requires error_code")
            return self

        raise ValueError("unsupported bridge result state")


def _reject_nonstandard_json_constant(value: str) -> None:
    raise BridgeProtocolError(f"bridge payload contains non-standard JSON constant: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BridgeProtocolError("bridge payload contains duplicate JSON keys")
        result[key] = value
    return result


def _decode_json_payload(
    payload: str | bytes,
    *,
    max_bytes: int,
    description: str,
) -> Any:
    if isinstance(payload, bytes):
        if len(payload) > max_bytes:
            raise BridgeProtocolError(f"{description} exceeds size limit")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BridgeProtocolError(f"{description} must be UTF-8") from exc
    else:
        text = payload
        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise BridgeProtocolError(f"{description} must be UTF-8") from exc
        if len(encoded) > max_bytes:
            raise BridgeProtocolError(f"{description} exceeds size limit")

    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except BridgeProtocolError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise BridgeProtocolError(f"{description} is not valid JSON") from exc


def parse_bridge_request(payload: str | bytes) -> BridgeRequest:
    raw = _decode_json_payload(
        payload,
        max_bytes=MAX_BRIDGE_REQUEST_BYTES,
        description="bridge request",
    )

    if not isinstance(raw, dict):
        raise BridgeProtocolError("bridge request must be a JSON object")

    try:
        return BridgeRequest.model_validate(raw)
    except ValidationError as exc:
        raise BridgeProtocolError("bridge request failed strict validation") from exc


def _is_sensitive_result_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_").replace(".", "_")
    if normalized in _SENSITIVE_RESULT_KEY_NAMES:
        return True
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & _SENSITIVE_RESULT_KEY_TOKENS)


def _looks_like_private_location(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(("/", "~/", "\\")):
        return True
    if _WINDOWS_ABSOLUTE_PATH_RE.match(stripped):
        return True
    return "://" in stripped


def sanitize_bridge_result_data(data: dict[str, Any]) -> dict[str, Any]:
    collection_items = 0

    def sanitize(value: Any, *, depth: int) -> Any:
        nonlocal collection_items

        if depth > MAX_RESULT_DEPTH:
            raise BridgeProtocolError("bridge result exceeds nesting limit")

        if value is None or isinstance(value, (bool, int)):
            return value

        if isinstance(value, float):
            if not math.isfinite(value):
                raise BridgeProtocolError("bridge result contains non-finite number")
            return value

        if isinstance(value, str):
            if len(value) > MAX_RESULT_STRING_CHARS:
                return value[:MAX_RESULT_STRING_CHARS] + "..."
            if _looks_like_private_location(value):
                return "[redacted]"
            return value

        if isinstance(value, list):
            collection_items += len(value)
            if collection_items > MAX_RESULT_COLLECTION_ITEMS:
                raise BridgeProtocolError("bridge result contains too many collection items")
            return [sanitize(item, depth=depth + 1) for item in value]

        if isinstance(value, dict):
            collection_items += len(value)
            if collection_items > MAX_RESULT_COLLECTION_ITEMS:
                raise BridgeProtocolError("bridge result contains too many collection items")

            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str) or not RESULT_KEY_RE.fullmatch(key):
                    raise BridgeProtocolError("bridge result contains unsupported key")
                if _is_sensitive_result_key(key):
                    sanitized[key] = "[redacted]"
                else:
                    sanitized[key] = sanitize(item, depth=depth + 1)
            return sanitized

        raise BridgeProtocolError("bridge result contains unsupported value type")

    return sanitize(data, depth=0)


def serialize_bridge_result(result: BridgeResult) -> str:
    try:
        raw = result.model_dump(mode="json", exclude_none=True)
    except PydanticSerializationError as exc:
        raise BridgeProtocolError(
            "bridge result contains unsupported value type"
        ) from exc
    if result.data is not None:
        raw["data"] = sanitize_bridge_result_data(result.data)

    encoded = json.dumps(
        raw,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > MAX_BRIDGE_RESULT_BYTES:
        raise BridgeProtocolError("bridge result exceeds size limit")
    return encoded.decode("utf-8")


def parse_bridge_result(payload: str | bytes) -> BridgeResult:
    raw = _decode_json_payload(
        payload,
        max_bytes=MAX_BRIDGE_RESULT_BYTES,
        description="bridge result",
    )

    if not isinstance(raw, dict):
        raise BridgeProtocolError("bridge result must be a JSON object")

    try:
        result = BridgeResult.model_validate(raw)
    except ValidationError as exc:
        raise BridgeProtocolError("bridge result failed strict validation") from exc

    if result.data is not None:
        safe_data = sanitize_bridge_result_data(result.data)
        result = result.model_copy(update={"data": safe_data})
    return result


def bridge_tool_call(request: BridgeRequest) -> tuple[str, dict[str, str]]:
    if request.action in {
        BridgeAction.LIST_PROJECTS,
        BridgeAction.SAFETY_STATUS,
        BridgeAction.QUEUE_STATUS,
        BridgeAction.WORKER_STATUS,
    }:
        return request.action.value, {}

    if request.action in {
        BridgeAction.PROJECT_STATUS,
        BridgeAction.PROJECT_CAPABILITIES,
        BridgeAction.LIST_TEST_PROFILES,
    }:
        assert request.project is not None
        return request.action.value, {"project": request.project}

    if request.action == BridgeAction.RUN_TESTS:
        assert request.project is not None
        assert request.profile is not None
        return request.action.value, {
            "project": request.project,
            "suite": request.profile,
        }

    if request.action in {BridgeAction.JOB_STATUS, BridgeAction.CANCEL_JOB}:
        assert request.job_id is not None
        return request.action.value, {"job_id": request.job_id}

    raise BridgeProtocolError("unsupported bridge action")
