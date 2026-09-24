import os
from pathlib import Path

from .base import (
    AdapterInfo,
    AdapterPresetError,
    MigrationPresetRecipe,
    TestPresetRecipe,
)


def _safe_file(path: Path) -> bool:
    return path.exists() and path.is_file() and not path.is_symlink()


def _safe_executable(path: Path) -> bool:
    return _safe_file(path) and os.access(path, os.X_OK)


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

    def _find_venv_executable(
        self,
        root: Path,
        names: tuple[str, ...],
    ) -> Path | None:
        if not _safe_directory(root):
            return None
        for directory in self._venv_bins(root):
            virtualenv = directory.parent
            if not _safe_directory(virtualenv) or not _safe_directory(directory):
                continue
            for name in names:
                candidate = directory / name
                if not _safe_executable(candidate):
                    continue
                try:
                    resolved = candidate.resolve(strict=True)
                    resolved.relative_to(root.resolve(strict=True))
                except (OSError, ValueError):
                    continue
                return resolved
        return None

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

    def materialize_test_preset(
        self,
        root: Path,
        preset: str,
        arguments: tuple[str, ...],
    ) -> TestPresetRecipe:
        if preset == "pytest":
            executable = self._find_venv_executable(root, ("python", "python3"))
            if executable is None:
                raise AdapterPresetError(
                    "Could not find a project Python executable in .venv/bin or venv/bin"
                )
            return TestPresetRecipe(
                argv=(str(executable), "-m", "pytest", "-q", *arguments),
            )
        if preset == "ruff":
            executable = self._find_venv_executable(root, ("ruff",))
            if executable is None:
                raise AdapterPresetError(
                    "Could not find a project Ruff executable in .venv/bin or venv/bin"
                )
            return TestPresetRecipe(
                argv=(str(executable), "check", ".", *arguments),
            )
        raise AdapterPresetError("Unknown Python test preset")

    def materialize_migration_preset(
        self,
        root: Path,
        preset: str,
    ) -> MigrationPresetRecipe:
        if preset != "alembic":
            raise AdapterPresetError("Unknown Python migration preset")
        executable = self._find_venv_executable(root, ("alembic",))
        if executable is None:
            raise AdapterPresetError("Could not find Alembic in .venv/bin or venv/bin")
        return MigrationPresetRecipe(
            status_argv=(str(executable), "current"),
            apply_argv=(str(executable), "upgrade", "head"),
        )
