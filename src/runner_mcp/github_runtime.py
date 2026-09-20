from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .bridge_mcp_executor import LocalMCPBridgeExecutor, LocalMCPConfig
from .bridge_replay import BridgeReplayLedger
from .bridge_resilience import serialize_watcher_heartbeat
from .github_mailbox import (
    GitHubApiSession,
    GitHubMailboxConfig,
    GitHubMailboxTransport,
    GitHubMailboxTransportError,
)
from .github_watcher import (
    GitHubMailboxWatcher,
    GitHubWatcherCursorStore,
    GitHubWatcherCycleOutcome,
    GitHubWatcherCycleState,
)
from .onboarding import OnboardingError, load_env_file, read_private_runtime

GITHUB_REPOSITORY_ENV = "RUNNER_MCP_GITHUB_REPOSITORY"
GITHUB_REQUEST_REF_ENV = "RUNNER_MCP_GITHUB_REQUEST_REF"
GITHUB_RESULT_REF_ENV = "RUNNER_MCP_GITHUB_RESULT_REF"
GITHUB_TOKEN_ENV = "RUNNER_MCP_GITHUB_TOKEN"
GITHUB_MAILBOX_ENV_KEYS = frozenset(
    {
        GITHUB_REPOSITORY_ENV,
        GITHUB_REQUEST_REF_ENV,
        GITHUB_RESULT_REF_ENV,
        GITHUB_TOKEN_ENV,
    }
)

DEFAULT_REQUEST_REF = "runner-control"
DEFAULT_RESULT_REF = "runner-results"
DEFAULT_POLL_SECONDS = 5.0
DEFAULT_HEARTBEAT_SECONDS = 300.0


class GitHubWatcherRuntimeError(RuntimeError):
    """Safe runtime bootstrap failure without private configuration values."""


@dataclass(slots=True)
class GitHubWatcherRuntime:
    watcher: GitHubMailboxWatcher
    transport: GitHubMailboxTransport

    @classmethod
    def from_private_config(cls, config_dir: Path) -> GitHubWatcherRuntime:
        try:
            paths, settings, _registry = read_private_runtime(config_dir)
            values = load_env_file(paths.env_file)
        except (OnboardingError, RuntimeError, ValueError) as exc:
            raise GitHubWatcherRuntimeError(
                "Runner MCP private runtime configuration is unavailable"
            ) from exc

        missing = sorted(
            key for key in GITHUB_MAILBOX_ENV_KEYS if not values.get(key, "").strip()
        )
        if missing:
            raise GitHubWatcherRuntimeError(
                "GitHub mailbox private configuration is incomplete"
            )

        try:
            mailbox_config = GitHubMailboxConfig(
                repository=values[GITHUB_REPOSITORY_ENV],
                request_ref=values[GITHUB_REQUEST_REF_ENV],
                result_ref=values[GITHUB_RESULT_REF_ENV],
            )
            github_session = GitHubApiSession(
                token=values[GITHUB_TOKEN_ENV],
            )
            transport = GitHubMailboxTransport(
                config=mailbox_config,
                session=github_session,
            )
            executor = LocalMCPBridgeExecutor(
                LocalMCPConfig(
                    endpoint=settings.resource_url,
                    bearer_token=settings.bearer_token,
                )
            )
        except ValueError as exc:
            raise GitHubWatcherRuntimeError(
                "GitHub mailbox private configuration is invalid"
            ) from exc

        ledger = BridgeReplayLedger(
            paths.config_dir / "github-mailbox-replay.json"
        )
        cursor = GitHubWatcherCursorStore(
            paths.config_dir / "github-mailbox-cursor.json"
        )
        watcher = GitHubMailboxWatcher(
            transport=transport,
            ledger=ledger,
            executor=executor,
            cursor_store=cursor,
        )
        return cls(watcher=watcher, transport=transport)

    def bootstrap(self) -> None:
        self.watcher.bootstrap_cursor_at_current_head()

    def run_once(self) -> GitHubWatcherCycleOutcome:
        return self.watcher.run_cycle(publish_heartbeat=True)

    def run_forever(
        self,
        *,
        poll_seconds: float = DEFAULT_POLL_SECONDS,
        heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS,
    ) -> None:
        _validate_intervals(
            poll_seconds=poll_seconds,
            heartbeat_seconds=heartbeat_seconds,
        )

        next_heartbeat_at = 0.0
        last_published_state: GitHubWatcherCycleState | None = None

        while True:
            now = time.monotonic()
            heartbeat_due = now >= next_heartbeat_at
            outcome = self.watcher.run_cycle(
                publish_heartbeat=heartbeat_due,
            )

            if outcome.state == GitHubWatcherCycleState.UNINITIALIZED:
                raise GitHubWatcherRuntimeError(
                    "GitHub watcher cursor is uninitialized; bootstrap is required"
                )

            if heartbeat_due:
                if outcome.heartbeat_published:
                    last_published_state = outcome.state
                    next_heartbeat_at = now + heartbeat_seconds
                else:
                    next_heartbeat_at = now + poll_seconds
            elif outcome.state != last_published_state:
                try:
                    self.transport.publish_heartbeat(
                        serialize_watcher_heartbeat(outcome.heartbeat)
                    )
                except GitHubMailboxTransportError:
                    pass
                else:
                    last_published_state = outcome.state
                    next_heartbeat_at = now + heartbeat_seconds

            time.sleep(poll_seconds)


def _validate_intervals(
    *,
    poll_seconds: float,
    heartbeat_seconds: float,
) -> None:
    if not 1 <= poll_seconds <= 300:
        raise ValueError("GitHub watcher poll interval must be between 1 and 300 seconds")
    if not 30 <= heartbeat_seconds <= 3_600:
        raise ValueError(
            "GitHub watcher heartbeat interval must be between 30 and 3600 seconds"
        )
    if heartbeat_seconds < poll_seconds:
        raise ValueError(
            "GitHub watcher heartbeat interval must not be shorter than polling"
        )
