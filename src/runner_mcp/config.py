from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

PROJECT_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)
    repository: str = Field(min_length=3, max_length=200)
    environment: str = Field(default="staging", min_length=1, max_length=40)
    root: str = Field(min_length=1)
    health_url: str | None = None
    allowed_services: list[str] = Field(default_factory=list)
    database_alias: str | None = None

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
