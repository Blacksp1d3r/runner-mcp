from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .completion_feedback import (
    COMPLETION_IDENTIFIER_RE,
    CompletionEvent,
    CompletionOperation,
    CompletionSource,
    CompletionState,
    completion_notification_marker,
    make_completion_event,
)
from .github_mailbox import GitHubApiSession
from .onboarding import read_private_runtime
from .safe_diagnostics import (
    DiagnosticComponent,
    DiagnosticErrorCategory,
    DiagnosticEvent,
    render_safe_diagnostic,
)
from .secure_io import PrivateAtomicWriteError, atomic_replace_private
from .self_update import (
    SelfUpdateError,
    reexec_component,
    run_restart_if_requested,
)
from .test_runner import JOB_ID_RE, TERMINAL_STATUSES, TestJobStatus

MAX_NOTIFICATION_CONFIG_BYTES = 8_192
MAX_NOTIFICATION_STATE_BYTES = 1_048_576
MAX_NOTIFICATION_DELIVERIES = 5_000
MAX_JOB_METADATA_BYTES = 65_536
MAX_JOB_METADATA_FILES = 10_000
MAX_COMMENT_PAGES = 20
_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}/"
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}$"
)
_GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


class CompletionDeliveryError(RuntimeError):
    """Safe completion-delivery failure without private response details."""


@dataclass(frozen=True, slots=True)
class GitHubIssueNotificationConfig:
    repository: str
    issue_number: int
    mention: str | None
    token: str

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("notification repository must use a safe owner/name shape")
        if not 1 <= self.issue_number <= 2_147_483_647:
            raise ValueError("notification issue number is outside the supported range")
        if self.mention is not None and not _GITHUB_LOGIN_RE.fullmatch(self.mention):
            raise ValueError("notification mention has an unsafe GitHub login shape")
        if not self.token or len(self.token) > 4_096:
            raise ValueError("notification GitHub token is missing or unreasonably large")
        if not self.token.isascii():
            raise ValueError("notification GitHub token must use ASCII characters")
        if any(ord(char) < 33 or ord(char) == 127 for char in self.token):
            raise ValueError("notification GitHub token contains unsupported characters")


@dataclass(frozen=True, slots=True)
class CompletionNotifierCycleOutcome:
    discovered_events: int
    delivered_events: int
    reconciled_events: int
    already_delivered_events: int
    delivery_failures: int

    @property
    def healthy(self) -> bool:
        return self.delivery_failures == 0


def notification_config_path(config_dir: Path) -> Path:
    return config_dir.expanduser().resolve() / "completion-notifier.json"


def notification_bootstrap_path(config_dir: Path) -> Path:
    return config_dir.expanduser().resolve() / "completion-notifier-bootstrap.json"


def notification_ledger_path(config_dir: Path) -> Path:
    return config_dir.expanduser().resolve() / "completion-notifier-deliveries.json"


def _destination_id(config: GitHubIssueNotificationConfig) -> str:
    canonical = f"github-issue:v1:{config.repository}:{config.issue_number}".encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CompletionDeliveryError("private completion state contains duplicate keys")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise CompletionDeliveryError(
        f"private completion state contains non-standard JSON constant: {value}"
    )


def _strict_json(raw: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except CompletionDeliveryError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise CompletionDeliveryError("private completion state is invalid JSON") from exc


def _check_private_file(path: Path, *, max_bytes: int) -> None:
    if path.is_symlink():
        raise CompletionDeliveryError("private completion state must not be a symlink")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise CompletionDeliveryError("private completion state is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise CompletionDeliveryError("private completion state must be a regular file")
    if metadata.st_mode & 0o077:
        raise CompletionDeliveryError("private completion state permissions are too broad")
    if metadata.st_size > max_bytes:
        raise CompletionDeliveryError("private completion state exceeds size limit")


def _atomic_private_json(path: Path, payload: dict[str, Any], *, max_bytes: int) -> None:
    if path.is_symlink():
        raise CompletionDeliveryError("private completion state must not be a symlink")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CompletionDeliveryError("private completion state could not be written") from exc
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > max_bytes:
        raise CompletionDeliveryError("private completion state exceeds size limit")
    try:
        atomic_replace_private(path, encoded)
    except PrivateAtomicWriteError as exc:
        raise CompletionDeliveryError("private completion state could not be written") from exc


def configure_github_issue_notifier(
    config_dir: Path,
    *,
    repository: str,
    issue_number: int,
    mention: str | None,
    token: str,
) -> None:
    config = GitHubIssueNotificationConfig(
        repository=repository,
        issue_number=issue_number,
        mention=mention,
        token=token,
    )
    _atomic_private_json(
        notification_config_path(config_dir),
        {
            "version": 1,
            "repository": config.repository,
            "issue_number": config.issue_number,
            "mention": config.mention,
            "token": config.token,
        },
        max_bytes=MAX_NOTIFICATION_CONFIG_BYTES,
    )


def load_github_issue_notifier(config_dir: Path) -> GitHubIssueNotificationConfig:
    path = notification_config_path(config_dir)
    if not path.exists():
        raise CompletionDeliveryError("completion notifier is not configured")
    _check_private_file(path, max_bytes=MAX_NOTIFICATION_CONFIG_BYTES)
    try:
        raw = _strict_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CompletionDeliveryError("completion notifier configuration is unavailable") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "version",
        "repository",
        "issue_number",
        "mention",
        "token",
    }:
        raise CompletionDeliveryError("completion notifier configuration is invalid")
    if raw["version"] != 1:
        raise CompletionDeliveryError("completion notifier configuration version is unsupported")
    try:
        return GitHubIssueNotificationConfig(
            repository=raw["repository"],
            issue_number=raw["issue_number"],
            mention=raw["mention"],
            token=raw["token"],
        )
    except (TypeError, ValueError) as exc:
        raise CompletionDeliveryError("completion notifier configuration is invalid") from exc


def completion_notifier_status(config_dir: Path) -> dict[str, bool]:
    config_path = notification_config_path(config_dir)
    configured = config_path.exists()
    initialized = False
    if configured:
        config = load_github_issue_notifier(config_dir)
        bootstrap = _load_bootstrap(config_dir, required=False)
        initialized = (
            bootstrap is not None
            and bootstrap["destination_id"] == _destination_id(config)
        )
    return {"configured": configured, "initialized": initialized}


def remove_completion_notifier(config_dir: Path) -> None:
    path = notification_config_path(config_dir)
    if path.exists() and path.is_symlink():
        raise CompletionDeliveryError("completion notifier configuration must not be a symlink")
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise CompletionDeliveryError("completion notifier configuration could not be removed") from exc


def bootstrap_completion_notifier(config_dir: Path) -> None:
    config = load_github_issue_notifier(config_dir)
    _atomic_private_json(
        notification_bootstrap_path(config_dir),
        {
            "version": 1,
            "destination_id": _destination_id(config),
            "started_at": datetime.now(UTC).isoformat(),
        },
        max_bytes=MAX_NOTIFICATION_CONFIG_BYTES,
    )


def _load_bootstrap(
    config_dir: Path,
    *,
    required: bool = True,
) -> dict[str, str] | None:
    path = notification_bootstrap_path(config_dir)
    if not path.exists():
        if required:
            raise CompletionDeliveryError(
                "completion notifier is not initialized; run bootstrap first"
            )
        return None
    _check_private_file(path, max_bytes=MAX_NOTIFICATION_CONFIG_BYTES)
    try:
        raw = _strict_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CompletionDeliveryError("completion notifier bootstrap state is unavailable") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "version",
        "destination_id",
        "started_at",
    }:
        raise CompletionDeliveryError("completion notifier bootstrap state is invalid")
    if raw["version"] != 1:
        raise CompletionDeliveryError("completion notifier bootstrap version is unsupported")
    destination_id = raw["destination_id"]
    started_at = raw["started_at"]
    if not isinstance(destination_id, str) or not re.fullmatch(r"[0-9a-f]{32}", destination_id):
        raise CompletionDeliveryError("completion notifier bootstrap destination is invalid")
    if not isinstance(started_at, str):
        raise CompletionDeliveryError("completion notifier bootstrap time is invalid")
    try:
        parsed = datetime.fromisoformat(started_at)
    except ValueError as exc:
        raise CompletionDeliveryError("completion notifier bootstrap time is invalid") from exc
    if parsed.tzinfo is None:
        raise CompletionDeliveryError("completion notifier bootstrap time must be timezone-aware")
    return {"destination_id": destination_id, "started_at": parsed.astimezone(UTC).isoformat()}


class CompletionDeliveryLedger:
    def __init__(self, path: Path) -> None:
        self._path = path

    def contains(self, *, destination_id: str, event_id: str) -> bool:
        key = self._key(destination_id, event_id)
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
                return key in self._load(handle)["deliveries"]
        except OSError as exc:
            raise CompletionDeliveryError("completion delivery ledger read failed") from exc

    def mark_delivered(self, *, destination_id: str, event_id: str) -> None:
        key = self._key(destination_id, event_id)
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                payload = self._load(handle)
                deliveries = payload["deliveries"]
                if key in deliveries:
                    return
                if len(deliveries) >= MAX_NOTIFICATION_DELIVERIES:
                    raise CompletionDeliveryError("completion delivery ledger capacity reached")
                deliveries[key] = datetime.now(UTC).isoformat()
                self._store(handle, payload)
        except OSError as exc:
            raise CompletionDeliveryError("completion delivery ledger write failed") from exc

    @staticmethod
    def _key(destination_id: str, event_id: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{32}", destination_id):
            raise CompletionDeliveryError("completion destination id is invalid")
        if not re.fullmatch(r"[0-9a-f]{32}", event_id):
            raise CompletionDeliveryError("completion event id is invalid")
        return f"{destination_id}:{event_id}"

    def _open(self) -> int:
        parent = self._path.parent
        if not parent.exists() or not parent.is_dir():
            raise CompletionDeliveryError("completion delivery ledger parent is unavailable")
        try:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self._path, flags, 0o600)
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                os.close(fd)
                raise CompletionDeliveryError(
                    "completion delivery ledger must be a regular file"
                )
            os.fchmod(fd, 0o600)
            return fd
        except OSError as exc:
            raise CompletionDeliveryError("completion delivery ledger could not be opened") from exc

    def _load(self, handle: Any) -> dict[str, Any]:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size > MAX_NOTIFICATION_STATE_BYTES:
            raise CompletionDeliveryError("completion delivery ledger exceeds size limit")
        handle.seek(0)
        text = handle.read()
        if not text:
            return {"version": 1, "deliveries": {}}
        raw = _strict_json(text)
        if not isinstance(raw, dict) or set(raw) != {"version", "deliveries"}:
            raise CompletionDeliveryError("completion delivery ledger is invalid")
        if raw["version"] != 1 or not isinstance(raw["deliveries"], dict):
            raise CompletionDeliveryError("completion delivery ledger is invalid")
        if len(raw["deliveries"]) > MAX_NOTIFICATION_DELIVERIES:
            raise CompletionDeliveryError("completion delivery ledger capacity exceeded")
        for key, value in raw["deliveries"].items():
            if not isinstance(key, str) or not re.fullmatch(
                r"[0-9a-f]{32}:[0-9a-f]{32}", key
            ):
                raise CompletionDeliveryError("completion delivery ledger key is invalid")
            if not isinstance(value, str):
                raise CompletionDeliveryError("completion delivery ledger timestamp is invalid")
        return raw

    def _store(self, handle: Any, payload: dict[str, Any]) -> None:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_NOTIFICATION_STATE_BYTES:
            raise CompletionDeliveryError("completion delivery ledger exceeds size limit")
        handle.seek(0)
        handle.truncate()
        handle.write(encoded.decode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


def _parse_finished_at(value: Any) -> datetime:
    if not isinstance(value, str):
        raise CompletionDeliveryError("test completion metadata has no terminal timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CompletionDeliveryError("test completion metadata timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise CompletionDeliveryError("test completion metadata timestamp must be timezone-aware")
    return parsed.astimezone(UTC)


def _completion_state(status: TestJobStatus) -> CompletionState:
    if status == TestJobStatus.PASSED:
        return CompletionState.SUCCEEDED
    if status == TestJobStatus.CANCELLED:
        return CompletionState.CANCELLED
    if status in TERMINAL_STATUSES:
        return CompletionState.FAILED
    raise CompletionDeliveryError("test job has not reached a terminal state")


def scan_test_completion_events(
    jobs_root: Path,
    *,
    since: datetime,
) -> list[CompletionEvent]:
    if since.tzinfo is None:
        raise ValueError("completion scan start must be timezone-aware")
    if jobs_root.is_symlink() or not jobs_root.is_dir():
        raise CompletionDeliveryError("test job storage is unavailable")
    paths = list(jobs_root.glob("*.json"))
    if len(paths) > MAX_JOB_METADATA_FILES:
        raise CompletionDeliveryError("test job metadata count exceeds notification limit")

    found: list[tuple[datetime, CompletionEvent]] = []
    allowed_fields = {
        "job_id",
        "project",
        "suite",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "exit_code",
        "log_truncated",
        "error_category",
    }
    for path in paths:
        if path.is_symlink():
            raise CompletionDeliveryError("test job metadata must not be a symlink")
        try:
            metadata = path.stat()
        except OSError as exc:
            raise CompletionDeliveryError("test job metadata is unavailable") from exc
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_JOB_METADATA_BYTES:
            raise CompletionDeliveryError("test job metadata is invalid")
        try:
            raw = _strict_json(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CompletionDeliveryError("test job metadata is unreadable") from exc
        if not isinstance(raw, dict) or set(raw) != allowed_fields:
            raise CompletionDeliveryError("test job metadata has an unsupported shape")

        job_id = raw["job_id"]
        project = raw["project"]
        suite = raw["suite"]
        if not isinstance(job_id, str) or not JOB_ID_RE.fullmatch(job_id) or path.stem != job_id:
            raise CompletionDeliveryError("test job metadata identity is invalid")
        if not isinstance(project, str) or not COMPLETION_IDENTIFIER_RE.fullmatch(project):
            raise CompletionDeliveryError("test job project identifier is unsafe")
        if not isinstance(suite, str) or not COMPLETION_IDENTIFIER_RE.fullmatch(suite):
            raise CompletionDeliveryError("test job profile identifier is unsafe")
        try:
            status = TestJobStatus(raw["status"])
        except (TypeError, ValueError) as exc:
            raise CompletionDeliveryError("test job status is invalid") from exc
        if status not in TERMINAL_STATUSES:
            continue

        finished_at = _parse_finished_at(raw["finished_at"])
        if finished_at < since.astimezone(UTC):
            continue
        event = make_completion_event(
            source=CompletionSource.TEST_JOB,
            source_id=job_id,
            operation=CompletionOperation.RUN_TESTS,
            project=project,
            profile=suite,
            state=_completion_state(status),
        )
        found.append((finished_at, event))

    found.sort(key=lambda item: (item[0], item[1].event_id))
    return [event for _, event in found]


class GitHubIssueCompletionNotifier:
    def __init__(
        self,
        config: GitHubIssueNotificationConfig,
        *,
        session: GitHubApiSession | None = None,
    ) -> None:
        self._config = config
        self._session = session or GitHubApiSession(token=config.token)

    def deliver(self, event: CompletionEvent) -> bool:
        marker = completion_notification_marker(event)
        if self._marker_exists(marker):
            return False

        prefix = f"@{self._config.mention} — " if self._config.mention else ""
        body = (
            f"{marker}\n"
            f"{prefix}Runner-MCP task completed.\n\n"
            f"- Project: `{event.project}`\n"
            f"- Test profile: `{event.profile}`\n"
            f"- Status: `{event.state.value}`\n"
            f"- Event: `{event.event_id}`\n\n"
            "Notification delivery did not re-run the task."
        )
        try:
            raw = self._session.post_json(
                self._comments_path(),
                payload={"body": body},
            )
        except Exception as exc:
            raise CompletionDeliveryError("completion notification delivery failed") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), int):
            raise CompletionDeliveryError("completion notification response is invalid")
        return True

    def _marker_exists(self, marker: str) -> bool:
        try:
            for page in range(1, MAX_COMMENT_PAGES + 1):
                raw = self._session.get_json(
                    self._comments_path(),
                    query={"per_page": "100", "page": str(page)},
                    allow_not_found=False,
                )
                if not isinstance(raw, list) or len(raw) > 100:
                    raise CompletionDeliveryError(
                        "completion notification comments response is invalid"
                    )
                for record in raw:
                    if not isinstance(record, dict):
                        raise CompletionDeliveryError(
                            "completion notification comment is invalid"
                        )
                    body = record.get("body")
                    if body is not None and not isinstance(body, str):
                        raise CompletionDeliveryError(
                            "completion notification comment body is invalid"
                        )
                    if isinstance(body, str) and marker in body:
                        return True
                if len(raw) < 100:
                    return False
        except CompletionDeliveryError:
            raise
        except Exception as exc:
            raise CompletionDeliveryError("completion notification lookup failed") from exc
        raise CompletionDeliveryError("completion notification comment scan exceeded page limit")

    def _comments_path(self) -> str:
        owner, repository = self._config.repository.split("/", 1)
        return f"/repos/{owner}/{repository}/issues/{self._config.issue_number}/comments"


class CompletionNotifierRuntime:
    def __init__(
        self,
        *,
        config_dir: Path,
        jobs_root: Path,
        config: GitHubIssueNotificationConfig,
        notifier: GitHubIssueCompletionNotifier | None = None,
        diagnostic_sink: Callable[[str], object] | None = None,
    ) -> None:
        self._config_dir = config_dir.expanduser().resolve()
        self._jobs_root = jobs_root
        self._config = config
        self._notifier = notifier or GitHubIssueCompletionNotifier(config)
        self._ledger = CompletionDeliveryLedger(notification_ledger_path(config_dir))
        self._diagnostic_sink = diagnostic_sink

    @classmethod
    def from_private_config(cls, config_dir: Path) -> CompletionNotifierRuntime:
        config_dir = config_dir.expanduser().resolve()
        _paths, settings, _registry = read_private_runtime(config_dir)
        if settings.test_jobs_root is None:
            raise CompletionDeliveryError("test job storage is not configured")
        return cls(
            config_dir=config_dir,
            jobs_root=settings.test_jobs_root,
            config=load_github_issue_notifier(config_dir),
        )

    def bootstrap(self) -> None:
        bootstrap_completion_notifier(self._config_dir)

    def run_once(self) -> CompletionNotifierCycleOutcome:
        bootstrap = _load_bootstrap(self._config_dir)
        destination_id = _destination_id(self._config)
        if bootstrap["destination_id"] != destination_id:
            raise CompletionDeliveryError(
                "completion notifier destination changed; bootstrap is required"
            )
        since = datetime.fromisoformat(bootstrap["started_at"]).astimezone(UTC)
        events = scan_test_completion_events(self._jobs_root, since=since)

        delivered = 0
        reconciled = 0
        already = 0
        failures = 0
        for event in events:
            if self._ledger.contains(
                destination_id=destination_id,
                event_id=event.event_id,
            ):
                already += 1
                continue
            try:
                created = self._notifier.deliver(event)
            except CompletionDeliveryError:
                failures += 1
                continue
            self._ledger.mark_delivered(
                destination_id=destination_id,
                event_id=event.event_id,
            )
            if created:
                delivered += 1
            else:
                reconciled += 1

        return CompletionNotifierCycleOutcome(
            discovered_events=len(events),
            delivered_events=delivered,
            reconciled_events=reconciled,
            already_delivered_events=already,
            delivery_failures=failures,
        )

    def _diagnose(
        self,
        event: DiagnosticEvent,
        error: DiagnosticErrorCategory | None = None,
    ) -> None:
        if self._diagnostic_sink is None:
            return
        self._diagnostic_sink(
            render_safe_diagnostic(
                component=DiagnosticComponent.COMPLETION_WATCHER,
                event=event,
                error=error,
            )
        )

    def run_forever(self, *, poll_seconds: float = 5.0) -> None:
        if not 1 <= poll_seconds <= 300:
            raise ValueError("completion notifier poll interval must be between 1 and 300 seconds")

        self._diagnose(DiagnosticEvent.LIFECYCLE_STARTED)
        try:
            while True:
                outcome = self.run_once()
                self._diagnose(
                    (
                        DiagnosticEvent.CYCLE_HEALTHY
                        if outcome.healthy
                        else DiagnosticEvent.CYCLE_DEGRADED
                    ),
                    (
                        None
                        if outcome.healthy
                        else DiagnosticErrorCategory.DELIVERY_FAILED
                    ),
                )
                try:
                    run_restart_if_requested(
                        self._config_dir,
                        "completion-watcher",
                        lambda: reexec_component(
                            self._config_dir,
                            "completion-watcher",
                        ),
                    )
                except SelfUpdateError as exc:
                    self._diagnose(
                        DiagnosticEvent.SUPERVISOR_RESTART_FAILED,
                        DiagnosticErrorCategory.RESTART_FAILED,
                    )
                    raise CompletionDeliveryError(
                        "Runner MCP self-update restart failed"
                    ) from exc
                time.sleep(poll_seconds)
        finally:
            self._diagnose(DiagnosticEvent.LIFECYCLE_STOPPED)
