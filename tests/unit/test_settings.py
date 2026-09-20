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
