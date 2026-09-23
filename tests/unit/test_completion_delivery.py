import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp import completion_delivery as completion_delivery_module
from runner_mcp import secure_io as secure_io_module
from runner_mcp.completion_delivery import (
    CompletionDeliveryError,
    CompletionDeliveryLedger,
    CompletionNotifierRuntime,
    GitHubIssueCompletionNotifier,
    GitHubIssueNotificationConfig,
    bootstrap_completion_notifier,
    completion_notifier_status,
    configure_github_issue_notifier,
    load_github_issue_notifier,
    notification_config_path,
    remove_completion_notifier,
    scan_test_completion_events,
)
from runner_mcp.completion_feedback import (
    CompletionOperation,
    CompletionSource,
    CompletionState,
    make_completion_event,
)


class FakeSession:
    def __init__(self) -> None:
        self.comments: list[dict] = []
        self.posts: list[tuple[str, dict]] = []

    def get_json(self, path, *, query=None, allow_not_found=False):
        assert path.endswith("/comments")
        page = int((query or {}).get("page", "1"))
        per_page = int((query or {}).get("per_page", "100"))
        start = (page - 1) * per_page
        return self.comments[start : start + per_page]

    def post_json(self, path, *, payload):
        assert path.endswith("/comments")
        self.posts.append((path, payload))
        record = {"id": len(self.comments) + 1, "body": payload["body"]}
        self.comments.append(record)
        return record


def _config(token: str = "a" * 40) -> GitHubIssueNotificationConfig:
    return GitHubIssueNotificationConfig(
        repository="example/private",
        issue_number=25,
        mention="operator-user",
        token=token,
    )


def _write_job(
    jobs_root: Path,
    *,
    job_id: str,
    status: str,
    finished_at: datetime | None,
    project: str = "demo",
    suite: str = "unit",
) -> None:
    payload = {
        "job_id": job_id,
        "project": project,
        "suite": suite,
        "status": status,
        "created_at": (datetime.now(UTC) - timedelta(seconds=2)).isoformat(),
        "started_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        "finished_at": finished_at.isoformat() if finished_at else None,
        "exit_code": 0 if status == "passed" else None,
        "log_truncated": False,
        "error_category": None,
    }
    path = jobs_root / f"{job_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)


def test_notification_config_is_private_and_round_trips(tmp_path: Path) -> None:
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention="operator-user",
        token="a" * 40,
    )

    path = notification_config_path(tmp_path)
    loaded = load_github_issue_notifier(tmp_path)

    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert loaded.repository == "example/private"
    assert loaded.issue_number == 25
    assert loaded.mention == "operator-user"
    assert loaded.token == "a" * 40
    assert completion_notifier_status(tmp_path) == {
        "configured": True,
        "initialized": False,
    }


def test_notification_config_refuses_symlink_without_touching_referent(
    tmp_path: Path,
) -> None:
    referent = tmp_path / "outside.json"
    referent.write_bytes(b"outside")
    referent.chmod(0o640)
    target = notification_config_path(tmp_path)
    target.symlink_to(referent)

    with pytest.raises(CompletionDeliveryError, match="symlink"):
        configure_github_issue_notifier(
            tmp_path,
            repository="example/private",
            issue_number=25,
            mention=None,
            token="a" * 40,
        )

    assert target.is_symlink()
    assert referent.read_bytes() == b"outside"
    assert oct(referent.stat().st_mode & 0o777) == "0o640"


def test_notification_config_write_failure_is_bounded_and_preserves_previous_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    target = notification_config_path(tmp_path)
    before = target.read_bytes()
    sensitive = str(tmp_path / "private-token-path")

    def fail_fsync(_fd: int) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, "fsync", fail_fsync)

    with pytest.raises(CompletionDeliveryError) as captured:
        configure_github_issue_notifier(
            tmp_path,
            repository="example/private",
            issue_number=26,
            mention=None,
            token="b" * 40,
        )

    assert str(captured.value) == "private completion state could not be written"
    assert sensitive not in str(captured.value)
    assert "b" * 40 not in str(captured.value)
    assert target.read_bytes() == before
    assert load_github_issue_notifier(tmp_path).token == "a" * 40
    assert list(tmp_path.glob(".completion-notifier.json.*.tmp")) == []


def test_notification_config_rejects_broad_permissions(tmp_path: Path) -> None:
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    path = notification_config_path(tmp_path)
    path.chmod(0o644)

    with pytest.raises(CompletionDeliveryError, match="permissions"):
        load_github_issue_notifier(tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository", "https://github.com/example/private"),
        ("issue_number", 0),
        ("mention", "@operator"),
        ("token", "has space"),
    ],
)
def test_notification_config_rejects_unsafe_values(field: str, value) -> None:
    kwargs = {
        "repository": "example/private",
        "issue_number": 25,
        "mention": "operator-user",
        "token": "a" * 40,
    }
    kwargs[field] = value

    with pytest.raises(ValueError):
        GitHubIssueNotificationConfig(**kwargs)


def test_bootstrap_is_destination_bound(tmp_path: Path) -> None:
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    bootstrap_completion_notifier(tmp_path)

    assert completion_notifier_status(tmp_path) == {
        "configured": True,
        "initialized": True,
    }

    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=26,
        mention=None,
        token="a" * 40,
    )
    assert completion_notifier_status(tmp_path) == {
        "configured": True,
        "initialized": False,
    }


def test_remove_config_preserves_private_delivery_state(tmp_path: Path) -> None:
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    ledger = CompletionDeliveryLedger(tmp_path / "completion-notifier-deliveries.json")
    ledger.mark_delivered(destination_id="a" * 32, event_id="b" * 32)

    remove_completion_notifier(tmp_path)

    assert not notification_config_path(tmp_path).exists()
    assert (tmp_path / "completion-notifier-deliveries.json").exists()


def test_scan_terminal_jobs_maps_states_and_ignores_history(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    now = datetime.now(UTC)
    _write_job(
        jobs,
        job_id="1" * 32,
        status="passed",
        finished_at=now,
    )
    _write_job(
        jobs,
        job_id="2" * 32,
        status="cancelled",
        finished_at=now + timedelta(milliseconds=1),
    )
    _write_job(
        jobs,
        job_id="3" * 32,
        status="failed",
        finished_at=now + timedelta(milliseconds=2),
    )
    _write_job(
        jobs,
        job_id="4" * 32,
        status="running",
        finished_at=None,
    )
    _write_job(
        jobs,
        job_id="5" * 32,
        status="passed",
        finished_at=now - timedelta(minutes=1),
    )

    events = scan_test_completion_events(
        jobs,
        since=now - timedelta(seconds=1),
    )

    assert [event.state for event in events] == [
        CompletionState.SUCCEEDED,
        CompletionState.CANCELLED,
        CompletionState.FAILED,
    ]
    assert all(event.source == CompletionSource.TEST_JOB for event in events)
    assert all(event.operation == CompletionOperation.RUN_TESTS for event in events)


def test_scan_rejects_tampered_job_identity(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    _write_job(
        jobs,
        job_id="1" * 32,
        status="passed",
        finished_at=datetime.now(UTC),
    )
    path = jobs / f"{'1' * 32}.json"
    payload = json.loads(path.read_text())
    payload["job_id"] = "2" * 32
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CompletionDeliveryError, match="identity"):
        scan_test_completion_events(
            jobs,
            since=datetime.now(UTC) - timedelta(minutes=1),
        )


def test_delivery_ledger_is_idempotent_and_private(tmp_path: Path) -> None:
    path = tmp_path / "deliveries.json"
    ledger = CompletionDeliveryLedger(path)

    assert not ledger.contains(destination_id="a" * 32, event_id="b" * 32)
    ledger.mark_delivered(destination_id="a" * 32, event_id="b" * 32)
    ledger.mark_delivered(destination_id="a" * 32, event_id="b" * 32)

    assert ledger.contains(destination_id="a" * 32, event_id="b" * 32)
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    raw = json.loads(path.read_text())
    assert len(raw["deliveries"]) == 1


def test_github_issue_notifier_posts_once_and_reconciles_marker() -> None:
    session = FakeSession()
    notifier = GitHubIssueCompletionNotifier(_config(), session=session)
    event = make_completion_event(
        source=CompletionSource.TEST_JOB,
        source_id="a" * 32,
        operation=CompletionOperation.RUN_TESTS,
        project="demo",
        profile="unit",
        state=CompletionState.SUCCEEDED,
    )

    assert notifier.deliver(event) is True
    assert notifier.deliver(event) is False
    assert len(session.posts) == 1
    body = session.posts[0][1]["body"]
    assert "@operator-user" in body
    assert event.event_id in body
    assert "private" not in body.lower()


def test_runtime_delivers_new_terminal_job_once(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention="operator-user",
        token="a" * 40,
    )
    bootstrap_completion_notifier(tmp_path)
    config = load_github_issue_notifier(tmp_path)
    session = FakeSession()
    notifier = GitHubIssueCompletionNotifier(config, session=session)
    runtime = CompletionNotifierRuntime(
        config_dir=tmp_path,
        jobs_root=jobs,
        config=config,
        notifier=notifier,
    )

    _write_job(
        jobs,
        job_id="1" * 32,
        status="passed",
        finished_at=datetime.now(UTC) + timedelta(milliseconds=10),
    )

    first = runtime.run_once()
    second = runtime.run_once()

    assert first.healthy is True
    assert first.discovered_events == 1
    assert first.delivered_events == 1
    assert first.delivery_failures == 0
    assert second.discovered_events == 1
    assert second.already_delivered_events == 1
    assert len(session.posts) == 1


def test_runtime_retries_delivery_failure_without_marking_delivered(
    tmp_path: Path,
) -> None:
    class FailingNotifier:
        def deliver(self, event):
            raise CompletionDeliveryError("offline")

    jobs = tmp_path / "jobs"
    jobs.mkdir()
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    bootstrap_completion_notifier(tmp_path)
    config = load_github_issue_notifier(tmp_path)
    runtime = CompletionNotifierRuntime(
        config_dir=tmp_path,
        jobs_root=jobs,
        config=config,
        notifier=FailingNotifier(),
    )
    _write_job(
        jobs,
        job_id="1" * 32,
        status="failed",
        finished_at=datetime.now(UTC) + timedelta(milliseconds=10),
    )

    outcome = runtime.run_once()

    assert outcome.healthy is False
    assert outcome.delivery_failures == 1
    ledger = CompletionDeliveryLedger(tmp_path / "completion-notifier-deliveries.json")
    event = scan_test_completion_events(
        jobs,
        since=datetime.now(UTC) - timedelta(minutes=1),
    )[0]
    assert not ledger.contains(
        destination_id="0" * 32,
        event_id=event.event_id,
    )


def test_runtime_forever_emits_bounded_healthy_lifecycle_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = tmp_path / "private-repository-secret" / "jobs"
    jobs.mkdir(parents=True)
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention="operator-user",
        token="sensitive-token-value",
    )
    bootstrap_completion_notifier(tmp_path)
    config = load_github_issue_notifier(tmp_path)
    diagnostics: list[str] = []
    runtime = CompletionNotifierRuntime(
        config_dir=tmp_path,
        jobs_root=jobs,
        config=config,
        notifier=GitHubIssueCompletionNotifier(config, session=FakeSession()),
        diagnostic_sink=diagnostics.append,
    )

    monkeypatch.setattr(
        completion_delivery_module,
        "run_restart_if_requested",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        completion_delivery_module.time,
        "sleep",
        lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        runtime.run_forever(poll_seconds=5)

    assert diagnostics == [
        "component=completion_watcher event=lifecycle_started",
        "component=completion_watcher event=cycle_healthy",
        "component=completion_watcher event=lifecycle_stopped",
    ]
    rendered = "\n".join(diagnostics)
    assert "private-repository-secret" not in rendered
    assert "example/private" not in rendered
    assert "operator-user" not in rendered
    assert "sensitive-token-value" not in rendered


def test_runtime_forever_degraded_diagnostic_does_not_echo_delivery_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive = "delivery-private-secret"
    jobs = tmp_path / sensitive / "jobs"
    jobs.mkdir(parents=True)
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    bootstrap_completion_notifier(tmp_path)
    config = load_github_issue_notifier(tmp_path)

    class FailingNotifier:
        def deliver(self, _event):
            raise CompletionDeliveryError(
                f"{sensitive} https://example.invalid/private event={'f' * 32}"
            )

    _write_job(
        jobs,
        job_id="1" * 32,
        status="failed",
        finished_at=datetime.now(UTC) + timedelta(milliseconds=10),
    )
    diagnostics: list[str] = []
    runtime = CompletionNotifierRuntime(
        config_dir=tmp_path,
        jobs_root=jobs,
        config=config,
        notifier=FailingNotifier(),
        diagnostic_sink=diagnostics.append,
    )

    monkeypatch.setattr(
        completion_delivery_module,
        "run_restart_if_requested",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        completion_delivery_module.time,
        "sleep",
        lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        runtime.run_forever(poll_seconds=5)

    assert diagnostics == [
        "component=completion_watcher event=lifecycle_started",
        (
            "component=completion_watcher event=cycle_degraded "
            "error=delivery_failed"
        ),
        "component=completion_watcher event=lifecycle_stopped",
    ]
    rendered = "\n".join(diagnostics)
    assert sensitive not in rendered
    assert "example.invalid" not in rendered
    assert "1" * 32 not in rendered
    assert "f" * 32 not in rendered


def test_runtime_forever_restart_failure_diagnostic_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive = "restart-private-secret"
    jobs = tmp_path / sensitive / "jobs"
    jobs.mkdir(parents=True)
    configure_github_issue_notifier(
        tmp_path,
        repository="example/private",
        issue_number=25,
        mention=None,
        token="a" * 40,
    )
    bootstrap_completion_notifier(tmp_path)
    config = load_github_issue_notifier(tmp_path)
    diagnostics: list[str] = []
    runtime = CompletionNotifierRuntime(
        config_dir=tmp_path,
        jobs_root=jobs,
        config=config,
        notifier=GitHubIssueCompletionNotifier(config, session=FakeSession()),
        diagnostic_sink=diagnostics.append,
    )

    def fail_restart(*_args, **_kwargs):
        raise completion_delivery_module.SelfUpdateError(
            f"{sensitive} {tmp_path} https://example.invalid/private"
        )

    monkeypatch.setattr(
        completion_delivery_module,
        "run_restart_if_requested",
        fail_restart,
    )

    with pytest.raises(CompletionDeliveryError) as captured:
        runtime.run_forever(poll_seconds=5)

    assert str(captured.value) == "Runner MCP self-update restart failed"
    assert sensitive not in str(captured.value)
    assert diagnostics == [
        "component=completion_watcher event=lifecycle_started",
        "component=completion_watcher event=cycle_healthy",
        (
            "component=completion_watcher event=supervisor_restart_failed "
            "error=restart_failed"
        ),
        "component=completion_watcher event=lifecycle_stopped",
    ]
    rendered = "\n".join(diagnostics)
    assert sensitive not in rendered
    assert str(tmp_path) not in rendered
    assert "example.invalid" not in rendered
