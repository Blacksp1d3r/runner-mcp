from pathlib import Path

import pytest

from runner_mcp.adapters import AdapterError, get_adapter, inspect_project, list_adapters
from runner_mcp.adapters.generic import GenericAdapter
from runner_mcp.adapters.python import PythonAdapter
from runner_mcp.adapters.registry import adapter_ids


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


def test_inspect_project_unknown_adapter_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(AdapterError, match="Unknown or disabled"):
        inspect_project("module.from.config", tmp_path)


def test_adapter_ids_enumerates_sorted_built_ins() -> None:
    assert adapter_ids() == ("generic", "python")


def test_list_adapters_exposes_full_capability_metadata() -> None:
    by_id = {entry["id"]: entry for entry in list_adapters()}

    assert by_id["generic"] == {
        "id": "generic",
        "name": "Generic project",
        "test_presets": ["custom"],
        "migration_presets": ["custom"],
        "supports_services": True,
        "supports_deployment": True,
    }
    assert by_id["python"] == {
        "id": "python",
        "name": "Python project",
        "test_presets": ["pytest", "ruff", "custom"],
        "migration_presets": ["alembic", "custom"],
        "supports_services": True,
        "supports_deployment": True,
    }


def test_generic_adapter_default_presets_are_always_none(tmp_path: Path) -> None:
    adapter = GenericAdapter()
    missing_root = tmp_path / "does-not-exist"

    assert adapter.default_test_preset(tmp_path) is None
    assert adapter.default_migration_preset(tmp_path) is None
    assert adapter.default_test_preset(missing_root) is None
    assert adapter.default_migration_preset(missing_root) is None


def test_python_adapter_default_presets_resolve_only_when_detected(
    tmp_path: Path,
) -> None:
    adapter = PythonAdapter()

    bare_root = tmp_path / "bare"
    bare_root.mkdir()
    assert adapter.default_test_preset(bare_root) is None
    assert adapter.default_migration_preset(bare_root) is None

    tooled_root = tmp_path / "tooled"
    tooled_root.mkdir()
    executable(tooled_root / ".venv" / "bin" / "pytest")
    executable(tooled_root / ".venv" / "bin" / "alembic")
    assert adapter.default_test_preset(tooled_root) == "pytest"
    assert adapter.default_migration_preset(tooled_root) == "alembic"


def test_python_adapter_missing_root_fails_closed(tmp_path: Path) -> None:
    result = inspect_project("python", tmp_path / "does-not-exist")

    assert result["project_root_available"] is False
    assert result["pyproject_present"] is False
    assert result["virtualenv_present"] is False
    assert result["pytest_available"] is False
    assert result["ruff_available"] is False
    assert result["alembic_available"] is False
    assert result["django_manage_present"] is False
    assert result["automatic_test_preset"] is None
    assert result["automatic_migration_preset"] is None


def test_python_adapter_ignores_symlinked_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-project"
    real_root.mkdir()
    executable(real_root / ".venv" / "bin" / "pytest")
    linked_root = tmp_path / "linked-project"
    linked_root.symlink_to(real_root)

    result = inspect_project("python", linked_root)

    assert result["project_root_available"] is False
    assert result["pytest_available"] is False
    assert result["automatic_test_preset"] is None


def test_python_adapter_ignores_symlinked_executable(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    real_executable = tmp_path / "real-pytest"
    executable(real_executable)
    linked_executable = root / ".venv" / "bin" / "pytest"
    linked_executable.parent.mkdir(parents=True)
    linked_executable.symlink_to(real_executable)

    result = inspect_project("python", root)

    assert result["pytest_available"] is False
    assert result["automatic_test_preset"] is None


def test_python_adapter_ignores_non_executable_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    candidate = root / ".venv" / "bin" / "pytest"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    candidate.chmod(0o644)

    result = inspect_project("python", root)

    assert result["pytest_available"] is False
    assert result["automatic_test_preset"] is None


def test_python_adapter_reports_virtualenv_and_django_flags(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    without_extras = inspect_project("python", root)
    assert without_extras["virtualenv_present"] is False
    assert without_extras["django_manage_present"] is False

    (root / ".venv" / "bin").mkdir(parents=True)
    (root / "manage.py").write_text("", encoding="utf-8")

    with_extras = inspect_project("python", root)
    assert with_extras["virtualenv_present"] is True
    assert with_extras["django_manage_present"] is True
