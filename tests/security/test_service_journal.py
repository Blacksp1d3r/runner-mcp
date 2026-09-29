from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp import service_journal as journal_module
from runner_mcp.bridge_protocol import BridgeAction
from runner_mcp.config import ProjectConfig, ProjectRegistry, ServiceConfig
from runner_mcp.service_journal import (
    MAX_JOURNAL_RAW_BYTES,
    JournalCapture,
    ServiceJournalError,
    ServiceJournalReader,
    SystemdJournalBackend,
    _run_bounded_stdout,
)


class FakeBackend:
    def __init__(self, capture: JournalCapture | None = None) -> None:
        self.capture = capture or JournalCapture(text="safe\n", truncated=False)
        self.calls: list[tuple[str, int]] = []

    def tail(self, unit: str, *, lines: int) -> JournalCapture:
        self.calls.append((unit, lines))
        return self.capture


def registry(
    tmp_path: Path,
    *,
    allow_log_read: bool,
    health_url: str | None = "http://127.0.0.1:9999/private-health",
) -> ProjectRegistry:
    root = tmp_path / "project"
    root.mkdir()
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=root,
                services={
                    "web": ServiceConfig(
                        unit="private-web.service",
                        health_url=health_url,
                        allow_restart=True,
                        allow_log_read=allow_log_read,
                    )
                },
            )
        }
    )


def test_log_read_disabled_fails_before_backend(tmp_path: Path) -> None:
    backend = FakeBackend()
    reader = ServiceJournalReader(
        registry=registry(tmp_path, allow_log_read=False),
        backend=backend,
    )

    with pytest.raises(ServiceJournalError, match="not allowed"):
        reader.tail("demo", "web", lines=20)

    assert backend.calls == []


def test_unknown_alias_fails_before_backend(tmp_path: Path) -> None:
    backend = FakeBackend()
    reader = ServiceJournalReader(
        registry=registry(tmp_path, allow_log_read=True),
        backend=backend,
    )

    with pytest.raises(ServiceJournalError, match="Unknown or disabled service"):
        reader.tail("demo", "missing", lines=20)

    assert backend.calls == []


@pytest.mark.parametrize("lines", [0, 101, True])
def test_line_limit_is_rejected_before_backend(
    tmp_path: Path,
    lines: object,
) -> None:
    backend = FakeBackend()
    reader = ServiceJournalReader(
        registry=registry(tmp_path, allow_log_read=True),
        backend=backend,
    )

    with pytest.raises(ServiceJournalError, match="between 1 and 100"):
        reader.tail("demo", "web", lines=lines)  # type: ignore[arg-type]

    assert backend.calls == []


def test_reader_redacts_runtime_secrets_paths_unit_and_health_url(
    tmp_path: Path,
) -> None:
    secret = "postgresql://user:very-private@example.invalid/app"
    github_token = "ghp_" + ("a" * 30)
    private_path = str(tmp_path / "private-data")
    project_root = str(tmp_path / "project")
    health_url = "http://127.0.0.1:9999/private-health"
    backend = FakeBackend(
        JournalCapture(
            text=(
                f"dsn={secret}\n"
                f"token={github_token}\n"
                f"path={private_path}\n"
                f"root={project_root}\n"
                "unit=private-web.service\n"
                f"health={health_url}\n"
                "password=abcdefghijk\n"
            ),
            truncated=False,
        )
    )
    reader = ServiceJournalReader(
        registry=registry(
            tmp_path,
            allow_log_read=True,
            health_url=health_url,
        ),
        secret_values=[secret],
        private_paths=[private_path],
        backend=backend,
    )

    result = reader.tail("demo", "web", lines=50)

    assert backend.calls == [("private-web.service", 50)]
    assert result["project"] == "demo"
    assert result["service"] == "web"
    assert result["truncated"] is False
    content = str(result["content"])
    for sensitive in (
        secret,
        github_token,
        private_path,
        project_root,
        "private-web.service",
        health_url,
        "abcdefghijk",
    ):
        assert sensitive not in content
    assert "[REDACTED]" in content
    assert "[PRIVATE_PATH]" in content
    assert "hostname" not in result
    assert "unit" not in result
    assert "cursor" not in result
    assert "argv" not in result


def test_reader_preserves_backend_truncation_and_boundary_redaction(
    tmp_path: Path,
) -> None:
    secret = "secret-boundary-value"
    prefix = "x" * (MAX_JOURNAL_RAW_BYTES - 8)
    backend = FakeBackend(
        JournalCapture(
            text=prefix + secret[:8],
            truncated=True,
        )
    )
    reader = ServiceJournalReader(
        registry=registry(tmp_path, allow_log_read=True),
        secret_values=[secret],
        backend=backend,
    )

    result = reader.tail("demo", "web", lines=100)

    assert result["truncated"] is True
    assert secret[:8] not in str(result["content"])
    assert len(str(result["content"]).encode("utf-8")) <= MAX_JOURNAL_RAW_BYTES


def test_systemd_journal_backend_builds_only_fixed_tail_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "journalctl"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    calls: list[tuple[list[str], float]] = []

    def fake_run(arguments: list[str], *, timeout_seconds: float) -> JournalCapture:
        calls.append((arguments, timeout_seconds))
        return JournalCapture(text="entry\n", truncated=False)

    monkeypatch.setattr(journal_module, "_run_bounded_stdout", fake_run)
    backend = SystemdJournalBackend(executable=executable, timeout_seconds=7)

    result = backend.tail("private-web.service", lines=25)

    assert result.text == "entry\n"
    assert calls == [
        (
            [
                str(executable),
                "--user",
                "--unit",
                "private-web.service",
                "--no-pager",
                "--output=cat",
                "--lines=25",
            ],
            7.0,
        )
    ]


def test_bounded_subprocess_uses_fixed_environment_no_shell_and_no_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeStdout:
        def __init__(self) -> None:
            self.reads = [b"hello\n", b""]

        def read(self, _size: int) -> bytes:
            return self.reads.pop(0)

        def close(self) -> None:
            captured["stdout_closed"] = True

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()

        def wait(self, timeout=None):
            captured["wait_timeout"] = timeout
            return 0

        def kill(self) -> None:
            captured["killed"] = True

    def fake_popen(arguments, **kwargs):
        captured["arguments"] = arguments
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(journal_module.subprocess, "Popen", fake_popen)

    result = _run_bounded_stdout(
        ["/usr/bin/journalctl", "--user", "--lines=1"],
        timeout_seconds=6,
    )

    assert result == JournalCapture(text="hello\n", truncated=False)
    assert captured["arguments"] == [
        "/usr/bin/journalctl",
        "--user",
        "--lines=1",
    ]
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.DEVNULL
    assert kwargs["env"] == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    assert captured["wait_timeout"] == 6
    assert captured["stdout_closed"] is True


def test_bounded_subprocess_retains_at_most_32_kib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized = b"x" * (MAX_JOURNAL_RAW_BYTES + 4096)

    class FakeStdout:
        def __init__(self) -> None:
            self.reads = [oversized, b""]

        def read(self, _size: int) -> bytes:
            return self.reads.pop(0)

        def close(self) -> None:
            return None

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()

        def wait(self, timeout=None):
            return 0

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        journal_module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: FakeProcess(),
    )

    result = _run_bounded_stdout(["/usr/bin/journalctl"], timeout_seconds=5)

    assert result.truncated is True
    assert len(result.text.encode("utf-8")) == MAX_JOURNAL_RAW_BYTES


def test_backend_rejects_symlink_executable(tmp_path: Path) -> None:
    target = tmp_path / "journalctl-real"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    link = tmp_path / "journalctl"
    link.symlink_to(target)

    with pytest.raises(ServiceJournalError, match="unavailable"):
        SystemdJournalBackend(executable=link)


def test_backend_failure_does_not_expose_stderr_or_exception_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive = "/private/path unit=private-web.service"

    class FakeStdout:
        def read(self, _size: int) -> bytes:
            return b""

        def close(self) -> None:
            return None

    class FakeProcess:
        stdout = FakeStdout()

        def wait(self, timeout=None):
            return 7

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        journal_module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: FakeProcess(),
    )

    with pytest.raises(ServiceJournalError) as captured:
        _run_bounded_stdout(
            ["/usr/bin/journalctl", "--unit", sensitive],
            timeout_seconds=5,
        )

    assert str(captured.value) == "Service journal command failed"
    assert sensitive not in str(captured.value)


def test_service_journal_is_not_a_bridge_action() -> None:
    values = {action.value for action in BridgeAction}
    assert "service_log" not in values
    assert "service_journal" not in values
