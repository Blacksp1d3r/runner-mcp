from pathlib import Path

import pytest

from runner_mcp.adapters import AdapterError, get_adapter, inspect_project, list_adapters


def executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def test_registry_contains_only_built_in_adapters() -> None:
    assert [item["id"] for item in list_adapters()] == ["generic", "python"]


def test_unknown_adapter_fails_closed() -> None:
    with pytest.raises(AdapterError, match="Unknown or disabled"):
        get_adapter("module.from.config")


def test_generic_adapter_never_guesses_presets(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    result = inspect_project("generic", root)
    assert result["automatic_test_preset"] is None
    assert result["automatic_migration_preset"] is None
    assert str(root) not in repr(result)


def test_python_adapter_detects_safe_tooling_without_paths(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    executable(root / ".venv" / "bin" / "pytest")
    executable(root / ".venv" / "bin" / "ruff")
    executable(root / ".venv" / "bin" / "alembic")

    result = inspect_project("python", root)

    assert result["pyproject_present"] is True
    assert result["pytest_available"] is True
    assert result["ruff_available"] is True
    assert result["alembic_available"] is True
    assert result["automatic_test_preset"] == "pytest"
    assert result["automatic_migration_preset"] == "alembic"
    assert str(root) not in repr(result)


def test_python_adapter_ignores_symlinked_marker(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("[project]\nname='outside'\n", encoding="utf-8")
    (root / "pyproject.toml").symlink_to(outside)

    assert inspect_project("python", root)["pyproject_present"] is False
