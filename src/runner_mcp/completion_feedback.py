from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

MAX_COMPLETION_EVENT_BYTES = 2_048
COMPLETION_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
COMPLETION_EVENT_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class CompletionFeedbackError(ValueError):
    """Raised when a completion-feedback payload fails strict validation."""


class CompletionSource(StrEnum):
    MAILBOX_RESULT = "mailbox_result"
    TEST_JOB = "test_job"
    MIGRATION_JOB = "migration_job"
    DEPLOYMENT_JOB = "deployment_job"
    ROLLBACK_JOB = "rollback_job"


class CompletionOperation(StrEnum):
    RUN_TESTS = "run_tests"
    APPLY_MIGRATION = "apply_migration"
    DEPLOY_STAGING = "deploy_staging"
    ROLLBACK_RELEASE = "rollback_release"


class CompletionState(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


_SOURCE_OPERATIONS = {
    CompletionSource.MAILBOX_RESULT: {CompletionOperation.RUN_TESTS},
    CompletionSource.TEST_JOB: {CompletionOperation.RUN_TESTS},
    CompletionSource.MIGRATION_JOB: {CompletionOperation.APPLY_MIGRATION},
    CompletionSource.DEPLOYMENT_JOB: {CompletionOperation.DEPLOY_STAGING},
    CompletionSource.ROLLBACK_JOB: {CompletionOperation.ROLLBACK_RELEASE},
}


@dataclass(frozen=True, slots=True)
class CompletionEvent:
    event_id: str
    source: CompletionSource
    operation: CompletionOperation
    project: str
    state: CompletionState
    profile: str | None = None

    def __post_init__(self) -> None:
        if not COMPLETION_EVENT_ID_RE.fullmatch(self.event_id):
            raise CompletionFeedbackError("completion event_id has an unsafe shape")
        if not COMPLETION_IDENTIFIER_RE.fullmatch(self.project):
            raise CompletionFeedbackError("completion project has an unsafe shape")
        if self.profile is not None and not COMPLETION_IDENTIFIER_RE.fullmatch(self.profile):
            raise CompletionFeedbackError("completion profile has an unsafe shape")
        if self.operation not in _SOURCE_OPERATIONS[self.source]:
            raise CompletionFeedbackError("completion source and operation do not match")
        if self.operation == CompletionOperation.RUN_TESTS:
            if self.profile is None:
                raise CompletionFeedbackError("run_tests completion requires profile")
        elif self.profile is not None:
            raise CompletionFeedbackError("only run_tests completion may include profile")

    @property
    def requires_attention(self) -> bool:
        return self.state != CompletionState.SUCCEEDED

    def public_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_version": 1,
            "event_id": self.event_id,
            "source": self.source.value,
            "operation": self.operation.value,
            "project": self.project,
            "state": self.state.value,
            "requires_attention": self.requires_attention,
        }
        if self.profile is not None:
            payload["profile"] = self.profile
        return payload


def completion_event_id(
    *,
    source: CompletionSource,
    source_id: str,
) -> str:
    if not COMPLETION_IDENTIFIER_RE.fullmatch(source_id):
        raise CompletionFeedbackError("completion source_id has an unsafe shape")
    canonical = f"runner-mcp-completion:v1:{source.value}:{source_id}".encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def make_completion_event(
    *,
    source: CompletionSource,
    source_id: str,
    operation: CompletionOperation,
    project: str,
    state: CompletionState,
    profile: str | None = None,
) -> CompletionEvent:
    return CompletionEvent(
        event_id=completion_event_id(source=source, source_id=source_id),
        source=source,
        operation=operation,
        project=project,
        state=state,
        profile=profile,
    )


def serialize_completion_event(event: CompletionEvent) -> str:
    encoded = json.dumps(
        event.public_payload(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > MAX_COMPLETION_EVENT_BYTES:
        raise CompletionFeedbackError("completion event exceeds size limit")
    return encoded.decode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CompletionFeedbackError("completion event contains duplicate JSON keys")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise CompletionFeedbackError(
        f"completion event contains non-standard JSON constant: {value}"
    )


def parse_completion_event(payload: str | bytes) -> CompletionEvent:
    if isinstance(payload, bytes):
        if len(payload) > MAX_COMPLETION_EVENT_BYTES:
            raise CompletionFeedbackError("completion event exceeds size limit")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CompletionFeedbackError("completion event must be UTF-8") from exc
    else:
        text = payload
        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CompletionFeedbackError("completion event must be UTF-8") from exc
        if len(encoded) > MAX_COMPLETION_EVENT_BYTES:
            raise CompletionFeedbackError("completion event exceeds size limit")

    try:
        raw = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except CompletionFeedbackError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise CompletionFeedbackError("completion event is not valid JSON") from exc

    if not isinstance(raw, dict):
        raise CompletionFeedbackError("completion event must be a JSON object")

    allowed = {
        "event_version",
        "event_id",
        "source",
        "operation",
        "project",
        "state",
        "profile",
        "requires_attention",
    }
    unknown = set(raw) - allowed
    if unknown:
        raise CompletionFeedbackError("completion event contains unknown fields")

    if raw.get("event_version") != 1:
        raise CompletionFeedbackError("unsupported completion event version")

    try:
        event = CompletionEvent(
            event_id=raw["event_id"],
            source=CompletionSource(raw["source"]),
            operation=CompletionOperation(raw["operation"]),
            project=raw["project"],
            state=CompletionState(raw["state"]),
            profile=raw.get("profile"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, CompletionFeedbackError):
            raise
        raise CompletionFeedbackError("completion event failed strict validation") from exc

    if raw.get("requires_attention") is not event.requires_attention:
        raise CompletionFeedbackError("completion requires_attention does not match state")

    return event


def completion_notification_marker(event: CompletionEvent) -> str:
    return f"<!-- runner-mcp-completion:v1:{event.event_id} -->"


def safe_completion_label(event: CompletionEvent) -> str:
    target = event.project
    if event.profile is not None:
        target = f"{target} / {event.profile}"
    return f"{target}: {event.state.value}"
