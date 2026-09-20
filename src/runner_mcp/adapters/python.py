from pathlib import Path

from .base import AdapterInfo


def _safe_file(path: Path) -> bool:
    return path.exists() and path.is_file() and not path.is_symlink()


def _safe_executable(path: Path) -> bool:
    return _safe_file(path) and bool(path.stat().st_mode & 0o111)


def _safe_directory(path: Path) -> bool:
    return path.exists() and path.is_dir() and not path.is_symlink()


class PythonAdapter:
    info = AdapterInfo(
        adapter_id="python",
        display_name="Python project",
        test_presets=("pytest", "ruff", "custom"),
        migration_presets=("alembic", "custom"),
    )

    @staticmethod
    def _venv_bins(root: Path) -> tuple[Path, ...]:
        return (
            root / ".venv" / "bin",
            root / "venv" / "bin",
        )

    def inspect(self, root: Path) -> dict[str, object]:
        root_ok = _safe_directory(root)
        bins = self._venv_bins(root) if root_ok else ()
        pytest_available = any(_safe_executable(path / "pytest") for path in bins)
        ruff_available = any(_safe_executable(path / "ruff") for path in bins)
        alembic_available = any(_safe_executable(path / "alembic") for path in bins)
        return {
            "adapter": self.info.adapter_id,
            "project_root_available": root_ok,
            "pyproject_present": root_ok and _safe_file(root / "pyproject.toml"),
            "virtualenv_present": root_ok and any(_safe_directory(path.parent) for path in bins),
            "pytest_available": pytest_available,
            "ruff_available": ruff_available,
            "alembic_available": alembic_available,
            "django_manage_present": root_ok and _safe_file(root / "manage.py"),
            "automatic_test_preset": "pytest" if pytest_available else None,
            "automatic_migration_preset": "alembic" if alembic_available else None,
        }

    def default_test_preset(self, root: Path) -> str | None:
        return "pytest" if self.inspect(root)["pytest_available"] else None

    def default_migration_preset(self, root: Path) -> str | None:
        return "alembic" if self.inspect(root)["alembic_available"] else None
