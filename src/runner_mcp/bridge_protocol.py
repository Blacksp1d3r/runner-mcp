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
    SYNC_PROJECT = "sync_project"
    LIST_TEST_PROFILES = "list_test_profiles"
    RUN_TESTS = "run_tests"
    QUEUE_STATUS = "queue_status"
    WORKER_STATUS = "worker_status"
    JOB_STATUS = "job_status"
    CANCEL_JOB = "cancel_job"
    JOB_LOG = "job_log"
    LIST_SERVICES = "list_services"
    SERVICE_STATUS = "service_status"
    START_SERVICE = "start_service"
    STOP_SERVICE = "stop_service"
    RESTART_SERVICE = "restart_service"
    LIST_BACKUPS = "list_backups"
    BACKUP_DATABASE = "backup_database"
    REQUEST_ACTION_APPROVAL = "request_action_approval"
    APPROVAL_STATUS = "approval_status"
    MIGRATION_STATUS = "migration_status"
    APPLY_MIGRATIONS = "apply_migrations"
    PLAN_DEPLOY = "plan_deploy"
    DEPLOY_STAGING = "deploy_staging"
    DEPLOYMENT_STATUS = "deployment_status"
    LIST_RELEASES = "list_releases"
    ROLLBACK_PLAN = "rollback_plan"
    ROLLBACK_RELEASE = "rollback_release"
    ROLLBACK_STATUS = "rollback_status"
    RUNTIME_STATUS = "runtime_status"
    RUNTIME_DOCTOR = "runtime_doctor"
    SELF_UPDATE = "self_update"
    SELF_UPDATE_STATUS = "self_update_status"


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
    commit: str | None = Field(default=None, min_length=40, max_length=40)
    job_id: str | None = Field(default=None, min_length=1, max_length=64)
    service: str | None = Field(default=None, min_length=1, max_length=80)
    approval_id: str | None = Field(default=None, min_length=1, max_length=64)
    operation: str | None = Field(default=None, min_length=1, max_length=32)
    offset: int | None = Field(default=None, ge=0, le=100_000)
    length: int | None = Field(default=None, ge=1, le=100)
    limit: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_action_arguments(self) -> BridgeRequest:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id contains unsupported characters")

        if self.project is not None and not PROJECT_CODE_RE.fullmatch(self.project):
            raise ValueError("project contains unsupported characters")

        if self.profile is not None and not PROJECT_CODE_RE.fullmatch(self.profile):
            raise ValueError("profile contains unsupported characters")

        if self.commit is not None and not re.fullmatch(r"[0-9a-fA-F]{40}", self.commit):
            raise ValueError("commit must be a full Git object ID")

        if self.job_id is not None and not JOB_ID_RE.fullmatch(self.job_id):
            raise ValueError("job_id contains unsupported characters")

        if self.service is not None and not PROJECT_CODE_RE.fullmatch(self.service):
            raise ValueError("service contains unsupported characters")

        if self.approval_id is not None and not JOB_ID_RE.fullmatch(self.approval_id):
            raise ValueError("approval_id contains unsupported characters")

        if self.operation is not None and self.operation not in {
            "migration",
            "deploy",
            "code_rollback",
        }:
            raise ValueError("operation is unsupported")

        extra_operational = (
            self.service,
            self.approval_id,
            self.operation,
            self.offset,
            self.length,
            self.limit,
        )

        if self.action in {
            BridgeAction.LIST_PROJECTS,
            BridgeAction.SAFETY_STATUS,
            BridgeAction.QUEUE_STATUS,
            BridgeAction.WORKER_STATUS,
            BridgeAction.RUNTIME_STATUS,
            BridgeAction.RUNTIME_DOCTOR,
        }:
            if (
                self.project is not None
                or self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError(f"{self.action.value} does not accept arguments")
            return self

        if self.action in {
            BridgeAction.PROJECT_STATUS,
            BridgeAction.PROJECT_CAPABILITIES,
            BridgeAction.LIST_TEST_PROFILES,
        }:
            if self.project is None:
                raise ValueError(f"{self.action.value} requires project")
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError(f"{self.action.value} accepts only project")
            return self

        if self.action == BridgeAction.SYNC_PROJECT:
            if self.project is None or self.commit is None:
                raise ValueError("sync_project requires project and commit")
            if (
                self.profile is not None
                or self.job_id is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError("sync_project accepts only project and commit")
            return self

        if self.action == BridgeAction.SELF_UPDATE:
            if self.commit is None:
                raise ValueError("self_update requires commit")
            if not re.fullmatch(r"[0-9a-f]{40}", self.commit):
                raise ValueError("self_update requires a full lowercase commit")
            if (
                self.project is not None
                or self.profile is not None
                or self.job_id is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError("self_update accepts only commit")
            return self

        if self.action == BridgeAction.RUN_TESTS:
            if self.project is None or self.profile is None:
                raise ValueError("run_tests requires project and profile")
            if (
                self.commit is not None
                or self.job_id is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError("run_tests accepts only project and profile")
            return self

        if self.action in {BridgeAction.JOB_STATUS, BridgeAction.CANCEL_JOB}:
            if self.job_id is None:
                raise ValueError(f"{self.action.value} requires job_id")
            if (
                self.project is not None
                or self.profile is not None
                or self.commit is not None
                or any(value is not None for value in extra_operational)
            ):
                raise ValueError(f"{self.action.value} accepts only job_id")
            return self

        if self.action == BridgeAction.JOB_LOG:
            if self.job_id is None:
                raise ValueError("job_log requires job_id")
            if (
                self.project is not None
                or self.profile is not None
                or self.commit is not None
                or self.service is not None
                or self.approval_id is not None
                or self.operation is not None
                or self.limit is not None
            ):
                raise ValueError("job_log accepts only job_id, offset and length")
            return self

        if self.action in {
            BridgeAction.LIST_SERVICES,
            BridgeAction.BACKUP_DATABASE,
            BridgeAction.MIGRATION_STATUS,
            BridgeAction.PLAN_DEPLOY,
            BridgeAction.ROLLBACK_PLAN,
        }:
            if self.project is None:
                raise ValueError(f"{self.action.value} requires project")
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.service is not None
                or self.approval_id is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
                raise ValueError(f"{self.action.value} accepts only project")
            return self

        if self.action in {
            BridgeAction.SERVICE_STATUS,
            BridgeAction.START_SERVICE,
            BridgeAction.STOP_SERVICE,
            BridgeAction.RESTART_SERVICE,
        }:
            if self.project is None or self.service is None:
                raise ValueError(f"{self.action.value} requires project and service")
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.approval_id is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
                raise ValueError(
                    f"{self.action.value} accepts only project and service"
                )
            return self

        if self.action in {BridgeAction.LIST_BACKUPS, BridgeAction.LIST_RELEASES}:
            if self.project is None:
                raise ValueError(f"{self.action.value} requires project")
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.service is not None
                or self.approval_id is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
            ):
                raise ValueError(
                    f"{self.action.value} accepts only project and optional limit"
                )
            return self

        if self.action == BridgeAction.REQUEST_ACTION_APPROVAL:
            if self.project is None or self.operation is None:
                raise ValueError(
                    "request_action_approval requires project and operation"
                )
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.service is not None
                or self.approval_id is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
                raise ValueError(
                    "request_action_approval accepts only project and operation"
                )
            return self

        if self.action == BridgeAction.APPROVAL_STATUS:
            if self.approval_id is None:
                raise ValueError("approval_status requires approval_id")
            if (
                self.project is not None
                or self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.service is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
                raise ValueError("approval_status accepts only approval_id")
            return self

        if self.action in {
            BridgeAction.APPLY_MIGRATIONS,
            BridgeAction.DEPLOY_STAGING,
            BridgeAction.ROLLBACK_RELEASE,
        }:
            if self.project is None or self.approval_id is None:
                raise ValueError(
                    f"{self.action.value} requires project and approval_id"
                )
            if (
                self.profile is not None
                or self.commit is not None
                or self.job_id is not None
                or self.service is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
                raise ValueError(
                    f"{self.action.value} accepts only project and approval_id"
                )
            return self

        if self.action in {
            BridgeAction.DEPLOYMENT_STATUS,
            BridgeAction.ROLLBACK_STATUS,
        }:
            if self.job_id is None:
                raise ValueError(f"{self.action.value} requires job_id")
            if (
                self.project is not None
                or self.profile is not None
                or self.commit is not None
                or self.service is not None
                or self.approval_id is not None
                or self.operation is not None
                or self.offset is not None
                or self.length is not None
                or self.limit is not None
            ):
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


def bridge_tool_call(request: BridgeRequest) -> tuple[str, dict[str, str | int]]:
    if request.action in {
        BridgeAction.LIST_PROJECTS,
        BridgeAction.SAFETY_STATUS,
        BridgeAction.QUEUE_STATUS,
        BridgeAction.WORKER_STATUS,
        BridgeAction.RUNTIME_STATUS,
        BridgeAction.RUNTIME_DOCTOR,
    }:
        return request.action.value, {}

    if request.action in {
        BridgeAction.PROJECT_STATUS,
        BridgeAction.PROJECT_CAPABILITIES,
        BridgeAction.LIST_TEST_PROFILES,
    }:
        assert request.project is not None
        return request.action.value, {"project": request.project}

    if request.action == BridgeAction.SYNC_PROJECT:
        assert request.project is not None
        assert request.commit is not None
        return request.action.value, {
            "project": request.project,
            "commit": request.commit,
        }

    if request.action == BridgeAction.SELF_UPDATE:
        assert request.commit is not None
        return request.action.value, {"commit": request.commit}

    if request.action == BridgeAction.RUN_TESTS:
        assert request.project is not None
        assert request.profile is not None
        return request.action.value, {
            "project": request.project,
            "suite": request.profile,
        }

    if request.action in {
        BridgeAction.JOB_STATUS,
        BridgeAction.CANCEL_JOB,
        BridgeAction.DEPLOYMENT_STATUS,
        BridgeAction.ROLLBACK_STATUS,
        BridgeAction.SELF_UPDATE_STATUS,
    }:
        assert request.job_id is not None
        return request.action.value, {"job_id": request.job_id}

    if request.action == BridgeAction.JOB_LOG:
        assert request.job_id is not None
        arguments: dict[str, str | int] = {"job_id": request.job_id}
        if request.offset is not None:
            arguments["offset"] = request.offset
        if request.length is not None:
            arguments["length"] = request.length
        return request.action.value, arguments

    if request.action in {
        BridgeAction.LIST_SERVICES,
        BridgeAction.BACKUP_DATABASE,
        BridgeAction.MIGRATION_STATUS,
        BridgeAction.PLAN_DEPLOY,
        BridgeAction.ROLLBACK_PLAN,
    }:
        assert request.project is not None
        return request.action.value, {"project": request.project}

    if request.action in {
        BridgeAction.SERVICE_STATUS,
        BridgeAction.START_SERVICE,
        BridgeAction.STOP_SERVICE,
        BridgeAction.RESTART_SERVICE,
    }:
        assert request.project is not None
        assert request.service is not None
        return request.action.value, {
            "project": request.project,
            "service": request.service,
        }

    if request.action in {BridgeAction.LIST_BACKUPS, BridgeAction.LIST_RELEASES}:
        assert request.project is not None
        arguments = {"project": request.project}
        if request.limit is not None:
            arguments["limit"] = request.limit
        return request.action.value, arguments

    if request.action == BridgeAction.REQUEST_ACTION_APPROVAL:
        assert request.project is not None
        assert request.operation is not None
        return request.action.value, {
            "project": request.project,
            "action": request.operation,
        }

    if request.action == BridgeAction.APPROVAL_STATUS:
        assert request.approval_id is not None
        return request.action.value, {"approval_id": request.approval_id}

    if request.action in {
        BridgeAction.APPLY_MIGRATIONS,
        BridgeAction.DEPLOY_STAGING,
        BridgeAction.ROLLBACK_RELEASE,
    }:
        assert request.project is not None
        assert request.approval_id is not None
        return request.action.value, {
            "project": request.project,
            "approval_id": request.approval_id,
        }

    raise BridgeProtocolError("unsupported bridge action")
