from pathlib import Path

import pytest

from runner_mcp.config import load_project_registry


def test_load_registry_expands_runtime_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    monkeypatch.setenv("TEST_ROOT", str(project_root))
    config = tmp_path / "projects.yml"
    config.write_text(
        """
projects:
  demo:
    display_name: Demo
    repository: example/demo
    environment: staging
    root: "${TEST_ROOT}"
""".strip(),
        encoding="utf-8",
    )

    registry = load_project_registry(config)
    assert registry.projects["demo"].root == project_root
    assert registry.projects["demo"].public_summary("demo")["code"] == "demo"


def test_unresolved_placeholder_fails_closed(tmp_path: Path) -> None:
    config = tmp_path / "projects.yml"
    config.write_text(
        """
projects:
  demo:
    display_name: Demo
    repository: example/demo
    root: "${MISSING_PRIVATE_VALUE}"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unresolved"):
        load_project_registry(config)


def test_relative_project_root_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "projects.yml"
    config.write_text(
        """
projects:
  demo:
    display_name: Demo
    repository: example/demo
    root: relative-root
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absolute"):
        load_project_registry(config)


def test_invalid_repository_shape_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "projects.yml"
    config.write_text(
        f"""
projects:
  demo:
    display_name: Demo
    repository: invalid repository
    root: "{tmp_path / 'project'}"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="owner/name"):
        load_project_registry(config)


def test_unsafe_service_name_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "projects.yml"
    config.write_text(
        f"""
projects:
  demo:
    display_name: Demo
    repository: example/demo
    root: "{tmp_path / 'project'}"
    allowed_services:
      - "demo.service;unexpected"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="service name"):
        load_project_registry(config)
