from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_ALIAS_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_RUNNER_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_MAX_RUNNERS = 16
_MAX_LABELS = 16
_IMPLICIT_RUNNER_LABELS = frozenset(
    {"self-hosted", "linux", "windows", "macos", "x64", "arm", "arm64"}
)


class CIRunnerLifecycleError(ValueError):
    """Bounded configuration/status error without private path disclosure."""


@dataclass(frozen=True, slots=True)
class CIRunnerSpec:
    alias: str
    repository: str
    runner_name: str
    runner_root: Path
    work_root: Path
    labels: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _ALIAS_RE.fullmatch(self.alias):
            raise CIRunnerLifecycleError("CI runner alias is invalid")
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise CIRunnerLifecycleError("CI runner repository is invalid")
        if not _RUNNER_NAME_RE.fullmatch(self.runner_name):
            raise CIRunnerLifecycleError("CI runner name is invalid")
        if not self.runner_root.is_absolute() or not self.work_root.is_absolute():
            raise CIRunnerLifecycleError("CI runner paths must be absolute")
        # Lexical containment is not physical containment when ".." survives
        # in an absolute configured path.
        if ".." in self.runner_root.parts or ".." in self.work_root.parts:
            raise CIRunnerLifecycleError("CI runner paths must not traverse parents")
        if self.runner_root == self.work_root:
            raise CIRunnerLifecycleError("CI runner work root must be separate")
        try:
            self.work_root.relative_to(self.runner_root)
        except ValueError as exc:
            raise CIRunnerLifecycleError(
                "CI runner work root must be inside runner root"
            ) from exc
        if not 1 <= len(self.labels) <= _MAX_LABELS:
            raise CIRunnerLifecycleError("CI runner labels are outside supported bounds")
        if len(set(self.labels)) != len(self.labels):
            raise CIRunnerLifecycleError("CI runner labels must be unique")
        for label in self.labels:
            if not _LABEL_RE.fullmatch(label):
                raise CIRunnerLifecycleError("CI runner label is invalid")
        if any(label.lower() in _IMPLICIT_RUNNER_LABELS for label in self.labels):
            raise CIRunnerLifecycleError(
                "CI runner labels must contain custom admission labels only"
            )


@dataclass(frozen=True, slots=True)
class CIRunnerStatus:
    alias: str
    configured: bool
    registered: bool
    runner_root_ready: bool
    work_root_ready: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "configured": self.configured,
            "registered": self.registered,
            "runner_root_ready": self.runner_root_ready,
            "work_root_ready": self.work_root_ready,
        }


@dataclass(frozen=True, slots=True)
class CIRunnerLifecyclePlan:
    alias: str
    repository: str
    runner_name: str
    labels: tuple[str, ...]
    enrollment_required: bool
    activation_supported: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "repository": self.repository,
            "runner_name": self.runner_name,
            "labels": list(self.labels),
            "enrollment_required": self.enrollment_required,
            "activation_supported": self.activation_supported,
        }


def parse_ci_runner_specs(raw: str | None) -> dict[str, CIRunnerSpec]:
    if raw is None or not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CIRunnerLifecycleError("CI runner configuration is invalid JSON") from exc
    if not isinstance(value, list) or len(value) > _MAX_RUNNERS:
        raise CIRunnerLifecycleError("CI runner configuration is outside supported bounds")

    result: dict[str, CIRunnerSpec] = {}
    for item in value:
        if not isinstance(item, dict):
            raise CIRunnerLifecycleError("CI runner entry is invalid")
        expected = {
            "alias",
            "repository",
            "runner_name",
            "runner_root",
            "work_root",
            "labels",
        }
        if set(item) != expected:
            raise CIRunnerLifecycleError("CI runner entry fields are invalid")
        labels = item["labels"]
        if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
            raise CIRunnerLifecycleError("CI runner labels are invalid")
        try:
            spec = CIRunnerSpec(
                alias=item["alias"],
                repository=item["repository"],
                runner_name=item["runner_name"],
                runner_root=Path(item["runner_root"]),
                work_root=Path(item["work_root"]),
                labels=tuple(labels),
            )
        except (TypeError, ValueError) as exc:
            if isinstance(exc, CIRunnerLifecycleError):
                raise
            raise CIRunnerLifecycleError("CI runner entry is invalid") from exc
        if spec.alias in result:
            raise CIRunnerLifecycleError("CI runner alias must be unique")
        if any(existing.runner_name == spec.runner_name for existing in result.values()):
            raise CIRunnerLifecycleError("CI runner name must be unique")
        result[spec.alias] = spec
    return result


def inspect_ci_runner(spec: CIRunnerSpec) -> CIRunnerStatus:
    if not isinstance(spec, CIRunnerSpec):
        raise TypeError("spec must be CIRunnerSpec")

    runner_ready = _safe_directory(spec.runner_root)
    work_ready = runner_ready and _safe_directory(spec.work_root)
    if work_ready:
        try:
            spec.work_root.resolve(strict=True).relative_to(
                spec.runner_root.resolve(strict=True)
            )
        except (OSError, ValueError):
            work_ready = False
    marker = spec.runner_root / ".runner"
    registered = runner_ready and marker.is_file() and not marker.is_symlink()

    return CIRunnerStatus(
        alias=spec.alias,
        configured=True,
        registered=registered,
        runner_root_ready=runner_ready,
        work_root_ready=work_ready,
    )


def plan_ci_runner(spec: CIRunnerSpec) -> CIRunnerLifecyclePlan:
    status = inspect_ci_runner(spec)
    return CIRunnerLifecyclePlan(
        alias=spec.alias,
        repository=spec.repository,
        runner_name=spec.runner_name,
        labels=spec.labels,
        enrollment_required=not status.registered,
        activation_supported=False,
    )


def _safe_directory(path: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return False
    return resolved.is_dir()
