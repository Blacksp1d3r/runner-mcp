from pathlib import Path

import pytest

from runner_mcp.config import load_project_registry


def test_load_registry_expands_runtime_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_ROOT", "runtime-root")
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
    assert registry.projects["demo"].root == "runtime-root"
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
