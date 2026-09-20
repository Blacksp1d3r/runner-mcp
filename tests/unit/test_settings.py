import pytest

from runner_mcp.server import Settings


def required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNNER_MCP_BEARER_TOKEN", "x" * 32)
    monkeypatch.setenv("RUNNER_MCP_AUTH_ISSUER", "https://auth.example.invalid/")
    monkeypatch.setenv("RUNNER_MCP_RESOURCE_URL", "https://mcp.example.invalid/mcp")


def test_runtime_defaults_keep_retention_unconfirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_RETENTION_CONFIRMED", raising=False)
    monkeypatch.delenv("RUNNER_MCP_OPERATOR_STOP_FILE", raising=False)

    settings = Settings.from_env()

    assert settings.retention_confirmed is False
    assert settings.operator_stop_file is None
    assert settings.retention_policy.min_releases_to_keep == 20
    assert settings.retention_policy.min_release_age_days == 90
    assert settings.retention_policy.pitr_retention_days == 30
    assert settings.retention_policy.pre_migration_backup_days == 180


def test_invalid_retention_confirmation_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_RETENTION_CONFIRMED", "yes")

    with pytest.raises(RuntimeError, match="must be true or false"):
        Settings.from_env()


def test_runtime_defaults_keep_test_execution_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_TEST_JOBS_ROOT", raising=False)
    monkeypatch.delenv("RUNNER_MCP_MAX_TEST_JOBS", raising=False)

    settings = Settings.from_env()

    assert settings.test_jobs_root is None
    assert settings.max_test_jobs == 2


@pytest.mark.parametrize("value", ["0", "17", "not-an-integer"])
def test_invalid_max_test_jobs_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_MAX_TEST_JOBS", value)

    with pytest.raises(RuntimeError, match="RUNNER_MCP_MAX_TEST_JOBS"):
        Settings.from_env()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RUNNER_MCP_OPERATOR_STOP_FILE", "relative/stop"),
        ("RUNNER_MCP_TEST_JOBS_ROOT", "relative/jobs"),
    ],
)
def test_operator_paths_must_be_absolute(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match="absolute path"):
        Settings.from_env()


def test_database_backup_root_defaults_to_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_DATABASE_BACKUP_ROOT", raising=False)
    settings = Settings.from_env()
    assert settings.database_backup_root is None


def test_database_backup_root_must_be_absolute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_DATABASE_BACKUP_ROOT", "relative/backups")
    with pytest.raises(RuntimeError, match="DATABASE_BACKUP_ROOT.*absolute"):
        Settings.from_env()


def test_deployment_jobs_root_defaults_to_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_DEPLOY_JOBS_ROOT", raising=False)
    assert Settings.from_env().deployment_jobs_root is None


def test_deployment_jobs_root_must_be_absolute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_DEPLOY_JOBS_ROOT", "relative/deploy-jobs")
    with pytest.raises(RuntimeError, match="DEPLOY_JOBS_ROOT.*absolute"):
        Settings.from_env()


def test_approval_root_defaults_to_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_APPROVAL_ROOT", raising=False)
    monkeypatch.delenv("RUNNER_MCP_APPROVAL_TTL_SECONDS", raising=False)
    settings = Settings.from_env()
    assert settings.approval_root is None
    assert settings.approval_ttl_seconds == 600


def test_approval_root_must_be_absolute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_APPROVAL_ROOT", "relative/approvals")
    with pytest.raises(RuntimeError, match="APPROVAL_ROOT.*absolute"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["59", "1801", "not-an-integer"])
def test_invalid_approval_ttl_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_APPROVAL_TTL_SECONDS", value)
    with pytest.raises(RuntimeError, match="APPROVAL_TTL_SECONDS"):
        Settings.from_env()
