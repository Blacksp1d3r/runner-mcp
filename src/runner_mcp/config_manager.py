from __future__ import annotations

import fcntl
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig, ProjectRegistry, ServiceConfig, TestProfile
from .onboarding import OnboardingError, PrivatePaths, read_private_runtime


class ConfigManagerError(RuntimeError):
    pass


def _absolute_without_symlinks(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    absolute = expanded if expanded.is_absolute() else Path.cwd() / expanded

    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ConfigManagerError(f"{label} must not contain symlinks")

    try:
        return absolute.resolve(strict=True)
    except OSError as exc:
        raise ConfigManagerError(f"{label} is unavailable") from exc


@contextmanager
def _configuration_lock(paths: PrivatePaths) -> Iterator[None]:
    lock_path = paths.config_dir / ".projects.lock"
    if lock_path.exists() and lock_path.is_symlink():
        raise ConfigManagerError("Project configuration lock must not be a symlink")

    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise ConfigManagerError("Could not acquire the private configuration lock") from exc

    try:
        os.chmod(lock_path, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _serialize_registry(registry: ProjectRegistry) -> str:
    payload = registry.model_dump(mode="json", exclude_none=True)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _atomic_write_private(path: Path, content: str) -> None:
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise ConfigManagerError("Project configuration directory is unavailable")
    if path.exists() and path.is_symlink():
        raise ConfigManagerError("Project configuration must not be a symlink")

    fd, temp_name = tempfile.mkstemp(
        prefix=".projects-",
        suffix=".tmp",
        dir=parent,
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        if fd >= 0:
            os.close(fd)


def _load_for_edit(config_dir: Path) -> tuple[PrivatePaths, Path, ProjectRegistry]:
    try:
        paths, settings, registry = read_private_runtime(config_dir)
    except OnboardingError as exc:
        raise ConfigManagerError(str(exc)) from exc
    project_file = settings.projects_config.expanduser().resolve()
    return paths, project_file, registry


def _save_registry(
    *,
    paths: PrivatePaths,
    project_file: Path,
    registry: ProjectRegistry,
) -> None:
    registry.validate_codes()
    if not registry.projects:
        raise ConfigManagerError("At least one project must remain configured")

    content = _serialize_registry(registry)
    validated = ProjectRegistry.model_validate(yaml.safe_load(content) or {})
    validated.validate_codes()

    with _configuration_lock(paths):
        _atomic_write_private(project_file, content)


def list_projects(config_dir: Path) -> list[dict[str, str]]:
    _, _, registry = _load_for_edit(config_dir)
    return [
        project.public_summary(code)
        for code, project in sorted(registry.projects.items())
    ]


def add_project(
    config_dir: Path,
    *,
    code: str,
    display_name: str,
    repository: str,
    root: Path,
) -> dict[str, str]:
    paths, project_file, registry = _load_for_edit(config_dir)
    if code in registry.projects:
        raise ConfigManagerError("Project code is already configured")

    resolved_root = _absolute_without_symlinks(root, label="Project root")
    if not resolved_root.is_dir():
        raise ConfigManagerError("Project root must be an existing directory")

    try:
        project = ProjectConfig(
            display_name=display_name,
            repository=repository,
            environment="staging",
            root=resolved_root,
        )
        updated = ProjectRegistry(
            projects={
                **registry.projects,
                code: project,
            }
        )
        updated.validate_codes()
    except ValueError as exc:
        raise ConfigManagerError(str(exc)) from exc

    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )
    return project.public_summary(code)


def remove_project(
    config_dir: Path,
    *,
    code: str,
) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    if code not in registry.projects:
        raise ConfigManagerError("Unknown project")
    if len(registry.projects) == 1:
        raise ConfigManagerError("The last configured project cannot be removed")

    remaining = {
        key: value
        for key, value in registry.projects.items()
        if key != code
    }
    updated = ProjectRegistry(projects=remaining)
    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )


def list_test_profiles(
    config_dir: Path,
    *,
    project: str,
) -> list[dict[str, Any]]:
    _, _, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")

    return [
        {
            "name": name,
            "timeout_seconds": profile.timeout_seconds,
            "max_log_bytes": profile.max_log_bytes,
            "environment_passthrough_count": len(profile.env_passthrough),
        }
        for name, profile in sorted(cfg.test_profiles.items())
    ]


def _detect_project_executable(root: Path, names: tuple[str, ...]) -> Path | None:
    prefixes = (
        root / ".venv" / "bin",
        root / "venv" / "bin",
    )
    for prefix in prefixes:
        for name in names:
            candidate = prefix / name
            if (
                candidate.exists()
                and candidate.is_file()
                and not candidate.is_symlink()
                and os.access(candidate, os.X_OK)
            ):
                return candidate.resolve()
    return None


def build_test_profile(
    *,
    project_root: Path,
    preset: str,
    executable: Path | None = None,
    arguments: list[str] | None = None,
    cwd: str = ".",
    timeout_seconds: int = 300,
    max_log_bytes: int = 2_000_000,
    env_passthrough: list[str] | None = None,
) -> TestProfile:
    args = list(arguments or [])
    environment = list(env_passthrough or [])

    if preset == "pytest":
        detected = _detect_project_executable(project_root, ("python", "python3"))
        if detected is None:
            raise ConfigManagerError(
                "Could not find a project Python executable in .venv/bin or venv/bin"
            )
        argv = [str(detected), "-m", "pytest", "-q", *args]
    elif preset == "ruff":
        detected = _detect_project_executable(project_root, ("ruff",))
        if detected is None:
            raise ConfigManagerError(
                "Could not find a project Ruff executable in .venv/bin or venv/bin"
            )
        argv = [str(detected), "check", ".", *args]
    elif preset == "custom":
        if executable is None:
            raise ConfigManagerError("Custom profiles require an executable")
        resolved = _absolute_without_symlinks(
            executable,
            label="Custom executable",
        )
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise ConfigManagerError("Custom executable is unavailable or unsafe")
        argv = [str(resolved), *args]
    else:
        raise ConfigManagerError("Unknown test-profile preset")

    try:
        return TestProfile(
            argv=argv,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            max_log_bytes=max_log_bytes,
            env_passthrough=environment,
        )
    except ValueError as exc:
        raise ConfigManagerError(str(exc)) from exc


def add_test_profile(
    config_dir: Path,
    *,
    project: str,
    name: str,
    preset: str,
    executable: Path | None = None,
    arguments: list[str] | None = None,
    cwd: str = ".",
    timeout_seconds: int = 300,
    max_log_bytes: int = 2_000_000,
    env_passthrough: list[str] | None = None,
) -> dict[str, Any]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if name in cfg.test_profiles:
        raise ConfigManagerError("Test profile is already configured")

    profile = build_test_profile(
        project_root=cfg.root,
        preset=preset,
        executable=executable,
        arguments=arguments,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        max_log_bytes=max_log_bytes,
        env_passthrough=env_passthrough,
    )

    profiles = {
        **cfg.test_profiles,
        name: profile,
    }
    try:
        updated_project = cfg.model_copy(update={"test_profiles": profiles})
        updated_project = ProjectConfig.model_validate(updated_project.model_dump())
        updated = ProjectRegistry(
            projects={
                **registry.projects,
                project: updated_project,
            }
        )
        updated.validate_codes()
    except ValueError as exc:
        raise ConfigManagerError(str(exc)) from exc

    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )
    return {
        "name": name,
        "timeout_seconds": profile.timeout_seconds,
        "max_log_bytes": profile.max_log_bytes,
        "environment_passthrough_count": len(profile.env_passthrough),
    }


def remove_test_profile(
    config_dir: Path,
    *,
    project: str,
    name: str,
) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if name not in cfg.test_profiles:
        raise ConfigManagerError("Unknown test profile")

    profiles = {
        key: value
        for key, value in cfg.test_profiles.items()
        if key != name
    }
    updated_project = cfg.model_copy(update={"test_profiles": profiles})
    updated = ProjectRegistry(
        projects={
            **registry.projects,
            project: updated_project,
        }
    )
    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )


def list_service_configs(
    config_dir: Path,
    *,
    project: str,
) -> list[dict[str, Any]]:
    _, _, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")

    return [
        {
            "name": name,
            "can_start": service.allow_start,
            "can_stop": service.allow_stop,
            "can_restart": service.allow_restart,
            "health_check": service.health_url is not None,
        }
        for name, service in sorted(cfg.services.items())
    ]


def add_service_config(
    config_dir: Path,
    *,
    project: str,
    name: str,
    unit: str,
    health_url: str | None = None,
    allow_start: bool = False,
    allow_stop: bool = False,
    allow_restart: bool = False,
) -> dict[str, Any]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if name in cfg.services:
        raise ConfigManagerError("Service alias is already configured")

    try:
        service = ServiceConfig(
            unit=unit,
            health_url=health_url,
            allow_start=allow_start,
            allow_stop=allow_stop,
            allow_restart=allow_restart,
        )
        services = {
            **cfg.services,
            name: service,
        }
        updated_project = cfg.model_copy(update={"services": services})
        updated_project = ProjectConfig.model_validate(updated_project.model_dump())
        updated = ProjectRegistry(
            projects={
                **registry.projects,
                project: updated_project,
            }
        )
        updated.validate_codes()
    except ValueError as exc:
        raise ConfigManagerError(str(exc)) from exc

    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )
    return {
        "name": name,
        "can_start": service.allow_start,
        "can_stop": service.allow_stop,
        "can_restart": service.allow_restart,
        "health_check": service.health_url is not None,
    }


def remove_service_config(
    config_dir: Path,
    *,
    project: str,
    name: str,
) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if name not in cfg.services:
        raise ConfigManagerError("Unknown service alias")

    services = {
        key: value
        for key, value in cfg.services.items()
        if key != name
    }
    updated_project = cfg.model_copy(update={"services": services})
    updated = ProjectRegistry(
        projects={
            **registry.projects,
            project: updated_project,
        }
    )
    _save_registry(
        paths=paths,
        project_file=project_file,
        registry=updated,
    )
