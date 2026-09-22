import pytest

from runner_mcp.server import Settings, transport_security_for


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
    assert settings.rate_limit_per_minute == 600
    assert settings.max_test_jobs == 2
    assert settings.max_queued_tests == 64
    assert settings.mailbox_workers == 4
    assert settings.mailbox_max_inflight == 32


def test_explicit_rate_limit_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_RATE_LIMIT_PER_MINUTE", "1200")

    assert Settings.from_env().rate_limit_per_minute == 1200


@pytest.mark.parametrize("value", ["0", "6001", "not-an-integer"])
def test_invalid_rate_limit_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_RATE_LIMIT_PER_MINUTE", value)

    with pytest.raises(RuntimeError, match="RUNNER_MCP_RATE_LIMIT_PER_MINUTE"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["0", "17", "not-an-integer"])
def test_invalid_max_test_jobs_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_MAX_TEST_JOBS", value)

    with pytest.raises(RuntimeError, match="RUNNER_MCP_MAX_TEST_JOBS"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["0", "1025", "not-an-integer"])
def test_invalid_max_queued_tests_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_MAX_QUEUED_TESTS", value)

    with pytest.raises(RuntimeError, match="RUNNER_MCP_MAX_QUEUED_TESTS"):
        Settings.from_env()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RUNNER_MCP_MAILBOX_WORKERS", "0"),
        ("RUNNER_MCP_MAILBOX_WORKERS", "17"),
        ("RUNNER_MCP_MAILBOX_WORKERS", "bad"),
        ("RUNNER_MCP_MAILBOX_MAX_INFLIGHT", "3"),
        ("RUNNER_MCP_MAILBOX_MAX_INFLIGHT", "257"),
        ("RUNNER_MCP_MAILBOX_MAX_INFLIGHT", "bad"),
    ],
)
def test_invalid_mailbox_capacity_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv(name, value)
    if name == "RUNNER_MCP_MAILBOX_MAX_INFLIGHT":
        monkeypatch.setenv("RUNNER_MCP_MAILBOX_WORKERS", "4")

    with pytest.raises(RuntimeError, match="RUNNER_MCP_MAILBOX"):
        Settings.from_env()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RUNNER_MCP_OPERATOR_STOP_FILE", "relative/stop"),
        ("RUNNER_MCP_TEST_JOBS_ROOT", "relative/jobs"),
        ("RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH", "relative/browsers"),
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


def test_playwright_browser_path_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_env(monkeypatch)
    monkeypatch.delenv("RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH", raising=False)
    assert Settings.from_env().playwright_browsers_path is None


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


@pytest.mark.parametrize("token", ["", "x" * 31])
def test_short_bearer_token_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
    token: str,
) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_BEARER_TOKEN", token)

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        Settings.from_env()


def test_missing_auth_issuer_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_AUTH_ISSUER", "")

    with pytest.raises(RuntimeError, match="issuer and MCP resource URL are required"):
        Settings.from_env()


def test_missing_resource_url_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    required_env(monkeypatch)
    monkeypatch.setenv("RUNNER_MCP_RESOURCE_URL", "")

    with pytest.raises(RuntimeError, match="issuer and MCP resource URL are required"):
        Settings.from_env()


def test_minimal_valid_settings_parse_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirms the happy path still returns a usable Settings object, not just
    that invalid input is rejected."""
    required_env(monkeypatch)

    settings = Settings.from_env()

    assert settings.bearer_token == "x" * 32
    assert settings.auth_issuer == "https://auth.example.invalid/"
    assert settings.resource_url == "https://mcp.example.invalid/mcp"


@pytest.mark.parametrize(
    "resource_url",
    ["not-a-url", "ftp://mcp.example.invalid/mcp", "https:///mcp"],
)
def test_transport_security_rejects_non_http_or_hostless_url(
    resource_url: str,
) -> None:
    with pytest.raises(RuntimeError, match="absolute HTTP\\(S\\) URL"):
        transport_security_for(resource_url)


def test_transport_security_rejects_embedded_credentials() -> None:
    with pytest.raises(RuntimeError, match="must not contain credentials"):
        transport_security_for("https://operator:secret@mcp.example.invalid/mcp")


def test_transport_security_accepts_valid_https_url() -> None:
    result = transport_security_for("https://mcp.example.invalid/mcp")

    assert result.enable_dns_rebinding_protection is True
    assert result.allowed_hosts == ["mcp.example.invalid"]
    assert result.allowed_origins == ["https://mcp.example.invalid"]
