from pathlib import Path

import pytest

from runner_mcp.cli import main
from runner_mcp.onboarding import (
    SetupAnswers,
    install_private_configuration,
    load_env_file,
)


def install_config(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"
    paths = install_private_configuration(
        config_dir=config_dir,
        answers=SetupAnswers(
            resource_url="https://mcp.example.invalid/mcp",
            auth_issuer="https://auth.example.invalid/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project_root,
        ),
    )
    return paths, project_root


def test_status_does_not_print_private_paths_or_bearer_value(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    token = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    result = main(["--config-dir", str(paths.config_dir), "status"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Mode: operational" in captured.out
    assert "demo: Demo" in captured.out
    assert str(project_root) not in captured.out
    assert str(paths.config_dir) not in captured.out
    assert token not in captured.out
    assert token not in captured.err


def test_doctor_command_reports_no_failures(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)

    result = main(["--config-dir", str(paths.config_dir), "doctor"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Doctor found no failures" in captured.out


def test_emergency_stop_cli_on_status_and_off(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "on"]
    ) == 0
    capsys.readouterr()

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "status"]
    ) == 0
    status_output = capsys.readouterr()
    assert status_output.out.strip() == "ACTIVE"

    monkeypatch.setattr("builtins.input", lambda _: "UNLOCK")
    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "off"]
    ) == 0
    capsys.readouterr()

    assert main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "status"]
    ) == 0
    final_output = capsys.readouterr()
    assert final_output.out.strip() == "inactive"


def test_emergency_stop_cli_refuses_wrong_unlock_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)
    main(["--config-dir", str(paths.config_dir), "emergency-stop", "on"])
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _: "yes")
    result = main(
        ["--config-dir", str(paths.config_dir), "emergency-stop", "off"]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "UNLOCK" in captured.err
    assert paths.stop_file.exists()


def test_serve_refuses_public_bind_without_explicit_override(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "serve",
            "--host",
            "0.0.0.0",
        ]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "--allow-public-bind" in captured.err


def test_setup_wizard_creates_private_configuration_without_printing_secret(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"

    answers = iter(
        [
            "",
            "demo",
            "Demo",
            "example/demo",
            str(project_root),
            "",
            "",
            "",
            "",
            "",
            "YES",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = main(["--config-dir", str(config_dir), "setup"])
    captured = capsys.readouterr()

    assert result == 0
    env_file = config_dir / "runner-mcp.env"
    assert env_file.exists()
    token = load_env_file(env_file)["RUNNER_MCP_BEARER_TOKEN"]
    assert token not in captured.out
    assert str(config_dir) not in captured.out
    assert "Configuration created successfully" in captured.out


def test_setup_wizard_cancellation_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"

    answers = iter(
        [
            "",
            "demo",
            "Demo",
            "example/demo",
            str(project_root),
            "",
            "",
            "",
            "",
            "",
            "NO",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = main(["--config-dir", str(config_dir), "setup"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Setup cancelled" in captured.out
    assert not (config_dir / "runner-mcp.env").exists()


def test_project_cli_add_and_list_is_path_safe(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)
    second_root = tmp_path / "second"
    second_root.mkdir()

    result = main([
        "--config-dir", str(paths.config_dir),
        "project", "add", "second",
        "--name", "Second",
        "--repository", "example/second",
        "--root", str(second_root),
    ])
    assert result == 0
    capsys.readouterr()

    result = main(["--config-dir", str(paths.config_dir), "project", "list"])
    captured = capsys.readouterr()
    assert result == 0
    assert "second: Second (example/second)" in captured.out
    assert str(second_root) not in captured.out


def test_test_profile_cli_custom_add_and_list_hides_executable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    executable = project_root / "check"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)

    result = main([
        "--config-dir", str(paths.config_dir),
        "test-profile", "add", "demo", "checks",
        "--preset", "custom",
        "--executable", str(executable),
    ])
    assert result == 0
    capsys.readouterr()

    result = main([
        "--config-dir", str(paths.config_dir),
        "test-profile", "list", "demo",
    ])
    captured = capsys.readouterr()
    assert result == 0
    assert "checks: timeout=300s" in captured.out
    assert str(executable) not in captured.out


def test_service_config_cli_hides_private_unit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)

    result = main([
        "--config-dir", str(paths.config_dir),
        "service-config", "add", "demo", "web",
        "--unit", "private-web.service",
        "--allow-restart",
    ])
    assert result == 0
    capsys.readouterr()

    result = main([
        "--config-dir", str(paths.config_dir),
        "service-config", "list", "demo",
    ])
    captured = capsys.readouterr()
    assert result == 0
    assert "web: restart" in captured.out
    assert "private-web.service" not in captured.out


def test_database_config_cli_uses_hidden_prompt_and_does_not_print_secret(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)
    secret = "postgresql://user:hidden-secret@example.invalid/app"
    monkeypatch.setattr("runner_mcp.cli.getpass.getpass", lambda _: secret)

    result = main([
        "--config-dir", str(paths.config_dir),
        "database-config", "add", "demo",
    ])
    captured = capsys.readouterr()

    assert result == 0
    assert secret not in captured.out
    assert secret not in captured.err

    result = main([
        "--config-dir", str(paths.config_dir),
        "database-config", "list",
    ])
    captured = capsys.readouterr()
    assert result == 0
    assert "demo: configured, postgresql" in captured.out
    assert secret not in captured.out


def test_deployment_config_cli_hides_release_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, _ = install_config(tmp_path)
    assert main([
        "--config-dir", str(paths.config_dir),
        "service-config", "add", "demo", "web",
        "--unit", "private-web.service",
        "--health-url", "http://127.0.0.1:9999/health",
        "--allow-restart",
    ]) == 0
    capsys.readouterr()
    release_root = tmp_path / "staging-releases"
    assert main([
        "--config-dir", str(paths.config_dir),
        "deployment-config", "add", "demo",
        "--release-root", str(release_root),
        "--service", "web",
    ]) == 0
    captured = capsys.readouterr()
    assert str(release_root) not in captured.out

    assert main([
        "--config-dir", str(paths.config_dir),
        "deployment-config", "list",
    ]) == 0
    captured = capsys.readouterr()
    assert "demo: configured, service=web" in captured.out
    assert str(release_root) not in captured.out


def test_adapter_cli_lists_and_inspects_without_private_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    assert main(["--config-dir", str(paths.config_dir), "adapter", "list"]) == 0
    listed = capsys.readouterr()
    assert "generic: Generic project" in listed.out
    assert "python: Python project" in listed.out

    assert main(["--config-dir", str(paths.config_dir), "adapter", "inspect", "demo"]) == 0
    inspected = capsys.readouterr()
    assert "Adapter: generic" in inspected.out
    assert str(project_root) not in inspected.out


def test_local_approval_cli_requires_explicit_phrase(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.approval_manager import ApprovalManager

    paths, _ = install_config(tmp_path)
    plan = ApprovalManager(root=paths.approvals_dir).request(
        action="deploy",
        project="demo",
        binding={"commit": "a" * 40},
        summary={"commit": "a" * 40, "environment": "staging"},
    )
    approval_id = plan["approval_id"]

    monkeypatch.setattr("builtins.input", lambda _: "no")
    assert main([
        "--config-dir", str(paths.config_dir),
        "approval", "approve", approval_id,
    ]) == 2
    denied = capsys.readouterr()
    assert "Approval cancelled" in denied.err

    monkeypatch.setattr("builtins.input", lambda _: f"APPROVE {approval_id[:8]}")
    assert main([
        "--config-dir", str(paths.config_dir),
        "approval", "approve", approval_id,
    ]) == 0
    approved = capsys.readouterr()
    assert "single-use" in approved.out
    assert ApprovalManager(root=paths.approvals_dir).status(approval_id)["state"] == "approved"

def test_guide_command_is_path_safe_and_actionable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paths, project_root = install_config(tmp_path)
    token = load_env_file(paths.env_file)["RUNNER_MCP_BEARER_TOKEN"]

    result = main(["--config-dir", str(paths.config_dir), "guide"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Runner MCP guide" in captured.out
    assert "- demo: Demo" in captured.out
    assert "test profiles: not configured" in captured.out
    assert "runner-mcp test-profile add demo" in captured.out
    assert "runner-mcp doctor" in captured.out
    assert str(project_root) not in captured.out
    assert str(paths.config_dir) not in captured.out
    assert token not in captured.out
    assert token not in captured.err


def test_github_mailbox_cli_configure_uses_hidden_token(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)
    token = "example-token-placeholder"
    repository = "example/private-mailbox"
    monkeypatch.setattr("runner_mcp.cli.getpass.getpass", lambda _: token)

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "configure",
            "--repository",
            repository,
        ]
    )
    configured = capsys.readouterr()

    assert result == 0
    assert token not in configured.out
    assert token not in configured.err
    assert repository not in configured.out
    assert "stored privately" in configured.out

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "status",
        ]
    )
    status = capsys.readouterr()
    assert result == 0
    assert status.out.strip() == "configured"
    assert token not in status.out
    assert repository not in status.out


def test_github_mailbox_cli_remove_requires_explicit_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)
    monkeypatch.setattr(
        "runner_mcp.cli.getpass.getpass",
        lambda _: "example-token-placeholder",
    )
    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "configure",
            "--repository",
            "example/private-mailbox",
        ]
    ) == 0
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _: "no")
    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "remove",
        ]
    ) == 2
    denied = capsys.readouterr()
    assert "cancelled" in denied.err.lower()

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "REMOVE GITHUB MAILBOX",
    )
    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "remove",
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-mailbox",
            "status",
        ]
    ) == 0
    status = capsys.readouterr()
    assert status.out.strip() == "not configured"


def test_github_watcher_cli_bootstrap_and_once_are_safe(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.bridge_resilience import WatcherHeartbeat, WatcherState
    from runner_mcp.github_watcher import (
        GitHubWatcherCycleOutcome,
        GitHubWatcherCycleState,
    )

    paths, _ = install_config(tmp_path)

    class FakeRuntime:
        def __init__(self) -> None:
            self.bootstrap_calls = 0
            self.once_calls = 0

        def bootstrap(self) -> None:
            self.bootstrap_calls += 1

        def run_once(self):
            self.once_calls += 1
            return GitHubWatcherCycleOutcome(
                state=GitHubWatcherCycleState.PROCESSED,
                discovered_requests=1,
                processed_requests=1,
                reconciled_requests=0,
                recovery_attention=0,
                heartbeat=WatcherHeartbeat(
                    state=WatcherState.HEALTHY,
                    pending_requests=0,
                    stale_requests=0,
                    recovery_attention=0,
                    oldest_pending_seconds=None,
                ),
                heartbeat_published=True,
            )

    runtime = FakeRuntime()
    monkeypatch.setattr(
        "runner_mcp.cli.GitHubWatcherRuntime.from_private_config",
        lambda _config_dir: runtime,
    )

    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-watcher",
            "bootstrap",
        ]
    ) == 0
    bootstrap = capsys.readouterr()
    assert runtime.bootstrap_calls == 1
    assert "Historical mailbox requests were not replayed." in bootstrap.out
    assert str(paths.config_dir) not in bootstrap.out

    assert main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-watcher",
            "once",
        ]
    ) == 0
    once = capsys.readouterr()
    assert runtime.once_calls == 1
    assert (
        "state=processed discovered=1 processed=1 reconciled=0 attention=0"
        in once.out
    )
    assert str(paths.config_dir) not in once.out


def test_github_watcher_cli_once_returns_nonzero_for_recovery(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.bridge_resilience import WatcherHeartbeat, WatcherState
    from runner_mcp.github_watcher import (
        GitHubWatcherCycleOutcome,
        GitHubWatcherCycleState,
    )

    paths, _ = install_config(tmp_path)

    class FakeRuntime:
        def run_once(self):
            return GitHubWatcherCycleOutcome(
                state=GitHubWatcherCycleState.RECOVERY_REQUIRED,
                discovered_requests=1,
                processed_requests=0,
                reconciled_requests=0,
                recovery_attention=1,
                heartbeat=WatcherHeartbeat(
                    state=WatcherState.DEGRADED,
                    pending_requests=1,
                    stale_requests=0,
                    recovery_attention=1,
                    oldest_pending_seconds=0,
                ),
                heartbeat_published=True,
            )

    monkeypatch.setattr(
        "runner_mcp.cli.GitHubWatcherRuntime.from_private_config",
        lambda _config_dir: FakeRuntime(),
    )

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-watcher",
            "once",
        ]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "state=recovery_required" in captured.out
    assert "attention=1" in captured.out


def test_github_watcher_cli_run_passes_bounded_intervals(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _ = install_config(tmp_path)

    class FakeRuntime:
        def __init__(self) -> None:
            self.args = None

        def run_forever(
            self,
            *,
            poll_seconds: float,
            heartbeat_seconds: float,
        ) -> None:
            self.args = (poll_seconds, heartbeat_seconds)
            raise KeyboardInterrupt

    runtime = FakeRuntime()
    monkeypatch.setattr(
        "runner_mcp.cli.GitHubWatcherRuntime.from_private_config",
        lambda _config_dir: runtime,
    )

    result = main(
        [
            "--config-dir",
            str(paths.config_dir),
            "github-watcher",
            "run",
            "--poll-seconds",
            "7",
            "--heartbeat-seconds",
            "180",
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert runtime.args == (7.0, 180.0)
    assert "running" in captured.out.lower()
    assert "stopped" in captured.out.lower()
