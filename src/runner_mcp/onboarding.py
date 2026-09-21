from __future__ import annotations

import os
import re
import secrets
import shlex
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .config import ProjectConfig, ProjectRegistry
from .github_mailbox import GITHUB_MAILBOX_ENV_KEYS
from .operational_safety import OperatorSafetyGuard
from .server import Settings


class OnboardingError(RuntimeError):
    pass


@dataclass(frozen=True)
class PrivatePaths:
    config_dir: Path
    env_file: Path
    projects_file: Path
    stop_file: Path
    jobs_dir: Path
    database_backups_dir: Path
    deployment_jobs_dir: Path
    approvals_dir: Path
    audit_log: Path

    @classmethod
    def for_config_dir(cls, config_dir: Path) -> PrivatePaths:
        root = config_dir.expanduser().resolve()
        return cls(
            config_dir=root,
            env_file=root / "runner-mcp.env",
            projects_file=root / "projects.yml",
            stop_file=root / "operator.stop",
            jobs_dir=root / "jobs",
            database_backups_dir=root / "database-backups",
            deployment_jobs_dir=root / "deployment-jobs",
            approvals_dir=root / "approvals",
            audit_log=root / "audit.jsonl",
        )


@dataclass(frozen=True)
class SetupAnswers:
    resource_url: str
    auth_issuer: str
    project_code: str
    project_name: str
    repository: str
    project_root: Path
    min_releases_to_keep: int = 20
    min_release_age_days: int = 90
    pitr_retention_days: int = 30
    pre_migration_backup_days: int = 180
    max_test_jobs: int = 2
    max_queued_tests: int = 64


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def default_config_dir() -> Path:
    override = os.getenv("RUNNER_MCP_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".config" / "runner-mcp").resolve()


def _validate_public_https_url(value: str, *, name: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        raise OnboardingError(f"{name} must be an absolute URL")
    if parsed.username or parsed.password:
        raise OnboardingError(f"{name} must not contain credentials")
    host = (parsed.hostname or "").lower()
    loopback = host in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not loopback:
        raise OnboardingError(f"{name} must use HTTPS unless it is loopback-only")
    if parsed.scheme not in {"http", "https"}:
        raise OnboardingError(f"{name} must use HTTP or HTTPS")
    return value.rstrip("/") + ("/" if parsed.path in {"", "/"} else "")


def validate_setup_answers(answers: SetupAnswers) -> SetupAnswers:
    _validate_public_https_url(answers.resource_url, name="MCP resource URL")
    _validate_public_https_url(answers.auth_issuer, name="Auth issuer URL")

    root = answers.project_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise OnboardingError("Project root must be an existing directory")

    try:
        ProjectRegistry(
            projects={
                answers.project_code: ProjectConfig(
                    display_name=answers.project_name,
                    repository=answers.repository,
                    root=root,
                )
            }
        ).validate_codes()
    except ValueError as exc:
        raise OnboardingError(str(exc)) from exc

    if not 2 <= answers.min_releases_to_keep <= 1000:
        raise OnboardingError("Minimum releases must be between 2 and 1000")
    if not 1 <= answers.min_release_age_days <= 3650:
        raise OnboardingError("Release retention days must be between 1 and 3650")
    if not 1 <= answers.pitr_retention_days <= 3650:
        raise OnboardingError("PITR retention days must be between 1 and 3650")
    if not 1 <= answers.pre_migration_backup_days <= 3650:
        raise OnboardingError("Pre-migration backup days must be between 1 and 3650")
    if not 1 <= answers.max_test_jobs <= 16:
        raise OnboardingError("Maximum test jobs must be between 1 and 16")
    if not 1 <= answers.max_queued_tests <= 1024:
        raise OnboardingError("Maximum queued tests must be between 1 and 1024")

    return SetupAnswers(
        resource_url=answers.resource_url,
        auth_issuer=answers.auth_issuer,
        project_code=answers.project_code,
        project_name=answers.project_name,
        repository=answers.repository,
        project_root=root,
        min_releases_to_keep=answers.min_releases_to_keep,
        min_release_age_days=answers.min_release_age_days,
        pitr_retention_days=answers.pitr_retention_days,
        pre_migration_backup_days=answers.pre_migration_backup_days,
        max_test_jobs=answers.max_test_jobs,
        max_queued_tests=answers.max_queued_tests,
    )


def _quote_env_value(value: str) -> str:
    if "\n" in value or "\r" in value or "\x00" in value:
        raise OnboardingError("Environment values must be single-line text")
    return shlex.quote(value)


def render_env_file(
    *,
    paths: PrivatePaths,
    answers: SetupAnswers,
    bearer_token: str,
    extra_values: dict[str, str] | None = None,
) -> str:
    values = {
        "RUNNER_MCP_BEARER_TOKEN": bearer_token,
        "RUNNER_MCP_AUTH_ISSUER": answers.auth_issuer,
        "RUNNER_MCP_RESOURCE_URL": answers.resource_url,
        "RUNNER_MCP_PROJECTS_CONFIG": str(paths.projects_file),
        "RUNNER_MCP_AUDIT_LOG": str(paths.audit_log),
        "RUNNER_MCP_RATE_LIMIT_PER_MINUTE": "600",
        "RUNNER_MCP_OPERATOR_STOP_FILE": str(paths.stop_file),
        "RUNNER_MCP_RETENTION_CONFIRMED": "true",
        "RUNNER_MCP_MIN_RELEASES_TO_KEEP": str(answers.min_releases_to_keep),
        "RUNNER_MCP_MIN_RELEASE_DAYS": str(answers.min_release_age_days),
        "RUNNER_MCP_PITR_RETENTION_DAYS": str(answers.pitr_retention_days),
        "RUNNER_MCP_PRE_MIGRATION_BACKUP_DAYS": str(
            answers.pre_migration_backup_days
        ),
        "RUNNER_MCP_TEST_JOBS_ROOT": str(paths.jobs_dir),
        "RUNNER_MCP_MAX_TEST_JOBS": str(answers.max_test_jobs),
        "RUNNER_MCP_MAX_QUEUED_TESTS": str(answers.max_queued_tests),
        "RUNNER_MCP_MAILBOX_WORKERS": "4",
        "RUNNER_MCP_MAILBOX_MAX_INFLIGHT": "32",
        "RUNNER_MCP_DATABASE_BACKUP_ROOT": str(paths.database_backups_dir),
        "RUNNER_MCP_DEPLOY_JOBS_ROOT": str(paths.deployment_jobs_dir),
        "RUNNER_MCP_APPROVAL_ROOT": str(paths.approvals_dir),
        "RUNNER_MCP_APPROVAL_TTL_SECONDS": "600",
    }
    for key, value in sorted((extra_values or {}).items()):
        if (
            key.startswith("RUNNER_MCP_DB_")
            or key in GITHUB_MAILBOX_ENV_KEYS
            or key == "RUNNER_MCP_RATE_LIMIT_PER_MINUTE"
        ):
            values[key] = value
    lines = [
        "# Private Runner MCP runtime configuration.",
        "# Never commit this file to a repository.",
    ]
    lines.extend(f"{key}={_quote_env_value(value)}" for key, value in values.items())
    return "\n".join(lines) + "\n"


def render_projects_file(answers: SetupAnswers) -> str:
    payload = {
        "projects": {
            answers.project_code: {
                "display_name": answers.project_name,
                "repository": answers.repository,
                "environment": "staging",
                "root": str(answers.project_root),
                "services": {},
                "test_profiles": {},
            }
        }
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _write_private_file(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise OnboardingError(f"{path.name} already exists; use --overwrite to replace it")

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if not overwrite:
        flags |= os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if fd >= 0:
            os.close(fd)
    os.chmod(path, 0o600)


def install_private_configuration(
    *,
    config_dir: Path,
    answers: SetupAnswers,
    overwrite: bool = False,
    rotate_token: bool = False,
) -> PrivatePaths:
    validated = validate_setup_answers(answers)
    paths = PrivatePaths.for_config_dir(config_dir)

    paths.config_dir.mkdir(parents=True, exist_ok=True)
    if paths.config_dir.is_symlink():
        raise OnboardingError("Configuration directory must not be a symlink")
    os.chmod(paths.config_dir, 0o700)

    paths.jobs_dir.mkdir(parents=True, exist_ok=True)
    if paths.jobs_dir.is_symlink():
        raise OnboardingError("Test jobs directory must not be a symlink")
    os.chmod(paths.jobs_dir, 0o700)

    paths.database_backups_dir.mkdir(parents=True, exist_ok=True)
    if paths.database_backups_dir.is_symlink():
        raise OnboardingError("Database backup directory must not be a symlink")
    os.chmod(paths.database_backups_dir, 0o700)

    paths.deployment_jobs_dir.mkdir(parents=True, exist_ok=True)
    if paths.deployment_jobs_dir.is_symlink():
        raise OnboardingError("Deployment jobs directory must not be a symlink")
    os.chmod(paths.deployment_jobs_dir, 0o700)

    paths.approvals_dir.mkdir(parents=True, exist_ok=True)
    if paths.approvals_dir.is_symlink():
        raise OnboardingError("Approval directory must not be a symlink")
    os.chmod(paths.approvals_dir, 0o700)

    token: str | None = None
    existing_private_values: dict[str, str] = {}
    if overwrite and paths.env_file.exists():
        _require_private_mode(
            paths.env_file,
            0o600,
            label="Existing private environment file",
        )
        existing = load_env_file(paths.env_file)
        existing_private_values = {
            key: value
            for key, value in existing.items()
            if key.startswith("RUNNER_MCP_DB_")
            or key in GITHUB_MAILBOX_ENV_KEYS
            or key == "RUNNER_MCP_RATE_LIMIT_PER_MINUTE"
        }
        if not rotate_token:
            candidate = existing.get("RUNNER_MCP_BEARER_TOKEN", "")
            if len(candidate) >= 32:
                token = candidate

    token = token or secrets.token_urlsafe(48)
    env_content = render_env_file(
        paths=paths,
        answers=validated,
        bearer_token=token,
        extra_values=existing_private_values,
    )
    projects_content = render_projects_file(validated)

    # Validate both complete documents before writing either one.
    parsed = yaml.safe_load(projects_content)
    registry = ProjectRegistry.model_validate(parsed)
    registry.validate_codes()

    _write_private_file(
        paths.projects_file,
        projects_content,
        overwrite=overwrite,
    )
    try:
        _write_private_file(
            paths.env_file,
            env_content,
            overwrite=overwrite,
        )
    except Exception:
        if not overwrite:
            paths.projects_file.unlink(missing_ok=True)
        raise

    return paths


_ENV_LINE_RE = re.compile(r"^[A-Z_][A-Z0-9_]*=")


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise OnboardingError("Private environment file is unavailable")

    loaded: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not _ENV_LINE_RE.match(line):
            raise OnboardingError(f"Invalid environment line {line_number}")
        key, _, encoded = line.partition("=")
        try:
            parts = shlex.split(encoded, posix=True)
        except ValueError as exc:
            raise OnboardingError(f"Invalid quoting on environment line {line_number}") from exc
        if len(parts) > 1:
            raise OnboardingError(f"Invalid environment value on line {line_number}")
        value = parts[0] if parts else ""
        loaded[key] = value
    return loaded


def _require_private_mode(path: Path, expected: int, *, label: str) -> None:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise OnboardingError(f"{label} is unavailable") from exc
    if mode != expected:
        raise OnboardingError(
            f"{label} permissions are unsafe; expected mode {expected:04o}"
        )


def read_private_runtime(config_dir: Path) -> tuple[PrivatePaths, Settings, ProjectRegistry]:
    paths = PrivatePaths.for_config_dir(config_dir)
    _require_private_mode(paths.config_dir, 0o700, label="Private configuration directory")
    _require_private_mode(paths.env_file, 0o600, label="Private environment file")

    values = load_env_file(paths.env_file)
    settings = Settings.from_mapping(values)

    project_file = settings.projects_config.expanduser().resolve()
    _require_private_mode(project_file, 0o600, label="Private project configuration")
    try:
        registry = ProjectRegistry.model_validate(
            yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}
        )
        registry.validate_codes()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise OnboardingError("Private project configuration is invalid") from exc
    return paths, settings, registry


def operator_stop_status(config_dir: Path) -> tuple[PrivatePaths, OperatorSafetyGuard]:
    paths, settings, _ = read_private_runtime(config_dir)
    guard = OperatorSafetyGuard(
        stop_file=settings.operator_stop_file,
        retention=settings.retention_policy,
        retention_confirmed=settings.retention_confirmed,
    )
    return paths, guard


def enable_operator_stop(config_dir: Path) -> None:
    paths, guard = operator_stop_status(config_dir)
    if guard.stop_file is None:
        raise OnboardingError("Operator stop is not configured")
    if guard.stop_file.exists() and guard.stop_file.is_symlink():
        raise OnboardingError("Operator stop file must not be a symlink")
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(guard.stop_file, flags, 0o600)
    except OSError as exc:
        raise OnboardingError("Operator stop file could not be created safely") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
            fd = -1
            handle.write("operator emergency stop\n")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if fd >= 0:
            os.close(fd)
    os.chmod(guard.stop_file, 0o600)


def disable_operator_stop(config_dir: Path, *, confirmation: str) -> None:
    _, guard = operator_stop_status(config_dir)
    if guard.stop_file is None:
        raise OnboardingError("Operator stop is not configured")
    if confirmation != "UNLOCK":
        raise OnboardingError("Emergency stop remains active; confirmation must be UNLOCK")
    if guard.stop_file.is_symlink():
        raise OnboardingError("Operator stop file must not be a symlink")
    guard.stop_file.unlink(missing_ok=True)


def _mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return None


def run_doctor(config_dir: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    paths = PrivatePaths.for_config_dir(config_dir)

    config_mode = _mode(paths.config_dir)
    checks.append(
        DoctorCheck(
            "private configuration directory",
            "PASS" if config_mode == 0o700 else "FAIL",
            "permissions are restricted" if config_mode == 0o700 else "expected mode 0700",
        )
    )

    for label, path in (
        ("runtime environment file", paths.env_file),
        ("project configuration file", paths.projects_file),
    ):
        mode = _mode(path)
        checks.append(
            DoctorCheck(
                label,
                "PASS" if mode == 0o600 else "FAIL",
                "permissions are restricted" if mode == 0o600 else "expected mode 0600",
            )
        )

    try:
        _, settings, registry = read_private_runtime(config_dir)
    except (OSError, ValueError, RuntimeError, yaml.YAMLError):
        checks.append(
            DoctorCheck(
                "configuration parse",
                "FAIL",
                "configuration could not be loaded",
            )
        )
        return checks

    checks.append(DoctorCheck("configuration parse", "PASS", "configuration is valid"))

    guard = OperatorSafetyGuard(
        stop_file=settings.operator_stop_file,
        retention=settings.retention_policy,
        retention_confirmed=settings.retention_confirmed,
    )
    safety = guard.status()
    checks.append(
        DoctorCheck(
            "retention confirmation",
            "PASS" if settings.retention_confirmed else "FAIL",
            "confirmed" if settings.retention_confirmed else "not confirmed",
        )
    )
    checks.append(
        DoctorCheck(
            "operator emergency stop",
            "WARN" if safety.stop_active else "PASS",
            "currently active" if safety.stop_active else "available and inactive",
        )
    )

    resource = urlsplit(settings.resource_url)
    secure_transport = resource.scheme == "https" or (resource.hostname or "").lower() in {
        "localhost",
        "127.0.0.1",
        "::1",
    }
    checks.append(
        DoctorCheck(
            "MCP resource transport",
            "PASS" if secure_transport else "FAIL",
            "HTTPS or loopback transport" if secure_transport else "non-loopback HTTP is unsafe",
        )
    )

    if settings.test_jobs_root is None:
        checks.append(DoctorCheck("test job storage", "WARN", "test execution is not configured"))
    else:
        jobs_ok = (
            settings.test_jobs_root.exists()
            and settings.test_jobs_root.is_dir()
            and not settings.test_jobs_root.is_symlink()
            and os.access(settings.test_jobs_root, os.W_OK | os.X_OK)
        )
        checks.append(
            DoctorCheck(
                "test job storage",
                "PASS" if jobs_ok else "FAIL",
                "available" if jobs_ok else "unavailable or unsafe",
            )
        )

    if settings.deployment_jobs_root is None:
        checks.append(
            DoctorCheck(
                "deployment job storage",
                "WARN",
                "staging deployment jobs are not configured",
            )
        )
    else:
        deployment_jobs_ok = (
            settings.deployment_jobs_root.exists()
            and settings.deployment_jobs_root.is_dir()
            and not settings.deployment_jobs_root.is_symlink()
            and os.access(settings.deployment_jobs_root, os.W_OK | os.X_OK)
        )
        checks.append(
            DoctorCheck(
                "deployment job storage",
                "PASS" if deployment_jobs_ok else "FAIL",
                "available" if deployment_jobs_ok else "unavailable or unsafe",
            )
        )

    if settings.database_backup_root is None:
        checks.append(
            DoctorCheck(
                "database backup storage",
                "WARN",
                "database backups are not configured",
            )
        )
    else:
        backup_ok = (
            settings.database_backup_root.exists()
            and settings.database_backup_root.is_dir()
            and not settings.database_backup_root.is_symlink()
            and os.access(settings.database_backup_root, os.W_OK | os.X_OK)
        )
        checks.append(
            DoctorCheck(
                "database backup storage",
                "PASS" if backup_ok else "FAIL",
                "available" if backup_ok else "unavailable or unsafe",
            )
        )

    for code, project in sorted(registry.projects.items()):
        root_ok = project.root.exists() and project.root.is_dir() and not project.root.is_symlink()
        checks.append(
            DoctorCheck(
                f"project {code}",
                "PASS" if root_ok else "FAIL",
                "root is available" if root_ok else "root is unavailable or symlinked",
            )
        )
        for profile_name, profile in sorted(project.test_profiles.items()):
            executable = Path(profile.argv[0])
            executable_ok = (
                executable.exists()
                and executable.is_file()
                and not executable.is_symlink()
                and os.access(executable, os.X_OK)
            )
            checks.append(
                DoctorCheck(
                    f"test profile {code}/{profile_name}",
                    "PASS" if executable_ok else "FAIL",
                    "executable is available" if executable_ok else "executable is unavailable or unsafe",
                )
            )

    return checks


def prompt_setup_answers(
    *,
    input_fn: Callable[[str], str] | None = None,
) -> SetupAnswers:
    reader = input_fn or input

    def ask(prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        value = reader(f"{prompt}{suffix}: ").strip()
        return value or (default or "")

    def ask_required(prompt: str) -> str:
        while True:
            value = reader(f"{prompt}: ").strip()
            if value:
                return value

    mode = ask("Setup mode (local/public)", "local").lower()
    if mode == "local":
        resource_url = "http://127.0.0.1:8000/mcp"
        auth_issuer = "http://127.0.0.1:8000/"
    elif mode == "public":
        resource_url = ask_required("Public MCP HTTPS URL")
        parsed = urlsplit(resource_url)
        issuer_default = (
            f"{parsed.scheme}://{parsed.netloc}/"
            if parsed.scheme and parsed.netloc
            else None
        )
        auth_issuer = ask("Auth issuer URL", issuer_default)
    else:
        raise OnboardingError("Setup mode must be local or public")

    project_code = ask("Project code", "myproject")
    project_name = ask("Project display name", project_code)
    repository = ask_required("Git repository (owner/name)")
    project_root = Path(ask_required("Project folder"))

    def ask_int(prompt: str, default: int) -> int:
        raw = ask(prompt, str(default))
        try:
            return int(raw)
        except ValueError as exc:
            raise OnboardingError(f"{prompt} must be a number") from exc

    return SetupAnswers(
        resource_url=resource_url,
        auth_issuer=auth_issuer,
        project_code=project_code,
        project_name=project_name,
        repository=repository,
        project_root=project_root,
        min_releases_to_keep=ask_int("Minimum releases to keep", 20),
        min_release_age_days=ask_int("Minimum release retention days", 90),
        pitr_retention_days=ask_int("Database PITR retention days", 30),
        pre_migration_backup_days=ask_int("Pre-migration backup retention days", 180),
        max_test_jobs=ask_int("Maximum simultaneous test jobs", 2),
        max_queued_tests=ask_int("Maximum queued test jobs", 64),
    )
