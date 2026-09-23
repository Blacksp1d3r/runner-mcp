from __future__ import annotations

import fcntl
import subprocess
from pathlib import Path

import pytest

from runner_mcp.cron_autostart import (
    CRON_BEGIN,
    CRON_END,
    CronAutostartError,
    component_active,
    cron_status,
    install_cron_services,
    remove_cron_services,
    render_cron_block,
    run_cron_component,
)


class FakeCrontab:
    def __init__(self, initial: str = "") -> None:
        self.content = initial
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs.get("input")))
        command = argv[1:]
        if command == ["-l"]:
            if self.content:
                return subprocess.CompletedProcess(argv, 0, self.content, "")
            return subprocess.CompletedProcess(argv, 1, "", "no crontab")
        if command == ["-"]:
            self.content = kwargs["input"] or ""
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 2, "", "unexpected")


@pytest.fixture
def fake_crontab_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "runner_mcp.cron_autostart._crontab_executable",
        lambda: "/usr/bin/crontab",
    )


def test_render_cron_block_is_fixed_and_bounded(tmp_path: Path) -> None:
    executable = tmp_path / "runner-mcp"
    config = tmp_path / "private config"

    block = render_cron_block(
        executable=executable,
        config_dir=config,
        components=("server", "github-watcher"),
        port=8123,
    )

    assert block[0] == CRON_BEGIN
    assert block[-1] == CRON_END
    assert block[1] == 'MAILTO=""'
    assert len(block) == 5
    assert "autostart cron-run server --port 8123" in block[2]
    assert "autostart cron-run github-watcher" in block[3]
    assert "completion-watcher" not in "\n".join(block)
    assert " >/dev/null 2>&1" in block[2]


def test_install_preserves_unrelated_lines_and_is_idempotent(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab("17 2 * * * /usr/bin/backup\n")
    executable = tmp_path / "runner-mcp"
    config = tmp_path / "private"

    first = install_cron_services(
        executable=executable,
        config_dir=config,
        components=("server",),
        runner=crontab,
    )
    second = install_cron_services(
        executable=executable,
        config_dir=config,
        components=("server", "github-watcher"),
        runner=crontab,
    )

    assert first == ("server",)
    assert second == ("server", "github-watcher")
    assert crontab.content.count(CRON_BEGIN) == 1
    assert crontab.content.count(CRON_END) == 1
    assert "17 2 * * * /usr/bin/backup" in crontab.content
    assert "cron-run server" in crontab.content
    assert "cron-run github-watcher" in crontab.content


def test_install_rejects_unmanaged_runner_mcp_cron(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab(
        "* * * * * /home/user/.local/bin/runner-mcp github-watcher run\n"
    )

    with pytest.raises(CronAutostartError, match="unmanaged Runner MCP"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server",),
            runner=crontab,
        )

    assert len(crontab.calls) == 1


@pytest.mark.parametrize(
    "content",
    [
        f"{CRON_BEGIN}\n* * * * * echo bad\n",
        f"{CRON_END}\n",
        f"{CRON_BEGIN}\n{CRON_BEGIN}\n{CRON_END}\n",
        f"{CRON_END}\n{CRON_BEGIN}\n",
    ],
)
def test_malformed_managed_block_fails_closed(
    tmp_path: Path,
    fake_crontab_executable: None,
    content: str,
) -> None:
    crontab = FakeCrontab(content)

    with pytest.raises(CronAutostartError, match="malformed"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server",),
            runner=crontab,
        )


def test_remove_deletes_only_managed_block(
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab(
        "5 1 * * * /usr/bin/backup\n"
        f"{CRON_BEGIN}\n"
        'MAILTO=""\n'
        "* * * * * /x/runner-mcp autostart cron-run server >/dev/null 2>&1\n"
        f"{CRON_END}\n"
        "9 1 * * * /usr/bin/other\n"
    )

    assert remove_cron_services(runner=crontab) is True
    assert CRON_BEGIN not in crontab.content
    assert CRON_END not in crontab.content
    assert "/usr/bin/backup" in crontab.content
    assert "/usr/bin/other" in crontab.content


def test_cron_run_uses_fixed_exec_argv_and_loopback(
    tmp_path: Path,
) -> None:
    sensitive = "private-token-value"
    config = tmp_path / sensitive / "private"
    config.mkdir(parents=True, mode=0o700)
    executable = tmp_path / sensitive / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    captured = {}
    diagnostics: list[str] = []

    def fake_exec(path: str, argv: list[str]) -> object:
        captured["path"] = path
        captured["argv"] = argv
        return object()

    assert run_cron_component(
        config_dir=config,
        executable=executable,
        component="server",
        port=8123,
        exec_fn=fake_exec,
        diagnostic_sink=diagnostics.append,
    ) == 0

    assert captured["path"] == str(executable)
    assert captured["argv"] == [
        str(executable),
        "--config-dir",
        str(config.resolve()),
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        "8123",
    ]
    assert diagnostics == [
        "component=cron_supervisor event=supervisor_restart_handoff"
    ]
    assert sensitive not in diagnostics[0]
    assert str(config) not in diagnostics[0]
    assert str(executable) not in diagnostics[0]


@pytest.mark.parametrize(
    ("component", "tail"),
    [
        ("github-watcher", ["github-watcher", "run"]),
        ("completion-watcher", ["completion-watcher", "run"]),
    ],
)
def test_cron_run_uses_fixed_watcher_argv(
    tmp_path: Path,
    component: str,
    tail: list[str],
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    captured = {}

    def fake_exec(path: str, argv: list[str]) -> object:
        captured["argv"] = argv
        return object()

    assert run_cron_component(
        config_dir=config,
        executable=executable,
        component=component,
        exec_fn=fake_exec,
    ) == 0
    assert captured["argv"][-2:] == tail


def test_cron_run_does_not_start_duplicate_component(tmp_path: Path) -> None:
    sensitive = "secret-lock-context"
    config = tmp_path / sensitive / "private"
    config.mkdir(parents=True, mode=0o700)
    executable = tmp_path / sensitive / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    lock_path = config / "autostart-server.lock"
    lock_fd = lock_path.open("w")
    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    called = []
    diagnostics: list[str] = []

    try:
        assert run_cron_component(
            config_dir=config,
            executable=executable,
            component="server",
            exec_fn=lambda *_: called.append(True),
            diagnostic_sink=diagnostics.append,
        ) == 0
    finally:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()

    assert called == []
    assert diagnostics == [
        (
            "component=cron_supervisor event=supervisor_restart_failed "
            "error=supervisor_locked"
        )
    ]
    assert sensitive not in diagnostics[0]


def test_cron_run_failure_diagnostic_is_bounded(
    tmp_path: Path,
) -> None:
    sensitive = "private-exec-secret"
    config = tmp_path / sensitive / "private"
    config.mkdir(parents=True, mode=0o700)
    executable = tmp_path / sensitive / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    diagnostics: list[str] = []

    def fail_exec(_path: str, _argv: list[str]) -> object:
        raise OSError(f"{sensitive} {config} {executable}")

    with pytest.raises(CronAutostartError) as captured:
        run_cron_component(
            config_dir=config,
            executable=executable,
            component="completion-watcher",
            exec_fn=fail_exec,
            diagnostic_sink=diagnostics.append,
        )

    assert str(captured.value) == "cron autostart component could not start"
    assert sensitive not in str(captured.value)
    assert diagnostics == [
        (
            "component=cron_supervisor event=supervisor_restart_handoff"
        ),
        (
            "component=cron_supervisor event=supervisor_restart_failed "
            "error=restart_failed"
        ),
    ]
    rendered = "\n".join(diagnostics)
    assert sensitive not in rendered
    assert str(config) not in rendered
    assert str(executable) not in rendered
    assert "completion-watcher" not in rendered


def test_component_active_observes_shared_lock(tmp_path: Path) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    assert component_active(config, "server") is False

    lock_path = config / "autostart-server.lock"
    with lock_path.open("r+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert component_active(config, "server") is True


def test_cron_status_reports_only_managed_components(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    crontab = FakeCrontab(
        f"{CRON_BEGIN}\n"
        'MAILTO=""\n'
        "* * * * * /x/runner-mcp --config-dir /x autostart cron-run server "
        "--port 8000 >/dev/null 2>&1\n"
        f"{CRON_END}\n"
    )

    rows = cron_status(
        config_dir=config,
        components=("server",),
        runner=crontab,
    )

    assert [row.public_dict() for row in rows] == [
        {
            "component": "server",
            "installed": True,
            "enabled": True,
            "active": False,
        },
        {
            "component": "github-watcher",
            "installed": False,
            "enabled": False,
            "active": False,
        },
        {
            "component": "completion-watcher",
            "installed": False,
            "enabled": False,
            "active": False,
        },
    ]
