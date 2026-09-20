import os
import stat
from pathlib import Path

import pytest

from runner_mcp.onboarding import (
    OnboardingError,
    SetupAnswers,
    install_private_configuration,
    load_env_file,
    read_private_runtime,
    run_doctor,
)


def answers_for(project_root: Path) -> SetupAnswers:
    return SetupAnswers(
        resource_url="https://mcp.example.invalid/mcp",
        auth_issuer="https://auth.example.invalid/",
        project_code="demo",
        project_name="Demo Project",
        repository="example/demo",
        project_root=project_root,
    )


def file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def installed(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "private-config",
        answers=answers_for(project_root),
    )
    return paths, project_root


def test_setup_writes_restrictive_permissions(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)

    assert file_mode(paths.config_dir) == 0o700
    assert file_mode(paths.jobs_dir) == 0o700
    assert file_mode(paths.env_file) == 0o600
    assert file_mode(paths.projects_file) == 0o600


def test_private_runtime_does_not_modify_inherited_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = installed(tmp_path)
    monkeypatch.setenv("RUNNER_MCP_BEARER_TOKEN", "external-test-value")

    _, settings, _ = read_private_runtime(paths.config_dir)

    assert settings.bearer_token != "external-test-value"
    assert os.environ["RUNNER_MCP_BEARER_TOKEN"] == "external-test-value"


def test_runtime_rejects_unsafe_environment_file_mode(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    os.chmod(paths.env_file, 0o644)

    with pytest.raises(OnboardingError, match="permissions are unsafe"):
        read_private_runtime(paths.config_dir)


def test_runtime_rejects_unsafe_project_file_mode(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    os.chmod(paths.projects_file, 0o644)

    with pytest.raises(OnboardingError, match="permissions are unsafe"):
        read_private_runtime(paths.config_dir)


def test_doctor_reports_generated_configuration_healthy(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)

    checks = run_doctor(paths.config_dir)

    assert checks
    assert not [check for check in checks if check.status == "FAIL"]


def test_setup_requires_https_for_non_loopback_resource(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    bad = SetupAnswers(
        resource_url="http://public.example.invalid/mcp",
        auth_issuer="https://auth.example.invalid/",
        project_code="demo",
        project_name="Demo",
        repository="example/demo",
        project_root=project_root,
    )

    with pytest.raises(OnboardingError, match="HTTPS"):
        install_private_configuration(config_dir=tmp_path / "config", answers=bad)


def test_setup_allows_loopback_http(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    local = SetupAnswers(
        resource_url="http://127.0.0.1:8000/mcp",
        auth_issuer="http://127.0.0.1:8000/",
        project_code="demo",
        project_name="Demo",
        repository="example/demo",
        project_root=project_root,
    )

    paths = install_private_configuration(
        config_dir=tmp_path / "config",
        answers=local,
    )

    assert paths.env_file.exists()


def test_setup_refuses_missing_project_root(tmp_path: Path) -> None:
    bad = answers_for(tmp_path / "missing-project")

    with pytest.raises(OnboardingError, match="existing directory"):
        install_private_configuration(config_dir=tmp_path / "config", answers=bad)


def test_setup_does_not_overwrite_without_explicit_flag(tmp_path: Path) -> None:
    paths, project_root = installed(tmp_path)
    original = paths.env_file.read_text(encoding="utf-8")

    with pytest.raises(OnboardingError, match="already exists"):
        install_private_configuration(
            config_dir=paths.config_dir,
            answers=answers_for(project_root),
            overwrite=False,
        )

    assert paths.env_file.read_text(encoding="utf-8") == original


def test_generated_project_config_is_loadable(tmp_path: Path) -> None:
    paths, project_root = installed(tmp_path)

    _, settings, registry = read_private_runtime(paths.config_dir)

    assert settings.projects_config == paths.projects_file
    assert registry.projects["demo"].root == project_root


def test_overwrite_preserves_existing_bearer_credential_by_default(tmp_path: Path) -> None:
    paths, project_root = installed(tmp_path)
    before = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    install_private_configuration(
        config_dir=paths.config_dir,
        answers=answers_for(project_root),
        overwrite=True,
    )
    after = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    assert after == before


def test_explicit_rotation_replaces_bearer_credential(tmp_path: Path) -> None:
    paths, project_root = installed(tmp_path)
    before = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    install_private_configuration(
        config_dir=paths.config_dir,
        answers=answers_for(project_root),
        overwrite=True,
        rotate_token=True,
    )
    after = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    assert after != before


def test_generated_database_backup_directory_is_private(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    assert file_mode(paths.database_backups_dir) == 0o700


def test_setup_overwrite_preserves_private_database_secret(tmp_path: Path) -> None:
    from runner_mcp.config_manager import add_database_config

    paths, project_root = installed(tmp_path)
    secret = "postgresql://user:private-value@example.invalid/app"
    add_database_config(paths.config_dir, project="demo", dsn=secret)

    install_private_configuration(
        config_dir=paths.config_dir,
        answers=answers_for(project_root),
        overwrite=True,
    )

    values = load_env_file(paths.env_file)
    assert secret in values.values()


def test_generated_deployment_job_directory_is_private(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    assert file_mode(paths.deployment_jobs_dir) == 0o700


def test_generated_approval_directory_is_private(tmp_path: Path) -> None:
    paths, _ = installed(tmp_path)
    assert file_mode(paths.approvals_dir) == 0o700


def test_setup_overwrite_preserves_github_mailbox_values(tmp_path: Path) -> None:
    from runner_mcp.config_manager import configure_github_mailbox
    from runner_mcp.github_mailbox import GITHUB_MAILBOX_ENV_KEYS

    paths, project_root = installed(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="private-mailbox-token-value-1234567890",
    )
    before = load_env_file(paths.env_file)
    expected = {key: before[key] for key in GITHUB_MAILBOX_ENV_KEYS}

    install_private_configuration(
        config_dir=paths.config_dir,
        answers=answers_for(project_root),
        overwrite=True,
    )

    after = load_env_file(paths.env_file)
    assert {key: after[key] for key in GITHUB_MAILBOX_ENV_KEYS} == expected


def test_setup_token_rotation_preserves_github_mailbox_and_database_secrets(
    tmp_path: Path,
) -> None:
    from runner_mcp.config_manager import add_database_config, configure_github_mailbox
    from runner_mcp.github_mailbox import GITHUB_MAILBOX_ENV_KEYS

    paths, project_root = installed(tmp_path)
    database_secret = "postgresql://user:private-value@example.invalid/app"
    add_database_config(
        paths.config_dir,
        project="demo",
        dsn=database_secret,
    )
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="private-mailbox-token-value-1234567890",
    )
    before = load_env_file(paths.env_file)
    old_bearer = before["RUNNER_MCP_BEARER_TOKEN"]
    mailbox_values = {key: before[key] for key in GITHUB_MAILBOX_ENV_KEYS}

    install_private_configuration(
        config_dir=paths.config_dir,
        answers=answers_for(project_root),
        overwrite=True,
        rotate_token=True,
    )

    after = load_env_file(paths.env_file)
    assert after["RUNNER_MCP_BEARER_TOKEN"] != old_bearer
    assert database_secret in after.values()
    assert {key: after[key] for key in GITHUB_MAILBOX_ENV_KEYS} == mailbox_values
