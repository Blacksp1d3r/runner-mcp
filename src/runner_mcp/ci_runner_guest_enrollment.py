from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .ci_runner_github import CIRunnerGitHubController, CIRunnerGitHubError

_ALIAS_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_RUNNER_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_BINDING_RE = re.compile(r"^[a-z][a-z0-9._-]{0,95}$")
_FORBIDDEN_LABELS = frozenset({"aifordable-staging"})
_VERIFY_ATTEMPTS = 5


class CIRunnerGuestEnrollmentError(RuntimeError):
    """Bounded guest enrollment failure without secret or host-detail leakage."""


@dataclass(frozen=True, slots=True)
class CIRunnerGuestSpec:
    alias: str
    repository: str
    runner_name: str
    labels: tuple[str, ...]
    transport_binding_key: str

    def __post_init__(self) -> None:
        if _ALIAS_RE.fullmatch(self.alias) is None:
            raise CIRunnerGuestEnrollmentError("guest CI runner alias is invalid")
        if _REPOSITORY_RE.fullmatch(self.repository) is None:
            raise CIRunnerGuestEnrollmentError("guest CI runner repository is invalid")
        if _RUNNER_NAME_RE.fullmatch(self.runner_name) is None:
            raise CIRunnerGuestEnrollmentError("guest CI runner name is invalid")
        if not self.labels or len(set(self.labels)) != len(self.labels):
            raise CIRunnerGuestEnrollmentError("guest CI runner labels are invalid")
        if any(_LABEL_RE.fullmatch(label) is None for label in self.labels):
            raise CIRunnerGuestEnrollmentError("guest CI runner labels are invalid")
        if any(label.casefold() in _FORBIDDEN_LABELS for label in self.labels):
            raise CIRunnerGuestEnrollmentError("guest CI runner label is forbidden")
        if _BINDING_RE.fullmatch(self.transport_binding_key) is None:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner transport binding is invalid"
            )


@dataclass(frozen=True, slots=True, repr=False)
class CIRunnerRegistrationSecret:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or len(self.value) < 16:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner registration secret is invalid"
            )

    def __repr__(self) -> str:
        return "<CIRunnerRegistrationSecret redacted>"


@dataclass(frozen=True, slots=True)
class CIRunnerGuestTransportResult:
    state: str
    registered: bool

    def __post_init__(self) -> None:
        if self.state not in {"registered", "already-registered"}:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner transport result is invalid"
            )
        if not isinstance(self.registered, bool):
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner transport result is invalid"
            )


class CIRunnerGuestEnrollmentTransport(Protocol):
    def enroll(
        self,
        spec: CIRunnerGuestSpec,
        secret: CIRunnerRegistrationSecret,
    ) -> CIRunnerGuestTransportResult: ...


@dataclass(frozen=True, slots=True)
class CIRunnerGuestEnrollmentResult:
    state: str
    alias: str
    runner_name: str
    registered: bool
    online: bool
    busy: bool
    custom_labels: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "state": self.state,
            "alias": self.alias,
            "runner_name": self.runner_name,
            "registered": self.registered,
            "online": self.online,
            "busy": self.busy,
            "custom_labels": list(self.custom_labels),
        }


Sleep = Callable[[float], None]


class CIRunnerGuestEnrollmentManager:
    """Keep GitHub authority local while delegating fixed guest execution."""

    def __init__(
        self,
        *,
        github: CIRunnerGitHubController,
        transport: CIRunnerGuestEnrollmentTransport,
        sleeper: Sleep = time.sleep,
    ) -> None:
        if not isinstance(github, CIRunnerGitHubController):
            raise TypeError("github must be CIRunnerGitHubController")
        if not callable(sleeper):
            raise TypeError("sleeper must be callable")
        self._github = github
        self._transport = transport
        self._sleeper = sleeper

    def enroll(self, spec: CIRunnerGuestSpec) -> CIRunnerGuestEnrollmentResult:
        if not isinstance(spec, CIRunnerGuestSpec):
            raise TypeError("spec must be CIRunnerGuestSpec")

        remote = self._safe_remote_status(spec)
        if remote is not None:
            return self._result("already-registered", spec, remote)

        secret = CIRunnerRegistrationSecret(
            self._registration_token(spec)
        )
        transport_result = self._transport.enroll(spec, secret)
        if not transport_result.registered:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner enrollment did not register"
            )

        verified = self._wait_for_remote_registration(spec)
        if set(verified.custom_labels) != set(spec.labels):
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner labels did not converge"
            )
        return self._result("registered", spec, verified)

    def _registration_token(self, spec: CIRunnerGuestSpec) -> str:
        try:
            token = self._github.create_registration_token(spec)
        except CIRunnerGitHubError as exc:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner registration token is unavailable"
            ) from exc
        return token.value

    def _safe_remote_status(self, spec: CIRunnerGuestSpec):
        try:
            return self._github.status(spec)
        except CIRunnerGitHubError as exc:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner GitHub status is unavailable"
            ) from exc

    def _wait_for_remote_registration(self, spec: CIRunnerGuestSpec):
        for attempt in range(_VERIFY_ATTEMPTS):
            state = self._safe_remote_status(spec)
            if state is not None:
                return state
            if attempt + 1 < _VERIFY_ATTEMPTS:
                self._sleeper(1.0)
        raise CIRunnerGuestEnrollmentError(
            "guest CI runner registration did not become visible on GitHub"
        )

    @staticmethod
    def _result(state: str, spec: CIRunnerGuestSpec, remote):
        return CIRunnerGuestEnrollmentResult(
            state=state,
            alias=spec.alias,
            runner_name=spec.runner_name,
            registered=True,
            online=remote.online,
            busy=remote.busy,
            custom_labels=remote.custom_labels,
        )
