import json
import os
import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import (
    DatabaseConfig,
    DeploymentConfig,
    MigrationConfig,
    ProjectConfig,
    ProjectRegistry,
    ServiceConfig,
)
from runner_mcp.config import (
    TestProfile as RunnerTestProfile,
)
from runner_mcp.deployment_manager import DeploymentError, DeploymentManager
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)
from runner_mcp.service_manager import ServiceManagerError


def git(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    git("init", cwd=root)
    git("config", "user.email", "test@example.invalid", cwd=root)
    git("config", "user.name", "Runner MCP Test", cwd=root)
    (root / "app.txt").write_text("v1\n", encoding="utf-8")
    git("add", ".", cwd=root)
    git("commit", "-m", "initial", cwd=root)
    return root


def commit_text(root: Path, text: str, message: str) -> str:
    (root / "app.txt").write_text(text, encoding="utf-8")
    git("add", "app.txt", cwd=root)
    git("commit", "-m", message, cwd=root)
    return git("rev-parse", "HEAD", cwd=root)


def guard(tmp_path: Path, *, stopped: bool = False) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


class FakeServices:
    def __init__(self, *, healthy: bool = True, fail_restart_count: int = 0) -> None:
        self.healthy = healthy
        self.fail_restart_count = fail_restart_count
        self.actions: list[tuple[str, str, str]] = []

    def action(self, project: str, service: str, action: str) -> dict:
        self.actions.append((project, service, action))
        if action == "restart" and self.fail_restart_count > 0:
            self.fail_restart_count -= 1
            raise ServiceManagerError("restart failed")
        return {
            "project": project,
            "service": service,
            "action": action,
            "active_state": "active",
            "health": "healthy" if self.healthy else "unhealthy",
        }

    def status(self, project: str, service: str) -> dict:
        return {
            "project": project,
            "service": service,
            "active_state": "active",
            "sub_state": "running",
            "health": "healthy" if self.healthy else "unhealthy",
        }


class FakeDatabase:
    def __init__(self, *, status: str = "applied") -> None:
        self.backup_root = Path("/virtual/private-backups")
        self.status = status
        self.calls: list[str] = []

    def apply_migrations(self, project: str) -> dict:
        self.calls.append(project)
        return {
            "project": project,
            "status": self.status,
            "exit_code": 0 if self.status == "applied" else 9,
            "pre_migration_backup": {
                "backup_id": "20260920T080000Z-aaaaaaaaaaaa",
                "project": project,
                "kind": "pre_migration",
                "created_at": "2026-09-20T08:00:00+00:00",
                "size_bytes": 123,
                "engine": "postgresql",
                "available": True,
            },
            "database_restore_performed": False,
            "output": "",
            "output_truncated": False,
        }


class FakeTests:
    def __init__(
        self,
        *,
        root: Path | None = None,
        final_status: str = "passed",
        mutate_worktree: bool = False,
    ) -> None:
        self.root = root
        self.final_status = final_status
        self.mutate_worktree = mutate_worktree
        self.started: list[tuple[str, str]] = []

    def start_test(self, project: str, suite: str) -> dict:
        self.started.append((project, suite))
        if self.mutate_worktree and self.root is not None:
            (self.root / "app.txt").write_text("mutated-by-test\n", encoding="utf-8")
        return {"job_id": "a" * 32, "project": project, "suite": suite}

    def status(self, job_id: str) -> dict:
        return {"job_id": job_id, "status": self.final_status}

    def cancel(self, job_id: str) -> dict:
        return {"job_id": job_id, "status": "cancelled"}


def registry(
    root: Path,
    release_root: Path,
    *,
    environment: str = "staging",
    required_tests: list[str] | None = None,
    run_migrations: bool = False,
) -> ProjectRegistry:
    test_profiles = {}
    for name in required_tests or []:
        test_profiles[name] = RunnerTestProfile(
            argv=["/bin/true"],
            timeout_seconds=5,
            max_log_bytes=4096,
        )

    database = None
    if run_migrations:
        database = DatabaseConfig(
            dsn_env="RUNNER_MCP_DB_DEMO",
            migrations=MigrationConfig(
                status_argv=["/bin/true"],
                apply_argv=["/bin/true"],
                dsn_target_env="DATABASE_URL",
            ),
        )

    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment=environment,
                root=root,
                services={
                    "web": ServiceConfig(
                        unit="private-web.service",
                        health_url="http://127.0.0.1:9999/health",
                        allow_restart=True,
                    )
                },
                test_profiles=test_profiles,
                database=database,
                deployment=DeploymentConfig(
                    release_root=release_root,
                    service="web",
                    required_tests=required_tests or [],
                    run_migrations=run_migrations,
                    activation_timeout_seconds=5,
                ),
            )
        }
    )


def manager(
    tmp_path: Path,
    root: Path,
    *,
    environment: str = "staging",
    required_tests: list[str] | None = None,
    run_migrations: bool = False,
    services: FakeServices | None = None,
    tests: FakeTests | None = None,
    database: FakeDatabase | None = None,
    stopped: bool = False,
) -> DeploymentManager:
    release_root = tmp_path / "staging"
    release_root.mkdir(exist_ok=True)
    (release_root / "releases").mkdir(exist_ok=True)
    (release_root / ".runtime-home").mkdir(exist_ok=True)
    release_root.chmod(0o700)
    (release_root / "releases").chmod(0o700)
    (release_root / ".runtime-home").chmod(0o700)
    return DeploymentManager(
        registry=registry(
            root,
            release_root,
            environment=environment,
            required_tests=required_tests,
            run_migrations=run_migrations,
        ),
        safety=guard(tmp_path, stopped=stopped),
        services=services or FakeServices(),
        tests=tests,
        database=database or FakeDatabase(),
        git_path=Path("/usr/bin/git"),
        poll_interval_seconds=0.01,
    )


def current_release(release_root: Path) -> str | None:
    current = release_root / "current"
    if not current.is_symlink():
        return None
    return (release_root / os.readlink(current)).resolve().name


def test_plan_is_staging_only(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root, environment="production")

    with pytest.raises(DeploymentError, match="staging"):
        deployer.plan("demo")


def test_plan_does_not_create_missing_release_root(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    release_root = tmp_path / "missing-release-root"
    deployer = DeploymentManager(
        registry=registry(root, release_root),
        safety=guard(tmp_path),
        services=FakeServices(),
        tests=None,
        database=FakeDatabase(),
        git_path=Path("/usr/bin/git"),
    )

    with pytest.raises(DeploymentError, match="release root"):
        deployer.plan("demo")

    assert not release_root.exists()


def test_dirty_worktree_is_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    (root / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(DeploymentError, match="clean"):
        deployer.deploy("demo")


def test_successful_deploy_creates_immutable_release_and_switches_current(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    services = FakeServices(healthy=True)
    deployer = manager(tmp_path, root, services=services)

    result = deployer.deploy("demo")

    assert result["status"] == "deployed"
    release_root = tmp_path / "staging"
    assert current_release(release_root) == result["release_id"]
    release_dir = release_root / "releases" / result["release_id"]
    assert (release_dir / "app.txt").read_text(encoding="utf-8") == "v1\n"
    metadata = json.loads(
        (release_dir / ".runner-mcp-release.json").read_text(encoding="utf-8")
    )
    assert metadata["commit"] == result["commit"]
    assert metadata["migrations_applied"] is False
    assert services.actions == [("demo", "web", "restart")]


def test_repository_symlink_is_rejected_from_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    target = root / "target.txt"
    target.write_text("target\n", encoding="utf-8")
    (root / "linked.txt").symlink_to(target.name)
    git("add", ".", cwd=root)
    git("commit", "-m", "add symlink", cwd=root)
    deployer = manager(tmp_path, root)

    with pytest.raises(DeploymentError, match="symlinks"):
        deployer.deploy("demo")

    releases = tmp_path / "staging" / "releases"
    assert list(releases.iterdir()) == []


def test_required_test_must_pass_before_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    tests = FakeTests(final_status="failed")
    deployer = manager(
        tmp_path,
        root,
        required_tests=["unit"],
        tests=tests,
    )

    with pytest.raises(DeploymentError, match="did not pass"):
        deployer.deploy("demo")

    assert tests.started == [("demo", "unit")]
    assert list((tmp_path / "staging" / "releases").iterdir()) == []


def test_test_that_mutates_worktree_is_detected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    tests = FakeTests(root=root, mutate_worktree=True)
    deployer = manager(
        tmp_path,
        root,
        required_tests=["unit"],
        tests=tests,
    )

    with pytest.raises(DeploymentError, match="clean"):
        deployer.deploy("demo")

    assert list((tmp_path / "staging" / "releases").iterdir()) == []


def test_health_failure_without_migration_rolls_back_one_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = make_repo(tmp_path)
    services = FakeServices(healthy=True)
    deployer = manager(tmp_path, root, services=services)
    first = deployer.deploy("demo")
    first_id = first["release_id"]

    commit_text(root, "v2\n", "second")
    outcomes = iter(
        [
            (False, {"active_state": "active", "health": "unhealthy"}),
            (True, {"active_state": "active", "health": "healthy"}),
        ]
    )
    monkeypatch.setattr(deployer, "_wait_healthy", lambda *args, **kwargs: next(outcomes))

    result = deployer.deploy("demo")

    assert result["status"] == "failed_rolled_back"
    assert result["automatic_code_rollback_performed"] is True
    assert current_release(tmp_path / "staging") == first_id
    assert len(services.actions) == 3


def test_health_failure_after_migration_never_auto_rolls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = make_repo(tmp_path)
    services = FakeServices(healthy=True)
    database = FakeDatabase(status="applied")
    deployer = manager(
        tmp_path,
        root,
        run_migrations=True,
        services=services,
        database=database,
    )
    monkeypatch.setattr(
        deployer,
        "_wait_healthy",
        lambda *args, **kwargs: (
            False,
            {"active_state": "active", "health": "unhealthy"},
        ),
    )

    result = deployer.deploy("demo")

    assert result["status"] == "failed_manual_recovery_required"
    assert result["automatic_code_rollback_performed"] is False
    assert database.calls == ["demo"]
    assert current_release(tmp_path / "staging") == result["release_id"]


def test_failed_migration_never_activates_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    database = FakeDatabase(status="failed")
    deployer = manager(
        tmp_path,
        root,
        run_migrations=True,
        database=database,
    )

    result = deployer.deploy("demo")

    assert result["status"] == "failed_before_activation"
    assert current_release(tmp_path / "staging") is None
    assert result["migration"]["status"] == "failed"


def test_emergency_stop_blocks_deploy_before_mutation(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root, stopped=True)

    with pytest.raises(OperatorStopActive):
        deployer.deploy("demo")

    assert list((tmp_path / "staging" / "releases").iterdir()) == []


def test_restart_failure_without_migration_reactivates_previous_release(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    stable_services = FakeServices(healthy=True)
    deployer = manager(tmp_path, root, services=stable_services)
    first = deployer.deploy("demo")
    first_id = first["release_id"]

    commit_text(root, "v2\n", "second")
    failing_services = FakeServices(healthy=True, fail_restart_count=1)
    deployer.services = failing_services

    result = deployer.deploy("demo")

    assert result["status"] == "failed_rolled_back"
    assert result["automatic_code_rollback_performed"] is True
    assert current_release(tmp_path / "staging") == first_id
    assert len(failing_services.actions) == 2


def test_restart_failure_after_migration_requires_manual_recovery(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    services = FakeServices(healthy=True, fail_restart_count=1)
    deployer = manager(
        tmp_path,
        root,
        run_migrations=True,
        services=services,
        database=FakeDatabase(status="applied"),
    )

    result = deployer.deploy("demo")

    assert result["status"] == "failed_manual_recovery_required"
    assert result["automatic_code_rollback_performed"] is False


def test_current_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    release_root = tmp_path / "staging"
    outside = tmp_path / "outside"
    outside.mkdir()
    (release_root / "current").symlink_to(outside)

    with pytest.raises(DeploymentError, match="escapes"):
        deployer.plan("demo")


def test_release_list_marks_current_and_one_step_rollback_eligibility(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    first = deployer.deploy("demo")
    commit_text(root, "v2\n", "second")
    second = deployer.deploy("demo")

    releases = deployer.list_releases("demo")

    assert len(releases) == 2
    current = next(item for item in releases if item["current"])
    previous = next(item for item in releases if not item["current"])
    assert current["release_id"] == second["release_id"]
    assert current["previous_release"] == first["release_id"]
    assert current["rollback_eligible"] is True
    assert current["retention_protected"] is True
    assert previous["rollback_eligible"] is False
    assert str(tmp_path) not in repr(releases)


def test_rollback_plan_targets_only_direct_previous_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    first = deployer.deploy("demo")
    commit_text(root, "v2\n", "second")
    second = deployer.deploy("demo")

    plan = deployer.rollback_plan("demo")

    assert plan["current_release"] == second["release_id"]
    assert plan["target_release"] == first["release_id"]
    assert plan["one_step_only"] is True
    assert plan["allowed"] is True
    assert plan["database_restore_performed"] is False


def test_successful_manual_rollback_moves_exactly_one_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    services = FakeServices(healthy=True)
    deployer = manager(tmp_path, root, services=services)
    first = deployer.deploy("demo")
    commit_text(root, "v2\n", "second")
    second = deployer.deploy("demo")

    result = deployer.rollback_one("demo")

    assert result["status"] == "rolled_back"
    assert result["target_release"] == first["release_id"]
    assert result["current_release"] == first["release_id"]
    assert result["current_release"] != second["release_id"]
    assert result["database_restore_performed"] is False
    assert current_release(tmp_path / "staging") == first["release_id"]


def test_rollback_is_blocked_across_database_migration_boundary(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    first_deployer = manager(tmp_path, root)
    first = first_deployer.deploy("demo")

    commit_text(root, "v2\n", "migration release")
    migrated = manager(
        tmp_path,
        root,
        run_migrations=True,
        database=FakeDatabase(status="applied"),
    )
    second = migrated.deploy("demo")
    assert second["status"] == "deployed"

    plan = migrated.rollback_plan("demo")
    assert plan["target_release"] == first["release_id"]
    assert plan["blocked_by_database_migration"] is True
    assert plan["allowed"] is False

    with pytest.raises(DeploymentError, match="database migration boundary"):
        migrated.rollback_one("demo")

    assert current_release(tmp_path / "staging") == second["release_id"]


def test_failed_rollback_health_reactivates_original_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    deployer.deploy("demo")
    commit_text(root, "v2\n", "second")
    second = deployer.deploy("demo")
    outcomes = iter(
        [
            (False, {"active_state": "active", "health": "unhealthy"}),
            (True, {"active_state": "active", "health": "healthy"}),
        ]
    )
    monkeypatch.setattr(deployer, "_wait_healthy", lambda *args, **kwargs: next(outcomes))

    result = deployer.rollback_one("demo")

    assert result["status"] == "rollback_failed_reactivated_current"
    assert result["current_release"] == second["release_id"]
    assert current_release(tmp_path / "staging") == second["release_id"]


def test_rollback_requires_previous_release(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    deployer.deploy("demo")

    with pytest.raises(DeploymentError, match="no previous release"):
        deployer.rollback_plan("demo")


def test_release_metadata_permission_tampering_fails_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    deployer = manager(tmp_path, root)
    deployed = deployer.deploy("demo")
    metadata = (
        tmp_path
        / "staging"
        / "releases"
        / deployed["release_id"]
        / ".runner-mcp-release.json"
    )
    metadata.chmod(0o644)

    with pytest.raises(DeploymentError, match="permissions"):
        deployer.list_releases("demo")
