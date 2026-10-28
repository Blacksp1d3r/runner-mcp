from __future__ import annotations

import fcntl
import os
import subprocess
from pathlib import Path

import pytest

from runner_mcp.autostart_activation import AutostartActivationPermit
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


def test_render_cron_block_adds_fixed_tunnel_port(tmp_path: Path) -> None:
    executable = tmp_path / "runner-mcp"
    config = tmp_path / "private config"

    block = render_cron_block(
        executable=executable,
        config_dir=config,
        components=("server", "tunnel"),
        port=8123,
    )

    assert "autostart cron-run server --port 8123" in block[2]
    assert "autostart cron-run tunnel --port 8123" in block[3]


def test_direct_cron_install_refuses_existing_systemd_units_without_crontab_write(
    tmp_path: Path,
    fake_crontab_executable: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crontab = FakeCrontab("17 2 * * * /usr/bin/backup\n")
    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", lambda: True
    )

    with pytest.raises(CronAutostartError, match="parallel cron activation"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server",),
            runner=crontab,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert crontab.calls == []
    assert crontab.content == "17 2 * * * /usr/bin/backup\n"


def test_direct_cron_install_refuses_unreadable_systemd_units_without_writes(
    tmp_path: Path,
    fake_crontab_executable: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.autostart import AutostartError

    crontab = FakeCrontab("17 2 * * * /usr/bin/backup\n")

    def unavailable() -> bool:
        raise AutostartError("private unit path")

    monkeypatch.setattr(
        "runner_mcp.autostart.has_managed_user_units", unavailable
    )
    with pytest.raises(CronAutostartError, match="managed systemd status is unavailable"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server",),
            runner=crontab,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert crontab.calls == []
    assert crontab.content == "17 2 * * * /usr/bin/backup\n"


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
        activation_permit=AutostartActivationPermit.clear(),
    )
    second = install_cron_services(
        executable=executable,
        config_dir=config,
        components=("server", "github-watcher"),
        runner=crontab,
        activation_permit=AutostartActivationPermit.clear(),
    )

    assert first == ("server",)
    assert second == ("server", "github-watcher")
    assert crontab.content.count(CRON_BEGIN) == 1
    assert crontab.content.count(CRON_END) == 1
    assert "17 2 * * * /usr/bin/backup" in crontab.content
    assert "cron-run server" in crontab.content
    assert "cron-run github-watcher" in crontab.content


def test_install_rejects_unmanaged_tunnel_cron_supervisor(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab(
        "* * * * * /home/user/.local/bin/runner-mcp autostart cron-run tunnel --port 8000\n"
    )

    with pytest.raises(CronAutostartError, match="unmanaged Runner MCP"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server", "tunnel"),
            runner=crontab,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert len(crontab.calls) == 1


def test_install_rejects_unmanaged_tunnel_run_cron(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab(
        "* * * * * /home/user/.local/bin/runner-mcp tunnel-run --port 8000\n"
    )

    with pytest.raises(CronAutostartError, match="unmanaged Runner MCP"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server", "tunnel"),
            runner=crontab,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert len(crontab.calls) == 1


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
            activation_permit=AutostartActivationPermit.clear(),
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
            activation_permit=AutostartActivationPermit.clear(),
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


def test_cron_tunnel_waits_until_managed_server_is_active(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    called: list[bool] = []

    assert run_cron_component(
        config_dir=config,
        executable=executable,
        component="tunnel",
        port=8123,
        exec_fn=lambda *_args: called.append(True),
    ) == 0

    assert called == []


def test_cron_tunnel_uses_fixed_runtime_when_server_lock_is_active(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    server_lock = config / "autostart-server.lock"
    server_fd = server_lock.open("w")
    server_lock.chmod(0o600)
    fcntl.flock(server_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    captured: dict[str, object] = {}

    def fake_exec(path: str, argv: list[str]) -> object:
        captured["path"] = path
        captured["argv"] = argv
        return object()

    try:
        assert run_cron_component(
            config_dir=config,
            executable=executable,
            component="tunnel",
            port=8123,
            exec_fn=fake_exec,
        ) == 0
    finally:
        fcntl.flock(server_fd.fileno(), fcntl.LOCK_UN)
        server_fd.close()

    assert captured["path"] == str(executable)
    assert captured["argv"][-3:] == ["tunnel-run", "--port", "8123"]


@pytest.mark.parametrize(
    ("component", "tail"),
    [
        ("topology-heartbeat", ["topology-heartbeat", "run"]),
        ("github-watcher", ["github-watcher", "run"]),
        ("completion-watcher", ["completion-watcher", "run"]),
        ("agent-bus-worker", ["agent-bus-worker", "run"]),
        ("fabric-agent-qualification", ["fabric-agent-qualification", "run"]),
        ("fabric-live-overview", ["fabric-live-overview", "run"]),
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
    lock_path.chmod(0o600)
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
    lock_path = config / "autostart-server.lock"
    assert component_active(config, "server") is False
    assert not lock_path.exists()

    lock_path.write_bytes(b"")
    lock_path.chmod(0o600)
    with lock_path.open("r+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert component_active(config, "server") is True
    assert lock_path.stat().st_mode & 0o777 == 0o600


def test_cron_status_reports_only_managed_components(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    crontab = FakeCrontab(
        f"{CRON_BEGIN}\n"
        'MAILTO=""\n'
        f"* * * * * /x/runner-mcp --config-dir {config} autostart cron-run server "
        "--port 8000 >/dev/null 2>&1\n"
        f"{CRON_END}\n"
    )

    rows = cron_status(
        config_dir=config,
        components=("server",),
        runner=crontab,
    )
    assert not (config / "autostart-server.lock").exists()

    assert [row.public_dict() for row in rows] == [
        {
            "component": "server",
            "installed": True,
            "enabled": True,
            "active": False,
        },
        {
            "component": "tunnel",
            "installed": False,
            "enabled": False,
            "active": False,
        },
        {
            "component": "topology-heartbeat",
            "installed": False,
            "enabled": False,
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
        {
            "component": "agent-bus-worker",
            "installed": False,
            "enabled": False,
            "active": False,
        },
        {
            "component": "fabric-agent-qualification",
            "installed": False,
            "enabled": False,
            "active": False,
        },
        {
            "component": "fabric-live-overview",
            "installed": False,
            "enabled": False,
            "active": False,
        },
    ]


def test_install_without_clear_permit_does_not_read_or_write_crontab(
    tmp_path: Path,
    fake_crontab_executable: None,
) -> None:
    crontab = FakeCrontab("17 2 * * * /usr/bin/backup\n")
    original = crontab.content

    with pytest.raises(CronAutostartError, match="activation is blocked"):
        install_cron_services(
            executable=tmp_path / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server",),
            runner=crontab,
        )

    assert crontab.calls == []
    assert crontab.content == original


def test_cron_status_does_not_change_preexisting_lock_bytes_or_mode(
    tmp_path: Path, fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    lock = config / "autostart-server.lock"
    lock.write_bytes(b"owner-lock")
    lock.chmod(0o600)
    crontab = FakeCrontab(
        f"{CRON_BEGIN}\n"
        f"* * * * * /x/runner-mcp --config-dir {config} autostart cron-run server "
        "--port 8000 >/dev/null 2>&1\n"
        f"{CRON_END}\n"
    )
    before = lock.stat()
    result = cron_status(config_dir=config, components=("server",), runner=crontab)
    after = lock.stat()
    assert result[0].installed is True
    assert result[0].active is False
    assert lock.read_bytes() == b"owner-lock"
    assert after.st_ino == before.st_ino
    assert after.st_mode == before.st_mode
    assert after.st_mtime_ns == before.st_mtime_ns
    assert len(crontab.calls) == 1
    assert crontab.calls[0][0][-1] == "-l"


@pytest.mark.parametrize("unsafe", ("symlink", "hardlink", "fifo", "permissions"))
def test_component_active_rejects_unsafe_lock_without_rewriting_it(
    tmp_path: Path, unsafe: str,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    lock = config / "autostart-server.lock"
    outside = tmp_path / "outside"
    outside.write_text("untouched")
    if unsafe == "symlink":
        lock.symlink_to(outside)
    elif unsafe == "hardlink":
        os.link(outside, lock)
    elif unsafe == "fifo":
        os.mkfifo(lock, mode=0o600)
    else:
        lock.write_bytes(b"not-private")
        lock.chmod(0o644)
    with pytest.raises(CronAutostartError, match="cron lock observation"):
        component_active(config, "server")
    assert outside.read_text() == "untouched"
    if unsafe == "permissions":
        assert lock.stat().st_mode & 0o777 == 0o644
    elif unsafe == "symlink":
        assert lock.is_symlink()


def test_missing_cron_lock_is_not_a_claim_that_scheduled_role_failed(
    tmp_path: Path, fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    crontab = FakeCrontab(
        f"{CRON_BEGIN}\n"
        f"* * * * * /x/runner-mcp --config-dir {config} autostart cron-run "
        "topology-heartbeat >/dev/null 2>&1\n"
        f"{CRON_END}\n"
    )
    rows = cron_status(
        config_dir=config, components=("topology-heartbeat",), runner=crontab,
    )
    observed = next(row for row in rows if row.component == "topology-heartbeat")
    assert observed.installed is True
    assert observed.enabled is True
    assert observed.active is False
    assert not (config / "autostart-topology-heartbeat.lock").exists()


@pytest.mark.parametrize("fake_entry", (
    "# * * * * * /x/runner-mcp --config-dir /x autostart cron-run server --port 8000 >/dev/null 2>&1",
    "* * * * * /x/runner-mcp --config-dir /x autostart cron-run server-stale --port 8000 >/dev/null 2>&1",
    "* * * * * echo autostart cron-run server --port 8000 >/dev/null 2>&1",
    "* * * * * /x/runner-mcp --config-dir /x autostart cron-run server --port 0 >/dev/null 2>&1",
    "* * * * * /x/runner-mcp --config-dir /x autostart cron-run server --port 99999999999999999999999999999 >/dev/null 2>&1",
    "* * * * * /x/runner-mcp --config-dir /x autostart cron-run server --port 8000 >/dev/null",
    "5 * * * * /x/runner-mcp --config-dir /x autostart cron-run server --port 8000 >/dev/null 2>&1",
))
def test_cron_status_cannot_mark_noncanonical_role_command_installed(
    tmp_path: Path, fake_crontab_executable: None, fake_entry: str,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    crontab = FakeCrontab(
        f"{CRON_BEGIN}\n{fake_entry}\n{CRON_END}\n"
    )
    rows = cron_status(
        config_dir=config, components=("server",), runner=crontab,
    )
    server = next(row for row in rows if row.component == "server")
    assert server.installed is False
    assert server.enabled is False
    assert server.active is False
    assert not (config / "autostart-server.lock").exists()


def test_cron_status_accepts_only_exact_rendered_managed_role_entries(
    tmp_path: Path, fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private config"
    config.mkdir(mode=0o700)
    executable = tmp_path / "runner-mcp"
    block = render_cron_block(
        executable=executable,
        config_dir=config,
        components=("server", "topology-heartbeat", "github-watcher"),
        port=8000,
    )
    rows = cron_status(
        config_dir=config,
        components=("server", "topology-heartbeat", "github-watcher"),
        runner=FakeCrontab("\n".join(block) + "\n"),
    )
    installed = {row.component for row in rows if row.installed}
    assert installed == {"server", "topology-heartbeat", "github-watcher"}
    assert not list(config.glob("autostart-*.lock"))



@pytest.mark.parametrize("mismatch", ("foreign_config", "old_release", "both"))
def test_cron_status_does_not_promote_foreign_configuration_or_release(
    tmp_path: Path, fake_crontab_executable: None, mismatch: str,
) -> None:
    current_config = tmp_path / "current-config"
    current_config.mkdir(mode=0o700)
    foreign_config = tmp_path / "other-config"
    foreign_config.mkdir(mode=0o700)
    current_executable = tmp_path / "current-release" / "runner-mcp"
    old_executable = tmp_path / "old-release" / "runner-mcp"
    scheduled_config = (
        foreign_config if mismatch in {"foreign_config", "both"}
        else current_config
    )
    scheduled_executable = (
        old_executable if mismatch in {"old_release", "both"}
        else current_executable
    )
    crontab = FakeCrontab("\n".join(render_cron_block(
        executable=scheduled_executable, config_dir=scheduled_config,
        components=("server", "github-watcher"), port=8000,
    )) + "\n")
    observed = cron_status(
        config_dir=current_config,
        executable=current_executable,
        components=("server", "github-watcher"),
        runner=crontab,
    )
    assert all(not row.installed and not row.active for row in observed)
    assert not list(current_config.glob("autostart-*.lock"))


def test_cron_status_exact_config_and_release_reports_configured_not_live(
    tmp_path: Path, fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private config"
    config.mkdir(mode=0o700)
    executable = tmp_path / "version-0.1.90" / "runner-mcp"
    cron = FakeCrontab("\n".join(render_cron_block(
        executable=executable, config_dir=config,
        components=("server", "topology-heartbeat"), port=8000,
    )) + "\n")
    result = cron_status(
        config_dir=config, executable=executable,
        components=("server", "topology-heartbeat"),
        runner=cron,
    )
    assert [row.component for row in result if row.installed] == [
        "server", "topology-heartbeat",
    ]
    assert all(not row.active for row in result)
    assert not list(config.glob("autostart-*.lock"))



@pytest.mark.parametrize("duplicate", ("same", "old_release", "foreign_config"))
def test_cron_status_duplicate_role_claim_not_marked_installed(
    tmp_path: Path, fake_crontab_executable: None, duplicate: str,
) -> None:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    executable = tmp_path / "release-current" / "runner-mcp"
    original = render_cron_block(
        executable=executable, config_dir=config,
        components=("server",), port=8000,
    )
    if duplicate == "same":
        second = original[2]
    else:
        second = render_cron_block(
            executable=(
                tmp_path / "release-old" / "runner-mcp"
                if duplicate == "old_release" else executable
            ),
            config_dir=(
                tmp_path / "foreign-config"
                if duplicate == "foreign_config" else config
            ),
            components=("server",), port=8000,
        )[2]
    lines = [*original[:-1], second, CRON_END]
    observed = cron_status(
        config_dir=config, executable=executable,
        components=("server",), runner=FakeCrontab("\n".join(lines) + "\n"),
    )
    server = next(row for row in observed if row.component == "server")
    assert server.installed is False
    assert server.enabled is False
    assert server.active is False
    assert not (config / "autostart-server.lock").exists()


@pytest.mark.parametrize("unsafe", (
    "symlink", "hardlink", "fifo", "directory", "permissions",
))
def test_cron_run_never_changes_unsafe_existing_lock_or_executes(
    tmp_path: Path, unsafe: str,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    lock = config / "autostart-server.lock"
    external = tmp_path / "unrelated-existing-file"
    external.write_bytes(b"do-not-chmod-or-write")
    external.chmod(0o600)
    if unsafe == "symlink":
        lock.symlink_to(external)
    elif unsafe == "hardlink":
        os.link(external, lock)
    elif unsafe == "fifo":
        os.mkfifo(lock, mode=0o600)
    elif unsafe == "directory":
        lock.mkdir(mode=0o700)
    else:
        lock.write_bytes(b"existing-unsafe-mode")
        lock.chmod(0o644)

    before_mode = external.stat().st_mode
    before_bytes = external.read_bytes()
    calls: list[tuple[str, list[str]]] = []
    with pytest.raises(CronAutostartError, match="cron autostart lock"):
        run_cron_component(
            config_dir=config,
            executable=tmp_path / "unused-entrypoint",
            component="server",
            exec_fn=lambda path, argv: calls.append((path, argv)),
        )
    assert calls == []
    assert external.read_bytes() == before_bytes
    assert external.stat().st_mode == before_mode
    if unsafe == "permissions":
        assert lock.stat().st_mode & 0o777 == 0o644
        assert lock.read_bytes() == b"existing-unsafe-mode"
    if unsafe == "symlink":
        assert lock.is_symlink()


def test_cron_run_creates_single_owner_private_lock_for_actual_exec(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    lock = config / "autostart-github-watcher.lock"
    calls: list[tuple[str, list[str]]] = []
    assert run_cron_component(
        config_dir=config,
        executable=tmp_path / "runner-mcp",
        component="github-watcher",
        exec_fn=lambda path, argv: calls.append((path, argv)),
    ) == 0
    assert len(calls) == 1
    assert calls[0][1][-2:] == ["github-watcher", "run"]
    assert lock.is_file()
    st = lock.stat()
    assert st.st_uid == os.geteuid()
    assert st.st_nlink == 1
    assert st.st_mode & 0o777 == 0o600


def test_cron_run_reuses_valid_private_lock_without_overwriting_bytes(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    lock = config / "autostart-completion-watcher.lock"
    lock.write_bytes(b"legacy-lock-content")
    lock.chmod(0o600)
    original_inode = lock.stat().st_ino
    called: list[bool] = []
    assert run_cron_component(
        config_dir=config,
        executable=tmp_path / "runner-mcp",
        component="completion-watcher",
        exec_fn=lambda *_args: called.append(True),
    ) == 0
    assert called == [True]
    assert lock.read_bytes() == b"legacy-lock-content"
    assert lock.stat().st_ino == original_inode


@pytest.mark.parametrize("component", (
    "server", "tunnel", "topology-heartbeat", "github-watcher",
    "completion-watcher", "agent-bus-worker",
    "fabric-agent-qualification", "fabric-live-overview",
))
def test_unmanaged_cron_run_role_blocks_install_without_changing_crontab(
    tmp_path: Path, fake_crontab_executable: None, component: str,
) -> None:
    """A legacy supervisor outside the owner block must not be duplicated."""
    legacy = (
        f"* * * * * /legacy/runner-mcp --config-dir /legacy/private "
        f"autostart cron-run {component}"
    )
    if component in {"server", "tunnel"}:
        legacy += " --port 8000"
    crontab = FakeCrontab(legacy + "\n")
    old_content = crontab.content
    with pytest.raises(CronAutostartError, match="unmanaged Runner MCP"):
        install_cron_services(
            executable=tmp_path / "current-release" / "runner-mcp",
            config_dir=tmp_path / "private",
            components=("server", "topology-heartbeat"),
            runner=crontab,
            activation_permit=AutostartActivationPermit.clear(),
        )
    assert crontab.content == old_content
    assert len(crontab.calls) == 1
    assert crontab.calls[0][0][-1] == "-l"


@pytest.mark.parametrize("relative_position", ("before", "after"))
def test_status_refuses_duplicate_unmanaged_server_outside_owned_block(
    tmp_path: Path, fake_crontab_executable: None, relative_position: str,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    executable = tmp_path / "current-release" / "runner-mcp"
    block = render_cron_block(
        executable=executable,
        config_dir=config,
        components=("server", "topology-heartbeat"),
        port=8000,
    )
    old_server = (
        "* * * * * /old-release/runner-mcp --config-dir /old/private "
        "autostart cron-run server --port 8000 >/dev/null 2>&1"
    )
    lines = ([old_server, *block] if relative_position == "before"
             else [*block, old_server])
    crontab = FakeCrontab("\n".join(lines) + "\n")
    with pytest.raises(CronAutostartError, match="unmanaged Runner MCP"):
        cron_status(
            config_dir=config,
            executable=executable,
            components=("server", "topology-heartbeat"),
            runner=crontab,
        )
    assert crontab.content == "\n".join(lines) + "\n"
    assert not list(config.glob("autostart-*.lock"))


def test_cron_status_ignores_commented_legacy_entry_outside_managed_block(
    tmp_path: Path, fake_crontab_executable: None,
) -> None:
    config = tmp_path / "private"
    config.mkdir(mode=0o700)
    executable = tmp_path / "current-release" / "runner-mcp"
    block = render_cron_block(
        executable=executable, config_dir=config,
        components=("server",), port=8000,
    )
    comment = (
        "# * * * * * /legacy/runner-mcp autostart "
        "cron-run server --port 8000"
    )
    rows = cron_status(
        config_dir=config, executable=executable, components=("server",),
        runner=FakeCrontab("\n".join([comment, *block]) + "\n"),
    )
    server = next(row for row in rows if row.component == "server")
    assert server.installed is True
    assert server.active is False
    assert not list(config.glob("autostart-*.lock"))
