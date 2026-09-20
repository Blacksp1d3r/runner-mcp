from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .config import PROJECT_CODE_RE

MAX_BRIDGE_REQUEST_BYTES = 8_192
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class BridgeProtocolError(ValueError):
    """Raised when a mailbox request fails strict protocol validation."""


class BridgeAction(StrEnum):
    LIST_PROJECTS = "list_projects"
    SAFETY_STATUS = "safety_status"
    PROJECT_STATUS = "project_status"
    PROJECT_CAPABILITIES = "project_capabilities"
    LIST_TEST_PROFILES = "list_test_profiles"
    RUN_TESTS = "run_tests"


class BridgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=64)
    action: BridgeAction
    project: str | None = Field(default=None, min_length=1, max_length=80)
    profile: str | None = Field(default=None, min_length=1, max_length=80)

    @model_validator(mode="after")
    def validate_action_arguments(self) -> BridgeRequest:
        if not REQUEST_ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id contains unsupported characters")

        if self.project is not None and not PROJECT_CODE_RE.fullmatch(self.project):
            raise ValueError("project contains unsupported characters")

        if self.profile is not None and not PROJECT_CODE_RE.fullmatch(self.profile):
            raise ValueError("profile contains unsupported characters")

        if self.action in {BridgeAction.LIST_PROJECTS, BridgeAction.SAFETY_STATUS}:
            if self.project is not None or self.profile is not None:
                raise ValueError(f"{self.action.value} does not accept project or profile")
            return self

        if self.action in {
            BridgeAction.PROJECT_STATUS,
            BridgeAction.PROJECT_CAPABILITIES,
            BridgeAction.LIST_TEST_PROFILES,
        }:
            if self.project is None:
                raise ValueError(f"{self.action.value} requires project")
            if self.profile is not None:
                raise ValueError(f"{self.action.value} does not accept profile")
            return self

        if self.action == BridgeAction.RUN_TESTS:
            if self.project is None or self.profile is None:
                raise ValueError("run_tests requires project and profile")
            return self

        raise ValueError("unsupported bridge action")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BridgeProtocolError("bridge request contains duplicate JSON keys")
        result[key] = value
    return result


def parse_bridge_request(payload: str | bytes) -> BridgeRequest:
    if isinstance(payload, bytes):
        if len(payload) > MAX_BRIDGE_REQUEST_BYTES:
            raise BridgeProtocolError("bridge request exceeds size limit")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BridgeProtocolError("bridge request must be UTF-8") from exc
    else:
        text = payload
        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise BridgeProtocolError("bridge request must be UTF-8") from exc
        if len(encoded) > MAX_BRIDGE_REQUEST_BYTES:
            raise BridgeProtocolError("bridge request exceeds size limit")

    try:
        raw = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except BridgeProtocolError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise BridgeProtocolError("bridge request is not valid JSON") from exc

    if not isinstance(raw, dict):
        raise BridgeProtocolError("bridge request must be a JSON object")

    try:
        return BridgeRequest.model_validate(raw)
    except ValidationError as exc:
        raise BridgeProtocolError("bridge request failed strict validation") from exc


def bridge_tool_call(request: BridgeRequest) -> tuple[str, dict[str, str]]:
    if request.action in {BridgeAction.LIST_PROJECTS, BridgeAction.SAFETY_STATUS}:
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
            "profile": request.profile,
        }

    raise BridgeProtocolError("unsupported bridge action")
