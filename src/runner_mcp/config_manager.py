from __future__ import annotations

import fcntl
import hashlib
import os
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

from .adapters import AdapterError, get_adapter, inspect_project, list_adapters
from .config import (
    DatabaseConfig,
    DeploymentConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
    ServiceConfig,
    TestProfile,
)
from .github_mailbox import (
    GITHUB_MAILBOX_ENV_KEYS,
    GITHUB_REPOSITORY_ENV,
    GITHUB_REQUEST_REF_ENV,
    GITHUB_RESULT_REF_ENV,
    GITHUB_TOKEN_ENV,
    GitHubApiSession,
    GitHubMailboxConfig,
)
from .secure_io import PrivateAtomicWriteError, atomic_replace_private
from .onboarding import (
    OnboardingError,
    PrivatePaths,
    load_env_file,
    read_private_runtime,
)


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
    if path.is_symlink():
        raise ConfigManagerError("Project configuration must not be a symlink")

    try:
        atomic_replace_private(path, content.encode("utf-8"))
    except PrivateAtomicWriteError as exc:
        raise ConfigManagerError("Project configuration could not be written") from exc


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
        {**project.public_summary(code), "adapter": project.adapter}
        for code, project in sorted(registry.projects.items())
    ]


def list_project_adapters() -> list[dict[str, object]]:
    return list_adapters()


def project_capabilities(config_dir: Path, *, project: str) -> dict[str, object]:
    _, _, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    try:
        adapter = get_adapter(cfg.adapter)
        inspection = inspect_project(cfg.adapter, cfg.root)
    except AdapterError as exc:
        raise ConfigManagerError(str(exc)) from exc
    return {
        "project": project,
        "adapter": adapter.info.adapter_id,
        "adapter_name": adapter.info.display_name,
        "test_presets": list(adapter.info.test_presets),
        "migration_presets": list(adapter.info.migration_presets),
        "supports_services": adapter.info.supports_services,
        "supports_deployment": adapter.info.supports_deployment,
        "inspection": inspection,
    }


def add_project(
    config_dir: Path,
    *,
    code: str,
    display_name: str,
    repository: str,
    root: Path,
    adapter: str = "generic",
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
            adapter=adapter,
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


def configure_project_test_capacity(
    config_dir: Path,
    *,
    project: str,
    max_parallel_tests: int,
    max_queued_tests: int,
) -> dict[str, int | str]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    try:
        updated_project = cfg.model_copy(
            update={
                "max_parallel_tests": max_parallel_tests,
                "max_queued_tests": max_queued_tests,
            }
        )
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
        "project": project,
        "max_parallel_tests": updated_project.max_parallel_tests,
        "max_queued_tests": updated_project.max_queued_tests,
    }


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
            "parallel_safe": profile.parallel_safe,
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
    runtime: str = "default",
    parallel_safe: bool = False,
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
            runtime=runtime,
            parallel_safe=parallel_safe,
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
    runtime: str = "default",
    parallel_safe: bool = False,
) -> dict[str, Any]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if name in cfg.test_profiles:
        raise ConfigManagerError("Test profile is already configured")

    if preset == "auto":
        try:
            automatic = get_adapter(cfg.adapter).default_test_preset(cfg.root)
        except AdapterError as exc:
            raise ConfigManagerError(str(exc)) from exc
        if automatic is None:
            raise ConfigManagerError("Project adapter has no automatic test preset")
        preset = automatic

    profile = build_test_profile(
        project_root=cfg.root,
        preset=preset,
        executable=executable,
        arguments=arguments,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        max_log_bytes=max_log_bytes,
        env_passthrough=env_passthrough,
        runtime=runtime,
        parallel_safe=parallel_safe,
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
        "runtime": profile.runtime,
        "parallel_safe": profile.parallel_safe,
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


def _database_env_name(project: str) -> str:
    safe = project.upper().replace("-", "_")
    digest = hashlib.sha256(project.encode("utf-8")).hexdigest()[:8].upper()
    return f"RUNNER_MCP_DB_{safe}_{digest}"


def _write_private_environment(paths: PrivatePaths, values: dict[str, str]) -> None:
    for key, value in values.items():
        if not key or "\n" in key or "=" in key:
            raise ConfigManagerError("Invalid private environment key")
        if "\n" in value or "\r" in value or "\x00" in value:
            raise ConfigManagerError("Private environment values must be single-line text")

    lines = [
        "# Private Runner MCP runtime configuration.",
        "# Never commit this file to a repository.",
    ]
    lines.extend(f"{key}={shlex.quote(value)}" for key, value in sorted(values.items()))
    _atomic_write_private(paths.env_file, "\n".join(lines) + "\n")


def github_mailbox_config_status(config_dir: Path) -> dict[str, bool]:
    paths, _project_file, _registry = _load_for_edit(config_dir)
    values = load_env_file(paths.env_file)
    present = {
        key: bool(values.get(key, "").strip())
        for key in GITHUB_MAILBOX_ENV_KEYS
    }
    if not any(present.values()):
        return {"configured": False}
    if not all(present.values()):
        raise ConfigManagerError("GitHub mailbox private configuration is incomplete")

    try:
        GitHubMailboxConfig(
            repository=values[GITHUB_REPOSITORY_ENV],
            request_ref=values[GITHUB_REQUEST_REF_ENV],
            result_ref=values[GITHUB_RESULT_REF_ENV],
        )
        GitHubApiSession(token=values[GITHUB_TOKEN_ENV])
    except ValueError as exc:
        raise ConfigManagerError(
            "GitHub mailbox private configuration is invalid"
        ) from exc
    return {"configured": True}


def configure_github_mailbox(
    config_dir: Path,
    *,
    repository: str,
    request_ref: str,
    result_ref: str,
    token: str,
) -> dict[str, bool]:
    try:
        GitHubMailboxConfig(
            repository=repository,
            request_ref=request_ref,
            result_ref=result_ref,
        )
        GitHubApiSession(token=token)
    except ValueError as exc:
        raise ConfigManagerError(str(exc)) from exc

    paths, _project_file, _registry = _load_for_edit(config_dir)
    values = load_env_file(paths.env_file)
    values[GITHUB_REPOSITORY_ENV] = repository
    values[GITHUB_REQUEST_REF_ENV] = request_ref
    values[GITHUB_RESULT_REF_ENV] = result_ref
    values[GITHUB_TOKEN_ENV] = token

    with _configuration_lock(paths):
        _write_private_environment(paths, values)
    return {"configured": True}


def remove_github_mailbox(config_dir: Path) -> None:
    paths, _project_file, _registry = _load_for_edit(config_dir)
    values = load_env_file(paths.env_file)
    for key in GITHUB_MAILBOX_ENV_KEYS:
        values.pop(key, None)
    with _configuration_lock(paths):
        _write_private_environment(paths, values)


def list_database_configs(config_dir: Path) -> list[dict[str, Any]]:
    _, _, registry = _load_for_edit(config_dir)
    result: list[dict[str, Any]] = []
    for code, project in sorted(registry.projects.items()):
        database = project.database
        result.append(
            {
                "project": code,
                "configured": database is not None,
                "engine": database.engine if database is not None else None,
                "migrations_configured": (
                    database is not None and database.migrations is not None
                ),
            }
        )
    return result


def add_database_config(
    config_dir: Path,
    *,
    project: str,
    dsn: str,
) -> dict[str, Any]:
    if not dsn or len(dsn) > 32768 or any(char in dsn for char in "\r\n\x00"):
        raise ConfigManagerError("PostgreSQL connection string has an invalid format")

    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.database is not None:
        raise ConfigManagerError("Project database is already configured")

    env_name = _database_env_name(project)
    for other in registry.projects.values():
        if other.database is not None and other.database.dsn_env == env_name:
            raise ConfigManagerError("Database secret name collides with another project")

    try:
        database = DatabaseConfig(dsn_env=env_name)
        updated_project = cfg.model_copy(update={"database": database})
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

    # Write the secret first. If project config persistence fails, the secret is
    # orphaned but inactive; the inverse ordering could activate a config with no secret.
    env_values = load_env_file(paths.env_file)
    env_values[env_name] = dsn
    with _configuration_lock(paths):
        _write_private_environment(paths, env_values)
        _atomic_write_private(project_file, _serialize_registry(updated))

    return {
        "project": project,
        "configured": True,
        "engine": database.engine,
        "migrations_configured": False,
    }


def remove_database_config(config_dir: Path, *, project: str) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.database is None:
        raise ConfigManagerError("Project database is not configured")

    env_name = cfg.database.dsn_env
    updated_project = cfg.model_copy(update={"database": None})
    updated = ProjectRegistry(
        projects={
            **registry.projects,
            project: updated_project,
        }
    )
    env_values = load_env_file(paths.env_file)
    env_values.pop(env_name, None)

    with _configuration_lock(paths):
        # Disable use of the secret in project config first. An unused secret is
        # safer than an active DB config with a missing credential.
        _atomic_write_private(project_file, _serialize_registry(updated))
        _write_private_environment(paths, env_values)


def _detect_alembic(project_root: Path) -> Path:
    for candidate in (
        project_root / ".venv" / "bin" / "alembic",
        project_root / "venv" / "bin" / "alembic",
    ):
        if (
            candidate.exists()
            and candidate.is_file()
            and not candidate.is_symlink()
            and os.access(candidate, os.X_OK)
        ):
            return candidate.resolve()
    raise ConfigManagerError("Could not find Alembic in .venv/bin or venv/bin")


def add_migration_config(
    config_dir: Path,
    *,
    project: str,
    preset: str,
    dsn_target_env: str = "DATABASE_URL",
    status_executable: Path | None = None,
    status_arguments: list[str] | None = None,
    apply_executable: Path | None = None,
    apply_arguments: list[str] | None = None,
    cwd: str = ".",
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.database is None:
        raise ConfigManagerError("Configure the project database first")
    if cfg.database.migrations is not None:
        raise ConfigManagerError("Migration profile is already configured")

    if preset == "auto":
        try:
            automatic = get_adapter(cfg.adapter).default_migration_preset(cfg.root)
        except AdapterError as exc:
            raise ConfigManagerError(str(exc)) from exc
        if automatic is None:
            raise ConfigManagerError("Project adapter has no automatic migration preset")
        preset = automatic

    if preset == "alembic":
        executable = _detect_alembic(cfg.root)
        status_argv = [str(executable), "current"]
        apply_argv = [str(executable), "upgrade", "head"]
    elif preset == "custom":
        if status_executable is None or apply_executable is None:
            raise ConfigManagerError(
                "Custom migration profiles require status and apply executables"
            )
        status_resolved = _absolute_without_symlinks(
            status_executable,
            label="Migration status executable",
        )
        apply_resolved = _absolute_without_symlinks(
            apply_executable,
            label="Migration apply executable",
        )
        for label, executable in (
            ("Migration status executable", status_resolved),
            ("Migration apply executable", apply_resolved),
        ):
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise ConfigManagerError(f"{label} is unavailable or unsafe")
        status_argv = [str(status_resolved), *(status_arguments or [])]
        apply_argv = [str(apply_resolved), *(apply_arguments or [])]
    else:
        raise ConfigManagerError("Unknown migration preset")

    try:
        migrations = MigrationConfig(
            status_argv=status_argv,
            apply_argv=apply_argv,
            cwd=cwd,
            dsn_target_env=dsn_target_env,
            timeout_seconds=timeout_seconds,
        )
        database = cfg.database.model_copy(update={"migrations": migrations})
        updated_project = cfg.model_copy(update={"database": database})
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

    _save_registry(paths=paths, project_file=project_file, registry=updated)
    return {
        "project": project,
        "preset": preset,
        "configured": True,
        "timeout_seconds": migrations.timeout_seconds,
    }


def remove_migration_config(config_dir: Path, *, project: str) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.database is None or cfg.database.migrations is None:
        raise ConfigManagerError("Migration profile is not configured")

    database = cfg.database.model_copy(update={"migrations": None})
    updated_project = cfg.model_copy(update={"database": database})
    updated = ProjectRegistry(
        projects={
            **registry.projects,
            project: updated_project,
        }
    )
    _save_registry(paths=paths, project_file=project_file, registry=updated)


def list_deployment_configs(config_dir: Path) -> list[dict[str, Any]]:
    _, _, registry = _load_for_edit(config_dir)
    result: list[dict[str, Any]] = []
    for code, project in sorted(registry.projects.items()):
        deployment = project.deployment
        result.append(
            {
                "project": code,
                "configured": deployment is not None,
                "service": deployment.service if deployment is not None else None,
                "required_tests": (
                    list(deployment.required_tests) if deployment is not None else []
                ),
                "run_migrations": (
                    deployment.run_migrations if deployment is not None else False
                ),
            }
        )
    return result


def _prepare_deployment_storage(path: Path) -> Path:
    if not path.is_absolute():
        raise ConfigManagerError("Deployment release root must be absolute")
    parent = _absolute_without_symlinks(path.parent, label="Deployment release-root parent")
    target = parent / path.name
    if target.exists() and target.is_symlink():
        raise ConfigManagerError("Deployment release root must not be a symlink")
    target.mkdir(mode=0o700, exist_ok=True)
    os.chmod(target, 0o700)

    for name in ("releases", ".runtime-home"):
        child = target / name
        if child.exists() and child.is_symlink():
            raise ConfigManagerError(f"Deployment {name} directory is unsafe")
        child.mkdir(mode=0o700, exist_ok=True)
        os.chmod(child, 0o700)
    return target.resolve(strict=True)


def add_deployment_config(
    config_dir: Path,
    *,
    project: str,
    release_root: Path,
    service: str,
    required_tests: list[str] | None = None,
    run_migrations: bool = False,
    activation_timeout_seconds: int = 60,
) -> dict[str, Any]:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.environment != "staging":
        raise ConfigManagerError("Deployment configuration is allowed only for staging")
    if cfg.deployment is not None:
        raise ConfigManagerError("Deployment is already configured")

    service_cfg = cfg.services.get(service)
    if service_cfg is None:
        raise ConfigManagerError("Deployment service alias is not configured")
    if not service_cfg.allow_restart:
        raise ConfigManagerError("Deployment service must explicitly allow restart")
    if service_cfg.health_url is None:
        raise ConfigManagerError("Deployment service must have a health check")

    tests = list(required_tests or [])
    missing = [name for name in tests if name not in cfg.test_profiles]
    if missing:
        raise ConfigManagerError(
            "Unknown required test profile(s): " + ", ".join(sorted(missing))
        )
    if run_migrations and (
        cfg.database is None or cfg.database.migrations is None
    ):
        raise ConfigManagerError(
            "Database and migration configuration are required before deploy migrations"
        )

    prepared_root = _prepare_deployment_storage(release_root)
    try:
        deployment = DeploymentConfig(
            release_root=prepared_root,
            service=service,
            required_tests=tests,
            run_migrations=run_migrations,
            activation_timeout_seconds=activation_timeout_seconds,
        )
        updated_project = cfg.model_copy(update={"deployment": deployment})
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

    _save_registry(paths=paths, project_file=project_file, registry=updated)
    return {
        "project": project,
        "configured": True,
        "service": service,
        "required_tests": tests,
        "run_migrations": run_migrations,
    }


def remove_deployment_config(config_dir: Path, *, project: str) -> None:
    paths, project_file, registry = _load_for_edit(config_dir)
    cfg = registry.projects.get(project)
    if cfg is None:
        raise ConfigManagerError("Unknown project")
    if cfg.deployment is None:
        raise ConfigManagerError("Deployment is not configured")

    updated_project = cfg.model_copy(update={"deployment": None})
    updated = ProjectRegistry(
        projects={
            **registry.projects,
            project: updated_project,
        }
    )
    # Release data is deliberately left untouched. Removing configuration must
    # never silently delete rollback material.
    _save_registry(paths=paths, project_file=project_file, registry=updated)
