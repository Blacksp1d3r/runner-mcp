from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

PROJECT_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+$")
SERVICE_RE = re.compile(r"^[A-Za-z0-9_.@-]+$")
ALIAS_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
BLOCKED_TEST_ENV_NAMES = {
    "BASH_ENV",
    "ENV",
    "GIT_CONFIG",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
    "HOME",
    "IFS",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "PATH",
    "PYTHONHOME",
    "PYTHONPATH",
    "SHELLOPTS",
    "TMPDIR",
}


class TestProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    argv: list[str] = Field(min_length=1, max_length=64)
    cwd: str = "."
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    max_log_bytes: int = Field(default=2_000_000, ge=4096, le=20_000_000)
    env_passthrough: list[str] = Field(default_factory=list, max_length=64)

    @field_validator("argv")
    @classmethod
    def validate_argv(cls, values: list[str]) -> list[str]:
        if not values or not Path(values[0]).is_absolute():
            raise ValueError("test executable must be an absolute path")
        if any(not value or len(value) > 2048 or "\x00" in value or "\n" in value for value in values):
            raise ValueError("test argv contains an invalid argument")
        return values

    @field_validator("cwd")
    @classmethod
    def validate_cwd(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or "\\" in value:
            raise ValueError("test cwd must be a project-relative path")
        return value

    @field_validator("env_passthrough")
    @classmethod
    def validate_env_names(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("env_passthrough contains duplicates")
        if any(not ENV_NAME_RE.fullmatch(value) for value in values):
            raise ValueError("env_passthrough contains an invalid environment variable name")
        blocked = sorted(set(values) & BLOCKED_TEST_ENV_NAMES)
        if blocked:
            raise ValueError(
                "env_passthrough contains blocked process-control variables: "
                + ", ".join(blocked)
            )
        return values


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)
    repository: str = Field(min_length=3, max_length=200)
    environment: str = Field(default="staging", min_length=1, max_length=40)
    root: Path
    health_url: AnyHttpUrl | None = None
    allowed_services: list[str] = Field(default_factory=list)
    database_alias: str | None = None
    test_profiles: dict[str, TestProfile] = Field(default_factory=dict)

    @field_validator("test_profiles")
    @classmethod
    def validate_test_profile_names(
        cls,
        values: dict[str, TestProfile],
    ) -> dict[str, TestProfile]:
        if any(not PROJECT_CODE_RE.fullmatch(name) for name in values):
            raise ValueError("test profile name contains unsupported characters")
        return values

    @field_validator("repository")
    @classmethod
    def validate_repository(cls, value: str) -> str:
        if not REPOSITORY_RE.fullmatch(value):
            raise ValueError("repository must use the form owner/name")
        return value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        if not PROJECT_CODE_RE.fullmatch(value):
            raise ValueError("environment contains unsupported characters")
        return value

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("project root must be absolute")
        return value

    @field_validator("allowed_services")
    @classmethod
    def validate_services(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("allowed_services contains duplicates")
        if any(not SERVICE_RE.fullmatch(value) for value in values):
            raise ValueError("allowed_services contains an invalid service name")
        return values

    @field_validator("database_alias")
    @classmethod
    def validate_database_alias(cls, value: str | None) -> str | None:
        if value is not None and not ALIAS_RE.fullmatch(value):
            raise ValueError("database_alias contains unsupported characters")
        return value

    def public_summary(self, code: str) -> dict[str, str]:
        return {
            "code": code,
            "name": self.display_name,
            "repository": self.repository,
            "environment": self.environment,
        }


class ProjectRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projects: dict[str, ProjectConfig]

    def validate_codes(self) -> None:
        invalid = [code for code in self.projects if not PROJECT_CODE_RE.fullmatch(code)]
        if invalid:
            raise ValueError(f"Invalid project code(s): {', '.join(sorted(invalid))}")


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand(item) for key, item in value.items()}
    return value


def _contains_unresolved(value: Any) -> bool:
    if isinstance(value, str):
        return "${" in value
    if isinstance(value, list):
        return any(_contains_unresolved(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_unresolved(item) for item in value.values())
    return False


def load_project_registry(path: Path) -> ProjectRegistry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    expanded = _expand(raw)
    if _contains_unresolved(expanded):
        raise ValueError("Project configuration contains unresolved environment placeholders")

    registry = ProjectRegistry.model_validate(expanded)
    registry.validate_codes()
    if not registry.projects:
        raise ValueError("At least one project must be configured")
    return registry
