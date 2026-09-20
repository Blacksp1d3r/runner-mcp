from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tarfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .config import DeploymentConfig, ProjectConfig, ProjectRegistry
from .database_manager import DatabaseManager, DatabaseManagerError
from .operational_safety import ActionClass, OperatorSafetyGuard, OperatorStopActive
from .service_manager import ServiceManager, ServiceManagerError
from .test_runner import TestRunner, TestRunnerError


class DeploymentError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def _find_git() -> Path:
    for candidate in (Path("/usr/bin/git"), Path("/bin/git")):
        if (
            candidate.exists()
            and candidate.is_file()
            and not candidate.is_symlink()
            and os.access(candidate, os.X_OK)
        ):
            return candidate
    raise DeploymentError("git is unavailable")


def _directory_without_symlinks(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    absolute = expanded if expanded.is_absolute() else Path.cwd() / expanded
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise DeploymentError(f"{label} must not contain symlinks")
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise DeploymentError(f"{label} is unavailable") from exc
    if not resolved.is_dir():
        raise DeploymentError(f"{label} is unavailable")
    return resolved


class DeploymentManager:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        services: ServiceManager,
        tests: TestRunner | None,
        database: DatabaseManager,
        git_path: Path | None = None,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.services = services
        self.tests = tests
        self.database = database
        self.git_path = git_path
        self.poll_interval_seconds = poll_interval_seconds
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, project: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._locks.get(project)
            if lock is None:
                lock = threading.Lock()
                self._locks[project] = lock
            return lock

    def _project(self, project: str) -> tuple[ProjectConfig, DeploymentConfig]:
        config = self.registry.projects.get(project)
        if config is None:
            raise DeploymentError("Unknown or disabled project")
        if config.environment != "staging":
            raise DeploymentError("Deployment is allowed only for staging projects")
        if config.deployment is None:
            raise DeploymentError("Staging deployment is not configured")
        return config, config.deployment

    def _git(self) -> Path:
        if self.git_path is None:
            self.git_path = _find_git()
        return self.git_path

    @staticmethod
    def _private_home(release_root: Path) -> Path:
        home = release_root / ".runtime-home"
        if not home.exists() or home.is_symlink() or not home.is_dir():
            raise DeploymentError("Deployment runtime home is unavailable or unsafe")
        if stat.S_IMODE(home.stat().st_mode) != 0o700:
            raise DeploymentError("Deployment runtime home must use mode 0700")
        return home

    def _git_env(self, release_root: Path) -> dict[str, str]:
        return {
            "HOME": str(self._private_home(release_root)),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }

    def _run_git(
        self,
        root: Path,
        release_root: Path,
        arguments: list[str],
        *,
        timeout: int = 60,
    ) -> str:
        try:
            completed = subprocess.run(
                [
                    str(self._git()),
                    "-c",
                    "core.fsmonitor=false",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "-C",
                    str(root),
                    *arguments,
                ],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                env=self._git_env(release_root),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DeploymentError("Git preflight command failed") from exc
        if completed.returncode != 0:
            raise DeploymentError("Git preflight command failed")
        return completed.stdout.strip()

    @staticmethod
    def _prepare_release_root(
        config: DeploymentConfig,
        *,
        create: bool,
    ) -> tuple[Path, Path]:
        release_root = config.release_root
        if create:
            parent = release_root.parent
            if not parent.exists():
                raise DeploymentError("Deployment release-root parent is unavailable")
            _directory_without_symlinks(parent, label="Deployment release-root parent")
            if release_root.exists() and release_root.is_symlink():
                raise DeploymentError("Deployment release root must not be a symlink")
            release_root.mkdir(mode=0o700, exist_ok=True)
            os.chmod(release_root, 0o700)

        resolved = _directory_without_symlinks(
            release_root,
            label="Deployment release root",
        )
        if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
            raise DeploymentError("Deployment release root must use mode 0700")

        runtime_home = resolved / ".runtime-home"
        if create:
            if runtime_home.exists() and runtime_home.is_symlink():
                raise DeploymentError("Deployment runtime home is unsafe")
            runtime_home.mkdir(mode=0o700, exist_ok=True)
            os.chmod(runtime_home, 0o700)
        DeploymentManager._private_home(resolved)

        releases = resolved / "releases"
        if create:
            if releases.exists() and releases.is_symlink():
                raise DeploymentError("Deployment releases directory is unsafe")
            releases.mkdir(mode=0o700, exist_ok=True)
            os.chmod(releases, 0o700)
        releases_resolved = _directory_without_symlinks(
            releases,
            label="Deployment releases directory",
        )
        if stat.S_IMODE(releases_resolved.stat().st_mode) != 0o700:
            raise DeploymentError("Deployment releases directory must use mode 0700")
        return resolved, releases_resolved

    @staticmethod
    def _current_release_id(release_root: Path, releases: Path) -> str | None:
        current = release_root / "current"
        if not current.exists() and not current.is_symlink():
            return None
        if not current.is_symlink():
            raise DeploymentError("Deployment current pointer is not a symlink")

        target = os.readlink(current)
        target_path = Path(target)
        try:
            if target_path.is_absolute():
                resolved = target_path.resolve(strict=True)
            else:
                resolved = (release_root / target_path).resolve(strict=True)
        except OSError as exc:
            raise DeploymentError("Deployment current pointer target is unavailable") from exc
        try:
            resolved.relative_to(releases)
        except ValueError as exc:
            raise DeploymentError("Deployment current pointer escapes release storage") from exc
        if resolved.parent != releases:
            raise DeploymentError("Deployment current pointer has an invalid target")
        return resolved.name

    @staticmethod
    def _validate_release_id(value: str) -> None:
        if not value or "/" in value or "\\" in value or value in {".", ".."}:
            raise DeploymentError("Invalid release identifier")

    @staticmethod
    def _write_metadata(release_dir: Path, payload: dict) -> None:
        path = release_dir / ".runner-mcp-release.json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
        except OSError as exc:
            raise DeploymentError("Could not create release metadata") from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
                fd = -1
                json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if fd >= 0:
                os.close(fd)
        os.chmod(path, 0o600)

    @staticmethod
    def _activate_release(
        release_root: Path,
        releases: Path,
        release_id: str,
    ) -> None:
        DeploymentManager._validate_release_id(release_id)
        target = releases / release_id
        if not target.exists() or not target.is_dir() or target.is_symlink():
            raise DeploymentError("Release is unavailable for activation")

        current = release_root / "current"
        if current.exists() and not current.is_symlink():
            raise DeploymentError("Deployment current pointer is unsafe")

        temp = release_root / f".current-{uuid4().hex}"
        try:
            temp.symlink_to(Path("releases") / release_id)
            os.replace(temp, current)
            directory_fd = os.open(release_root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temp.unlink(missing_ok=True)

    def _source_state(
        self,
        project_root: Path,
        release_root: Path,
    ) -> tuple[str, str]:
        project_root = _directory_without_symlinks(
            project_root,
            label="Project root",
        )
        inside = self._run_git(
            project_root,
            release_root,
            ["rev-parse", "--is-inside-work-tree"],
        )
        if inside != "true":
            raise DeploymentError("Project root is not a Git working tree")

        dirty = self._run_git(
            project_root,
            release_root,
            ["status", "--porcelain=v1", "--untracked-files=normal"],
        )
        if dirty:
            raise DeploymentError("Project working tree must be clean before deployment")

        commit = self._run_git(
            project_root,
            release_root,
            ["rev-parse", "--verify", "HEAD"],
        )
        if len(commit) != 40 or any(char not in "0123456789abcdefABCDEF" for char in commit):
            raise DeploymentError("Git HEAD did not resolve to a full commit")
        return commit.lower(), commit[:12].lower()

    def _validate_configuration(
        self,
        project: str,
        config: ProjectConfig,
        deployment: DeploymentConfig,
    ) -> None:
        service = config.services.get(deployment.service)
        if service is None:
            raise DeploymentError("Deployment service alias is not configured")
        if not service.allow_restart:
            raise DeploymentError("Deployment service must explicitly allow restart")
        if service.health_url is None:
            raise DeploymentError("Deployment service must have a health check")

        for profile in deployment.required_tests:
            if profile not in config.test_profiles:
                raise DeploymentError(
                    f"Required deployment test profile is not configured: {profile}"
                )
        if deployment.required_tests and self.tests is None:
            raise DeploymentError("Test execution is not configured")

        if deployment.run_migrations:
            if config.database is None or config.database.migrations is None:
                raise DeploymentError("Deployment migrations are enabled but not configured")
            if self.database.backup_root is None:
                raise DeploymentError("Database backup storage is required for migrations")

        if project not in self.registry.projects:
            raise DeploymentError("Unknown project")

    def plan(self, project: str) -> dict:
        config, deployment = self._project(project)
        self._validate_configuration(project, config, deployment)
        release_root, releases = self._prepare_release_root(
            deployment,
            create=False,
        )
        commit, short_commit = self._source_state(config.root, release_root)
        current = self._current_release_id(release_root, releases)
        return {
            "project": project,
            "environment": config.environment,
            "commit": commit,
            "short_commit": short_commit,
            "current_release": current,
            "service": deployment.service,
            "required_tests": list(deployment.required_tests),
            "run_migrations": deployment.run_migrations,
            "automatic_code_rollback": not deployment.run_migrations,
        }

    def _run_required_tests(self, project: str, deployment: DeploymentConfig) -> list[dict]:
        if not deployment.required_tests:
            return []
        if self.tests is None:
            raise DeploymentError("Test execution is not configured")

        results: list[dict] = []
        for suite in deployment.required_tests:
            self.safety.assert_action_allowed(ActionClass.DEPLOY)
            try:
                started = self.tests.start_test(project, suite)
            except TestRunnerError as exc:
                raise DeploymentError(str(exc)) from exc
            job_id = started["job_id"]
            while True:
                status = self.tests.status(job_id)
                if status["status"] not in {"queued", "running"}:
                    break
                if self.safety.status().stop_active:
                    self.tests.cancel(job_id)
                    raise OperatorStopActive("Operator emergency stop is active")
                time.sleep(self.poll_interval_seconds)

            results.append(
                {
                    "suite": suite,
                    "status": status["status"],
                    "job_id": job_id,
                }
            )
            if status["status"] != "passed":
                raise DeploymentError(f"Required test did not pass: {suite}")
        return results

    def _create_release(
        self,
        *,
        config: ProjectConfig,
        release_root: Path,
        releases: Path,
        commit: str,
        short_commit: str,
        previous_release: str | None,
    ) -> tuple[str, Path]:
        release_id = (
            utc_now().strftime("%Y%m%dT%H%M%SZ")
            + f"-{short_commit}-{uuid4().hex[:6]}"
        )
        self._validate_release_id(release_id)
        release_dir = releases / release_id
        if release_dir.exists():
            raise DeploymentError("Release identifier already exists")
        release_dir.mkdir(mode=0o700)

        archive_path = release_root / f".archive-{uuid4().hex}.tar"
        try:
            try:
                completed = subprocess.run(
                    [
                        str(self._git()),
                        "-c",
                        "core.fsmonitor=false",
                        "-c",
                        "core.hooksPath=/dev/null",
                        "-C",
                        str(config.root),
                        "archive",
                        "--format=tar",
                        f"--output={archive_path}",
                        commit,
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=120,
                    check=False,
                    shell=False,
                    env=self._git_env(release_root),
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise DeploymentError("Git archive creation failed") from exc
            if completed.returncode != 0:
                raise DeploymentError("Git archive creation failed")

            if archive_path.is_symlink() or not archive_path.is_file():
                raise DeploymentError("Git archive output is unsafe")

            with tarfile.open(archive_path, mode="r:") as archive:
                members = archive.getmembers()
                if any(member.issym() or member.islnk() for member in members):
                    raise DeploymentError("Repository symlinks are not allowed in releases")
                archive.extractall(release_dir, filter="data")

            self._write_metadata(
                release_dir,
                {
                    "release_id": release_id,
                    "commit": commit,
                    "created_at": utc_now().isoformat(),
                    "previous_release": previous_release,
                    "environment": config.environment,
                    "migrations_applied": False,
                    "pre_migration_backup_id": None,
                },
            )
            return release_id, release_dir
        except Exception:
            shutil.rmtree(release_dir, ignore_errors=True)
            raise
        finally:
            archive_path.unlink(missing_ok=True)

    @staticmethod
    def _update_release_metadata(
        release_dir: Path,
        *,
        migrations_applied: bool,
        backup_id: str | None,
    ) -> None:
        path = release_dir / ".runner-mcp-release.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise DeploymentError("Release metadata is unavailable") from exc
        payload["migrations_applied"] = migrations_applied
        payload["pre_migration_backup_id"] = backup_id

        temp = release_dir / f".metadata-{uuid4().hex}.tmp"
        try:
            with temp.open("x", encoding="utf-8") as handle:
                os.chmod(temp, 0o600)
                json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
            os.chmod(path, 0o600)
        finally:
            temp.unlink(missing_ok=True)

    def _wait_healthy(
        self,
        project: str,
        service: str,
        *,
        timeout_seconds: int,
    ) -> tuple[bool, dict | None]:
        deadline = time.monotonic() + timeout_seconds
        last: dict | None = None
        while time.monotonic() < deadline:
            if self.safety.status().stop_active:
                return False, last
            try:
                last = self.services.status(project, service)
            except ServiceManagerError:
                last = None
            if (
                last is not None
                and last.get("active_state") == "active"
                and last.get("health") == "healthy"
            ):
                return True, last
            time.sleep(self.poll_interval_seconds)
        return False, last

    def _read_release_metadata(
        self,
        releases: Path,
        release_id: str,
    ) -> dict:
        self._validate_release_id(release_id)
        release_dir = releases / release_id
        if not release_dir.exists() or release_dir.is_symlink() or not release_dir.is_dir():
            raise DeploymentError("Release metadata target is unavailable")
        try:
            release_dir.resolve(strict=True).relative_to(releases)
        except (OSError, ValueError) as exc:
            raise DeploymentError("Release metadata target is unsafe") from exc

        path = release_dir / ".runner-mcp-release.json"
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise DeploymentError("Release metadata is unavailable")
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise DeploymentError("Release metadata permissions are unsafe")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise DeploymentError("Release metadata is invalid") from exc

        if payload.get("release_id") != release_id:
            raise DeploymentError("Release metadata identity mismatch")
        commit = payload.get("commit")
        if (
            not isinstance(commit, str)
            or len(commit) != 40
            or any(char not in "0123456789abcdefABCDEF" for char in commit)
        ):
            raise DeploymentError("Release metadata commit is invalid")
        created_at = payload.get("created_at")
        try:
            created = datetime.fromisoformat(str(created_at))
        except ValueError as exc:
            raise DeploymentError("Release metadata timestamp is invalid") from exc
        if created.tzinfo is None:
            raise DeploymentError("Release metadata timestamp must include a timezone")
        if payload.get("environment") != "staging":
            raise DeploymentError("Release metadata environment is invalid")
        previous = payload.get("previous_release")
        if previous is not None:
            if not isinstance(previous, str):
                raise DeploymentError("Release metadata previous-release value is invalid")
            self._validate_release_id(previous)
        migrations_applied = payload.get("migrations_applied")
        if not isinstance(migrations_applied, bool):
            raise DeploymentError("Release metadata migration state is invalid")
        backup_id = payload.get("pre_migration_backup_id")
        if backup_id is not None and not isinstance(backup_id, str):
            raise DeploymentError("Release metadata backup reference is invalid")

        return {
            "release_id": release_id,
            "commit": commit.lower(),
            "created_at": created.isoformat(),
            "created_at_value": created,
            "previous_release": previous,
            "migrations_applied": migrations_applied,
            "pre_migration_backup_id": backup_id,
        }

    def list_releases(self, project: str, *, limit: int = 100) -> list[dict]:
        if limit < 1 or limit > 500:
            raise DeploymentError("Release list limit must be between 1 and 500")
        config, deployment = self._project(project)
        self._validate_configuration(project, config, deployment)
        release_root, releases = self._prepare_release_root(
            deployment,
            create=False,
        )
        current = self._current_release_id(release_root, releases)
        directories = sorted(
            (
                entry
                for entry in releases.iterdir()
                if entry.is_dir() and not entry.is_symlink()
            ),
            key=lambda entry: entry.name,
            reverse=True,
        )

        result: list[dict] = []
        for rank, entry in enumerate(directories):
            metadata = self._read_release_metadata(releases, entry.name)
            protected = not self.safety.retention.release_is_deletable(
                release_rank_from_newest=rank,
                deployed_at=metadata["created_at_value"],
            )
            is_current = entry.name == current
            rollback_eligible = (
                is_current
                and metadata["previous_release"] is not None
                and not metadata["migrations_applied"]
            )
            result.append(
                {
                    "release_id": metadata["release_id"],
                    "commit": metadata["commit"],
                    "created_at": metadata["created_at"],
                    "previous_release": metadata["previous_release"],
                    "current": is_current,
                    "migrations_applied": metadata["migrations_applied"],
                    "pre_migration_backup_id": metadata["pre_migration_backup_id"],
                    "retention_protected": protected,
                    "rollback_eligible": rollback_eligible,
                }
            )
            if len(result) >= limit:
                break
        return result

    def rollback_plan(self, project: str) -> dict:
        config, deployment = self._project(project)
        self._validate_configuration(project, config, deployment)
        release_root, releases = self._prepare_release_root(
            deployment,
            create=False,
        )
        current = self._current_release_id(release_root, releases)
        if current is None:
            raise DeploymentError("No active release is available for rollback")
        current_metadata = self._read_release_metadata(releases, current)
        target = current_metadata["previous_release"]
        if target is None:
            raise DeploymentError("The active release has no previous release")
        target_metadata = self._read_release_metadata(releases, target)
        blocked = current_metadata["migrations_applied"]
        return {
            "project": project,
            "current_release": current,
            "current_commit": current_metadata["commit"],
            "target_release": target,
            "target_commit": target_metadata["commit"],
            "one_step_only": True,
            "blocked_by_database_migration": blocked,
            "allowed": not blocked,
            "database_restore_performed": False,
        }

    def rollback_one(
        self,
        project: str,
        *,
        expected_current_release: str | None = None,
        expected_target_release: str | None = None,
    ) -> dict:
        self.safety.assert_action_allowed(ActionClass.CODE_ROLLBACK)
        self.safety.assert_code_rollback_steps(1)
        lock = self._lock_for(project)
        if not lock.acquire(blocking=False):
            raise DeploymentError("Another deployment or rollback is already in progress")
        try:
            plan = self.rollback_plan(project)
            if (
                expected_current_release is not None
                and plan["current_release"] != expected_current_release
            ):
                raise DeploymentError("Rollback current release changed after approval")
            if (
                expected_target_release is not None
                and plan["target_release"] != expected_target_release
            ):
                raise DeploymentError("Rollback target changed after approval")
            if not plan["allowed"]:
                raise DeploymentError(
                    "Code rollback is blocked across a database migration boundary"
                )
            _, deployment = self._project(project)
            release_root, releases = self._prepare_release_root(
                deployment,
                create=False,
            )
            current = plan["current_release"]
            target = plan["target_release"]

            self.safety.assert_action_allowed(ActionClass.CODE_ROLLBACK)
            self._activate_release(release_root, releases, target)
            try:
                self.services.action(project, deployment.service, "restart")
            except (ServiceManagerError, OperatorStopActive):
                if self.safety.status().stop_active:
                    return {
                        **plan,
                        "status": "rollback_failed_operator_stop_active",
                        "current_release": target,
                    }
                self._activate_release(release_root, releases, current)
                try:
                    self.services.action(project, deployment.service, "restart")
                except (ServiceManagerError, OperatorStopActive):
                    return {
                        **plan,
                        "status": "rollback_failed_reactivation_restart",
                        "current_release": current,
                    }
                return {
                    **plan,
                    "status": "rollback_failed_reactivated_current",
                    "current_release": current,
                }

            healthy, health = self._wait_healthy(
                project,
                deployment.service,
                timeout_seconds=deployment.activation_timeout_seconds,
            )
            if healthy:
                return {
                    **plan,
                    "status": "rolled_back",
                    "current_release": target,
                    "health": health,
                }

            if self.safety.status().stop_active:
                return {
                    **plan,
                    "status": "rollback_failed_operator_stop_active",
                    "current_release": target,
                    "health": health,
                }

            self._activate_release(release_root, releases, current)
            try:
                self.services.action(project, deployment.service, "restart")
            except (ServiceManagerError, OperatorStopActive):
                return {
                    **plan,
                    "status": "rollback_failed_reactivation_restart",
                    "current_release": current,
                    "health": health,
                }
            recovered, recovered_health = self._wait_healthy(
                project,
                deployment.service,
                timeout_seconds=deployment.activation_timeout_seconds,
            )
            return {
                **plan,
                "status": (
                    "rollback_failed_reactivated_current"
                    if recovered
                    else "rollback_failed_current_unhealthy"
                ),
                "current_release": current,
                "health": recovered_health,
            }
        finally:
            lock.release()

    def deploy(
        self,
        project: str,
        *,
        expected_commit: str | None = None,
    ) -> dict:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        lock = self._lock_for(project)
        if not lock.acquire(blocking=False):
            raise DeploymentError("Another deployment is already in progress")
        try:
            config, deployment = self._project(project)
            self._validate_configuration(project, config, deployment)
            release_root, releases = self._prepare_release_root(
                deployment,
                create=True,
            )
            commit, short_commit = self._source_state(config.root, release_root)
            if expected_commit is not None and commit != expected_commit:
                raise DeploymentError("Deployment commit changed after approval")
            previous_release = self._current_release_id(release_root, releases)

            tests = self._run_required_tests(project, deployment)
            self.safety.assert_action_allowed(ActionClass.DEPLOY)
            post_test_commit, _ = self._source_state(config.root, release_root)
            if post_test_commit != commit:
                raise DeploymentError("Project HEAD changed while deployment tests were running")

            release_id, release_dir = self._create_release(
                config=config,
                release_root=release_root,
                releases=releases,
                commit=commit,
                short_commit=short_commit,
                previous_release=previous_release,
            )

            migrations_applied = False
            backup_id: str | None = None
            migration_result: dict | None = None
            if deployment.run_migrations:
                self.safety.assert_action_allowed(ActionClass.DEPLOY)
                pre_migration_commit, _ = self._source_state(config.root, release_root)
                if pre_migration_commit != commit:
                    raise DeploymentError("Project HEAD changed before migration execution")
                try:
                    migration_result = self.database.apply_migrations(project)
                except DatabaseManagerError as exc:
                    raise DeploymentError(str(exc)) from exc
                if migration_result.get("status") != "applied":
                    return {
                        "project": project,
                        "status": "failed_before_activation",
                        "release_id": release_id,
                        "commit": commit,
                        "tests": tests,
                        "migration": migration_result,
                        "current_release": previous_release,
                        "automatic_code_rollback_performed": False,
                    }
                migrations_applied = True
                backup = migration_result.get("pre_migration_backup") or {}
                backup_id = backup.get("backup_id")
                self._update_release_metadata(
                    release_dir,
                    migrations_applied=True,
                    backup_id=backup_id,
                )

            self.safety.assert_action_allowed(ActionClass.DEPLOY)
            self._activate_release(release_root, releases, release_id)
            try:
                self.services.action(project, deployment.service, "restart")
            except (ServiceManagerError, OperatorStopActive):
                if migrations_applied:
                    return {
                        "project": project,
                        "status": "failed_manual_recovery_required",
                        "release_id": release_id,
                        "commit": commit,
                        "previous_release": previous_release,
                        "tests": tests,
                        "migration": migration_result,
                        "automatic_code_rollback_performed": False,
                        "reason": "service restart failed after database migration",
                    }
                if previous_release is None or self.safety.status().stop_active:
                    return {
                        "project": project,
                        "status": (
                            "failed_operator_stop_active"
                            if self.safety.status().stop_active
                            else "failed_no_previous_release"
                        ),
                        "release_id": release_id,
                        "commit": commit,
                        "previous_release": previous_release,
                        "tests": tests,
                        "automatic_code_rollback_performed": False,
                    }
                self.safety.assert_action_allowed(ActionClass.CODE_ROLLBACK)
                self.safety.assert_code_rollback_steps(1)
                self._activate_release(release_root, releases, previous_release)
                try:
                    self.services.action(project, deployment.service, "restart")
                except (ServiceManagerError, OperatorStopActive):
                    return {
                        "project": project,
                        "status": "failed_rollback_restart",
                        "release_id": release_id,
                        "commit": commit,
                        "previous_release": previous_release,
                        "tests": tests,
                        "automatic_code_rollback_performed": True,
                        "current_release": previous_release,
                    }
                rollback_healthy, rollback_health = self._wait_healthy(
                    project,
                    deployment.service,
                    timeout_seconds=deployment.activation_timeout_seconds,
                )
                return {
                    "project": project,
                    "status": (
                        "failed_rolled_back"
                        if rollback_healthy
                        else "failed_rollback_unhealthy"
                    ),
                    "release_id": release_id,
                    "commit": commit,
                    "previous_release": previous_release,
                    "tests": tests,
                    "health": rollback_health,
                    "automatic_code_rollback_performed": True,
                    "current_release": previous_release,
                }

            healthy, health = self._wait_healthy(
                project,
                deployment.service,
                timeout_seconds=deployment.activation_timeout_seconds,
            )
            if healthy:
                return {
                    "project": project,
                    "status": "deployed",
                    "release_id": release_id,
                    "commit": commit,
                    "previous_release": previous_release,
                    "tests": tests,
                    "migration": migration_result,
                    "health": health,
                    "automatic_code_rollback_performed": False,
                }

            if migrations_applied:
                return {
                    "project": project,
                    "status": "failed_manual_recovery_required",
                    "release_id": release_id,
                    "commit": commit,
                    "previous_release": previous_release,
                    "tests": tests,
                    "migration": migration_result,
                    "health": health,
                    "automatic_code_rollback_performed": False,
                    "reason": "activation health failed after database migration",
                }

            if self.safety.status().stop_active:
                return {
                    "project": project,
                    "status": "failed_operator_stop_active",
                    "release_id": release_id,
                    "commit": commit,
                    "previous_release": previous_release,
                    "tests": tests,
                    "health": health,
                    "automatic_code_rollback_performed": False,
                }

            if previous_release is None:
                return {
                    "project": project,
                    "status": "failed_no_previous_release",
                    "release_id": release_id,
                    "commit": commit,
                    "tests": tests,
                    "health": health,
                    "automatic_code_rollback_performed": False,
                }

            self.safety.assert_action_allowed(ActionClass.CODE_ROLLBACK)
            self.safety.assert_code_rollback_steps(1)
            self._activate_release(release_root, releases, previous_release)
            try:
                self.services.action(project, deployment.service, "restart")
            except (ServiceManagerError, OperatorStopActive):
                return {
                    "project": project,
                    "status": "failed_rollback_restart",
                    "release_id": release_id,
                    "commit": commit,
                    "previous_release": previous_release,
                    "tests": tests,
                    "automatic_code_rollback_performed": True,
                    "current_release": previous_release,
                }

            rollback_healthy, rollback_health = self._wait_healthy(
                project,
                deployment.service,
                timeout_seconds=deployment.activation_timeout_seconds,
            )
            return {
                "project": project,
                "status": (
                    "failed_rolled_back"
                    if rollback_healthy
                    else "failed_rollback_unhealthy"
                ),
                "release_id": release_id,
                "commit": commit,
                "previous_release": previous_release,
                "tests": tests,
                "health": rollback_health,
                "automatic_code_rollback_performed": True,
                "current_release": previous_release,
            }
        finally:
            lock.release()
