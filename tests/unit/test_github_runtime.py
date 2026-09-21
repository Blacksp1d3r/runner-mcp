from pathlib import Path

import pytest

from runner_mcp.bridge_protocol import BridgeAction
from runner_mcp.bridge_replay import ReplayState
from runner_mcp.bridge_resilience import WatcherHeartbeat, WatcherState
from runner_mcp.config_manager import configure_github_mailbox
from runner_mcp.github_runtime import (
    GitHubWatcherRuntime,
    GitHubWatcherRuntimeError,
    _validate_intervals,
)
from runner_mcp.github_watcher import (
    GitHubRecoveryResolution,
    GitHubWatcherCycleOutcome,
    GitHubWatcherCycleState,
)
from runner_mcp.onboarding import (
    SetupAnswers,
    install_private_configuration,
)


class FakeWatcher:
    def __init__(self, outcomes: list[GitHubWatcherCycleOutcome]) -> None:
        self.outcomes = list(outcomes)
        self.publish_flags: list[bool] = []
        self.bootstrap_calls = 0
        self.resolve_calls: list[str] = []

    def bootstrap_cursor_at_current_head(self) -> None:
        self.bootstrap_calls += 1

    def resolve_missing_result_fail_closed(
        self,
        request_id: str,
    ) -> GitHubRecoveryResolution:
        self.resolve_calls.append(request_id)
        return GitHubRecoveryResolution(
            request_id=request_id,
            action=BridgeAction.SYNC_PROJECT,
            prior_state=ReplayState.CLAIMED,
        )

    def run_cycle(
        self,
        *,
        publish_heartbeat: bool = True,
    ) -> GitHubWatcherCycleOutcome:
        self.publish_flags.append(publish_heartbeat)
        if not self.outcomes:
            raise AssertionError("unexpected watcher cycle")
        return self.outcomes.pop(0)


class FakeTransport:
    def __init__(self) -> None:
        self.heartbeats: list[str] = []

    def publish_heartbeat(self, heartbeat_json: str) -> None:
        self.heartbeats.append(heartbeat_json)


def _healthy_outcome(
    *,
    state: GitHubWatcherCycleState = GitHubWatcherCycleState.IDLE,
    heartbeat_published: bool = False,
) -> GitHubWatcherCycleOutcome:
    return GitHubWatcherCycleOutcome(
        state=state,
        discovered_requests=0,
        processed_requests=(
            1 if state == GitHubWatcherCycleState.PROCESSED else 0
        ),
        reconciled_requests=0,
        recovery_attention=0,
        heartbeat=WatcherHeartbeat(
            state=WatcherState.HEALTHY,
            pending_requests=0,
            stale_requests=0,
            recovery_attention=0,
            oldest_pending_seconds=None,
        ),
        heartbeat_published=heartbeat_published,
    )


def _recovery_outcome() -> GitHubWatcherCycleOutcome:
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
        heartbeat_published=False,
    )


def _private_config(
    tmp_path: Path,
    *,
    resource_url: str = "http://127.0.0.1:8000/mcp",
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "config",
        answers=SetupAnswers(
            resource_url=resource_url,
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project_root,
        ),
    )
    return paths


def test_runtime_requires_complete_private_github_config(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)

    with pytest.raises(
        GitHubWatcherRuntimeError,
        match="configuration is incomplete",
    ):
        GitHubWatcherRuntime.from_private_config(paths.config_dir)


def test_runtime_builds_from_private_config_without_network(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="example-token-placeholder",
    )

    runtime = GitHubWatcherRuntime.from_private_config(paths.config_dir)

    assert runtime.watcher._cursor_store._path == (
        paths.config_dir / "github-mailbox-cursor.json"
    )
    assert runtime.watcher._ledger._path == (
        paths.config_dir / "github-mailbox-replay.json"
    )
    assert runtime.transport._config.repository == "example/private-mailbox"
    assert runtime.transport._config.request_ref == "runner-control"
    assert runtime.transport._config.result_ref == "runner-results"


def test_runtime_rejects_non_loopback_runner_endpoint_safely(
    tmp_path: Path,
) -> None:
    paths = _private_config(
        tmp_path,
        resource_url="https://mcp.example.invalid/mcp",
    )
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="example-token-placeholder",
    )

    with pytest.raises(
        GitHubWatcherRuntimeError,
        match="private configuration is invalid",
    ) as caught:
        GitHubWatcherRuntime.from_private_config(paths.config_dir)

    assert "mcp.example.invalid" not in str(caught.value)


def test_runtime_bootstrap_delegates_once() -> None:
    watcher = FakeWatcher([])
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=FakeTransport(),  # type: ignore[arg-type]
    )

    runtime.bootstrap()

    assert watcher.bootstrap_calls == 1


def test_runtime_delegates_fail_closed_recovery() -> None:
    watcher = FakeWatcher([])
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=FakeTransport(),  # type: ignore[arg-type]
    )

    resolution = runtime.resolve_missing_result_fail_closed("req-recovery-1")

    assert watcher.resolve_calls == ["req-recovery-1"]
    assert resolution.request_id == "req-recovery-1"
    assert resolution.action == BridgeAction.SYNC_PROJECT
    assert resolution.prior_state == ReplayState.CLAIMED


def test_runtime_once_requests_heartbeat() -> None:
    watcher = FakeWatcher([_healthy_outcome(heartbeat_published=True)])
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=FakeTransport(),  # type: ignore[arg-type]
    )

    outcome = runtime.run_once()

    assert outcome.state == GitHubWatcherCycleState.IDLE
    assert watcher.publish_flags == [True]


@pytest.mark.parametrize(
    ("poll_seconds", "heartbeat_seconds"),
    [
        (0.5, 300),
        (301, 300),
        (5, 29),
        (5, 3601),
        (60, 30),
    ],
)
def test_runtime_rejects_unsafe_intervals(
    poll_seconds: float,
    heartbeat_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        _validate_intervals(
            poll_seconds=poll_seconds,
            heartbeat_seconds=heartbeat_seconds,
        )


def test_runtime_requires_bootstrap_before_continuous_run() -> None:
    watcher = FakeWatcher(
        [
            GitHubWatcherCycleOutcome(
                state=GitHubWatcherCycleState.UNINITIALIZED,
                discovered_requests=0,
                processed_requests=0,
                reconciled_requests=0,
                recovery_attention=0,
                heartbeat=WatcherHeartbeat(
                    state=WatcherState.DEGRADED,
                    pending_requests=0,
                    stale_requests=0,
                    recovery_attention=0,
                    oldest_pending_seconds=None,
                ),
                heartbeat_published=True,
            )
        ]
    )
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=FakeTransport(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        GitHubWatcherRuntimeError,
        match="bootstrap is required",
    ):
        runtime.run_forever(poll_seconds=5, heartbeat_seconds=300)


def test_runtime_separates_polling_and_periodic_heartbeat(
    monkeypatch,
) -> None:
    watcher = FakeWatcher(
        [
            _healthy_outcome(heartbeat_published=True),
            _healthy_outcome(),
            _healthy_outcome(),
        ]
    )
    transport = FakeTransport()
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=transport,  # type: ignore[arg-type]
    )
    monotonic_values = iter([0.0, 5.0, 10.0])
    sleeps = 0

    def fake_sleep(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        "runner_mcp.github_runtime.time.monotonic",
        lambda: next(monotonic_values),
    )
    monkeypatch.setattr(
        "runner_mcp.github_runtime.time.sleep",
        fake_sleep,
    )

    with pytest.raises(KeyboardInterrupt):
        runtime.run_forever(
            poll_seconds=5,
            heartbeat_seconds=300,
        )

    assert watcher.publish_flags == [True, False, False]
    assert transport.heartbeats == []


def test_runtime_publishes_heartbeat_immediately_on_state_change(
    monkeypatch,
) -> None:
    watcher = FakeWatcher(
        [
            _healthy_outcome(heartbeat_published=True),
            _healthy_outcome(),
            _recovery_outcome(),
        ]
    )
    transport = FakeTransport()
    runtime = GitHubWatcherRuntime(
        watcher=watcher,  # type: ignore[arg-type]
        transport=transport,  # type: ignore[arg-type]
    )
    monotonic_values = iter([0.0, 5.0, 10.0])
    sleeps = 0

    def fake_sleep(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        "runner_mcp.github_runtime.time.monotonic",
        lambda: next(monotonic_values),
    )
    monkeypatch.setattr(
        "runner_mcp.github_runtime.time.sleep",
        fake_sleep,
    )

    with pytest.raises(KeyboardInterrupt):
        runtime.run_forever(
            poll_seconds=5,
            heartbeat_seconds=300,
        )

    assert watcher.publish_flags == [True, False, False]
    assert len(transport.heartbeats) == 1
    assert '"state":"degraded"' in transport.heartbeats[0]
