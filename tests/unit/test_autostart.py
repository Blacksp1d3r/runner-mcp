from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from runner_mcp import autostart as autostart_module
from runner_mcp import secure_io as secure_io_module
from runner_mcp.autostart import (
    AGENT_BUS_WORKER_UNIT,
    COMPLETION_WATCHER_UNIT,
    FABRIC_AGENT_QUALIFICATION_UNIT,
    FABRIC_LIVE_OVERVIEW_UNIT,
    GITHUB_WATCHER_UNIT,
    MANAGED_MARKER,
    SERVER_UNIT,
    TOPOLOGY_HEARTBEAT_UNIT,
    TUNNEL_UNIT,
    AutostartError,
    _write_managed_unit,
    install_user_services,
    plan_qualification_override_swap,
    remove_user_services,
    render_user_units,
    user_service_status,
)
from runner_mcp.autostart_activation import AutostartActivationPermit
from runner_mcp.completion_delivery import (
    bootstrap_completion_notifier,
    configure_github_issue_notifier,
)
from runner_mcp.config_manager import configure_github_mailbox
from runner_mcp.github_watcher import GitHubWatcherCursorStore
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


class FakeSystemctl:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.enabled: set[str] = set()
        self.active: set[str] = set()

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        assert kwargs["stdin"] is subprocess.DEVNULL
        assert kwargs["stdout"] is subprocess.PIPE
        assert kwargs["stderr"] is subprocess.PIPE
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 30
        assert kwargs["check"] is False
        command = argv[2:]
        returncode = 0
        if command[:1] == ["enable"] and "--now" in command:
            names = [item for item in command[2:] if item.endswith(".service")]
            self.enabled.update(names)
            self.active.update(names)
        elif command[:1] == ["disable"] and "--now" in command:
            names = [item for item in command[2:] if item.endswith(".service")]
            self.enabled.difference_update(names)
            self.active.difference_update(names)
        elif command[:1] == ["is-enabled"]:
            returncode = 0 if command[1] in self.enabled else 1
        elif command[:1] == ["is-active"]:
            returncode = 0 if command[1] in self.active else 3
        return subprocess.CompletedProcess(argv, returncode, "", "")


def _private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "private"
    paths = install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    return paths, executable


def test_migration_plan_is_never_a_cutover_permit() -> None:
    from runner_mcp.autostart import AutostartStatus, plan_cron_to_systemd
    from runner_mcp.cron_autostart import CRON_COMPONENTS, CronComponentStatus

    cron = tuple(
        CronComponentStatus(
            component=name,
            installed=name == "server",
            enabled=name == "server",
            active=False,
        )
        for name in CRON_COMPONENTS
    )
    units = tuple(
        AutostartStatus(name, installed=False, enabled=False, active=False)
        for name in CRON_COMPONENTS
    )
    inputs = {
        "component": "server",
        "expected_hostname": "test-host",
        "expected_uid": 1001,
        "observed_hostname": "test-host",
        "observed_uid": 1001,
        "configured_components": ("server",),
        "cron_managed": True,
        "cron_rows": cron,
        "systemd_rows": units,
        "systemd_manager_reachable": True,
    }
    plan = plan_cron_to_systemd(**inputs)
    assert plan.state == "PLAN_ONLY"
    assert plan.reason_code == "original_host_and_rollback_not_attested"
    assert plan.cron_installed
    assert plan.systemd_units_absent
    assert plan.systemd_manager_reachable
    assert plan.cutover_authorized is False


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"observed_hostname": "other-host"}, "host_or_uid_mismatch"),
        ({"observed_uid": 1002}, "host_or_uid_mismatch"),
        ({"expected_uid": 0, "observed_uid": 0}, "host_or_uid_mismatch"),
        ({"cron_managed": False}, "exact_owned_cron_role_unavailable"),
        ({"configured_components": ()}, "exact_owned_cron_role_unavailable"),
        ({"cron_rows": ()}, "exact_owned_cron_role_unavailable"),
        ({"systemd_manager_reachable": False}, "systemd_user_manager_unreachable"),
    ],
)
def test_migration_plan_fails_closed_for_missing_owner_or_manager(
    change: dict[str, object],
    reason: str,
) -> None:
    from runner_mcp.autostart import AutostartStatus, plan_cron_to_systemd
    from runner_mcp.cron_autostart import CRON_COMPONENTS, CronComponentStatus

    inputs = {
        "component": "server",
        "expected_hostname": "lab-host",
        "expected_uid": 1001,
        "observed_hostname": "lab-host",
        "observed_uid": 1001,
        "configured_components": ("server",),
        "cron_managed": True,
        "cron_rows": (CronComponentStatus("server", True, True, False),),
        "systemd_rows": tuple(
            AutostartStatus(name, False, False, False)
            for name in CRON_COMPONENTS
        ),
        "systemd_manager_reachable": True,
    }
    plan = plan_cron_to_systemd(**(inputs | change))
    assert plan.state == "WAIT"
    assert plan.reason_code == reason
    assert plan.cutover_authorized is False


def test_migration_plan_refuses_existing_foreign_or_duplicate_units() -> None:
    from runner_mcp.autostart import AutostartStatus, plan_cron_to_systemd
    from runner_mcp.cron_autostart import CRON_COMPONENTS, CronComponentStatus

    units = tuple(
        AutostartStatus(name, name == "server", False, False)
        for name in CRON_COMPONENTS
    )
    plan = plan_cron_to_systemd(
        component="server",
        expected_hostname="lab-host",
        expected_uid=1001,
        observed_hostname="lab-host",
        observed_uid=1001,
        configured_components=("server",),
        cron_managed=True,
        cron_rows=(CronComponentStatus("server", True, True, False),),
        systemd_rows=units,
        systemd_manager_reachable=True,
    )
    assert plan.state == "WAIT"
    assert plan.reason_code == "systemd_unit_conflict_or_unknown"
    assert plan.cutover_authorized is False


def test_render_server_unit_contains_no_credentials(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert set(units) == {SERVER_UNIT}
    assert units[SERVER_UNIT].startswith(MANAGED_MARKER)
    assert "127.0.0.1" in units[SERVER_UNIT]
    assert "serve" in units[SERVER_UNIT]
    assert "Authorization" not in units[SERVER_UNIT]
    assert "token" not in units[SERVER_UNIT].lower()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux systemd syntax qualification")
def test_disposable_rendered_units_pass_real_systemd_parser(tmp_path: Path) -> None:
    """Validate real unit syntax/dependencies without a user manager or install."""
    analyze = shutil.which("systemd-analyze")
    assert analyze is not None, "Linux qualification image must have systemd-analyze"
    paths, executable = _private_config(tmp_path)
    tunnel_env = paths.config_dir / "tunnel.env"
    tunnel_env.write_text(
        "CONTROL_PLANE_TUNNEL_ID=synthetic-qualification-id\n"
        "CONTROL_PLANE_API_KEY=synthetic-qualification-key\n",
        encoding="utf-8",
    )
    tunnel_env.chmod(0o600)
    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
        port=8123,
    )
    assert set(units) == {SERVER_UNIT, TUNNEL_UNIT}
    sandbox = tmp_path / "candidates"
    sandbox.mkdir()
    candidates = []
    for name, content in sorted(units.items()):
        target = sandbox / name
        target.write_text(content, encoding="utf-8")
        candidates.append(str(target))

    result = subprocess.run(
        [analyze, "verify", *candidates],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1200:]
    assert "synthetic-qualification-key" not in result.stderr
    assert "synthetic-qualification-key" not in result.stdout
    # Verification did not activate or install a service; only test-owned
    # disposable candidate files exist and the original source is untouched.
    assert {file.name for file in sandbox.iterdir()} == {SERVER_UNIT, TUNNEL_UNIT}


@pytest.mark.skipif(sys.platform != "linux", reason="Linux systemd syntax qualification")
def test_all_configured_roles_pass_real_systemd_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The complete known service graph must parse before any live cutover."""
    analyze = shutil.which("systemd-analyze")
    assert analyze is not None, "Linux qualification image must have systemd-analyze"
    paths, executable = _private_config(tmp_path)
    monkeypatch.setattr(
        autostart_module,
        "configured_autostart_components",
        lambda _config_dir: (
            "server",
            "tunnel",
            "topology-heartbeat",
            "github-watcher",
            "completion-watcher",
            "agent-bus-worker",
            "fabric-agent-qualification",
            "fabric-live-overview",
        ),
    )
    units = render_user_units(config_dir=paths.config_dir, executable=executable)
    assert set(units) == set(autostart_module.KNOWN_UNITS)
    sandbox = tmp_path / "candidate-graph"
    sandbox.mkdir()
    paths_to_verify: list[str] = []
    for unit_name, content in sorted(units.items()):
        candidate = sandbox / unit_name
        candidate.write_text(content, encoding="utf-8")
        paths_to_verify.append(str(candidate))
        assert "Restart=on-failure" in content
        assert "RestartSec=3" in content
        if unit_name != SERVER_UNIT:
            assert f"Requires={SERVER_UNIT}" in content
    result = subprocess.run(
        [analyze, "verify", *paths_to_verify],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1200:]
    assert {p.name for p in sandbox.iterdir()} == set(units)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux systemd syntax qualification")
def test_disposable_systemd_parser_rejects_broken_execstart(tmp_path: Path) -> None:
    """A malformed candidate must fail before any real manager is involved."""
    analyze = shutil.which("systemd-analyze")
    assert analyze is not None, "Linux qualification image must have systemd-analyze"
    paths, executable = _private_config(tmp_path)
    good = render_user_units(config_dir=paths.config_dir, executable=executable)[
        SERVER_UNIT
    ]
    broken = "\n".join(
        'ExecStart="unterminated' if line.startswith("ExecStart=") else line
        for line in good.splitlines()
    ) + "\n"
    candidate = tmp_path / SERVER_UNIT
    candidate.write_text(broken, encoding="utf-8")

    result = subprocess.run(
        [analyze, "verify", str(candidate)],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode != 0
    assert candidate.read_text(encoding="utf-8") == broken
    assert not (tmp_path / "units").exists()


def test_complete_tunnel_config_adds_fixed_dependent_tunnel_unit(
    tmp_path: Path,
) -> None:
    paths, executable = _private_config(tmp_path)
    tunnel_id = "tunnel_sensitive_placeholder"
    api_key = "api_sensitive_placeholder"
    tunnel_env = paths.config_dir / "tunnel.env"
    tunnel_env.write_text(
        f"CONTROL_PLANE_TUNNEL_ID={tunnel_id}\n"
        f"CONTROL_PLANE_API_KEY={api_key}\n",
        encoding="utf-8",
    )
    tunnel_env.chmod(0o600)

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
        port=8123,
    )

    assert set(units) == {SERVER_UNIT, TUNNEL_UNIT}
    content = units[TUNNEL_UNIT]
    assert f"After=network-online.target {SERVER_UNIT}" in content
    assert f"Requires={SERVER_UNIT}" in content
    assert "tunnel-run" in content
    assert "--port" in content
    assert "8123" in content
    assert tunnel_id not in content
    assert api_key not in content



def test_topology_heartbeat_unit_requires_tunnel_and_agent_bus(
    tmp_path: Path,
) -> None:
    paths, executable = _private_config(tmp_path)
    tunnel_env = paths.config_dir / "tunnel.env"
    tunnel_env.write_text(
        "CONTROL_PLANE_TUNNEL_ID=tunnel_sensitive_placeholder\n"
        "CONTROL_PLANE_API_KEY=api_sensitive_placeholder\n",
        encoding="utf-8",
    )
    tunnel_env.chmod(0o600)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_RELAY_ORIGIN=https://relay.example.invalid\n")
        handle.write("RUNNER_FABRIC_RELAY_SUBJECT=runner:one\n")
        handle.write(f"RUNNER_FABRIC_RELAY_CREDENTIAL={'r' * 48}\n")
        handle.write(
            "RUNNER_FABRIC_AGENT_RESOURCE_URL=http://127.0.0.1:9020/mcp\n"
        )
        handle.write(f"RUNNER_FABRIC_AGENT_BEARER_TOKEN={'a' * 48}\n")

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert TOPOLOGY_HEARTBEAT_UNIT in units
    content = units[TOPOLOGY_HEARTBEAT_UNIT]
    assert f"Requires={SERVER_UNIT}" in content
    assert "topology-heartbeat" in content
    assert " run" in content
    assert "relay.example.invalid" not in content
    assert "r" * 48 not in content


def test_agent_bus_worker_unit_is_added_only_when_configured(
    tmp_path: Path,
) -> None:
    paths, executable = _private_config(tmp_path)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_RELAY_ORIGIN=https://relay.example.invalid\n")
        handle.write("RUNNER_FABRIC_RELAY_SUBJECT=runner:one\n")
        handle.write(f"RUNNER_FABRIC_RELAY_CREDENTIAL={'r' * 48}\n")
        handle.write(
            "RUNNER_FABRIC_AGENT_RESOURCE_URL=http://127.0.0.1:9020/mcp\n"
        )
        handle.write(f"RUNNER_FABRIC_AGENT_BEARER_TOKEN={'a' * 48}\n")

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert set(units) == {
        SERVER_UNIT,
        AGENT_BUS_WORKER_UNIT,
        FABRIC_AGENT_QUALIFICATION_UNIT,
    }
    assert "agent-bus-worker" in units[AGENT_BUS_WORKER_UNIT]
    assert "r" * 48 not in units[AGENT_BUS_WORKER_UNIT]

def test_mailbox_autostart_requires_explicit_bootstrap(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="a" * 40,
    )

    with pytest.raises(AutostartError, match="not bootstrapped"):
        render_user_units(
            config_dir=paths.config_dir,
            executable=executable,
        )


def test_optional_watchers_are_added_only_after_bootstrap(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="a" * 40,
    )
    GitHubWatcherCursorStore(
        paths.config_dir / "github-mailbox-cursor.json"
    ).initialize("b" * 40)
    configure_github_issue_notifier(
        paths.config_dir,
        repository="example/private-mailbox",
        issue_number=25,
        mention="operator-user",
        token="c" * 40,
    )

    with pytest.raises(AutostartError, match="completion notifier.*not bootstrapped"):
        render_user_units(
            config_dir=paths.config_dir,
            executable=executable,
        )

    bootstrap_completion_notifier(paths.config_dir)
    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert set(units) == {
        SERVER_UNIT,
        GITHUB_WATCHER_UNIT,
        COMPLETION_WATCHER_UNIT,
    }
    combined = "\n".join(units.values())
    assert "a" * 40 not in combined
    assert "c" * 40 not in combined
    assert "github-watcher" in units[GITHUB_WATCHER_UNIT]
    assert "completion-watcher" in units[COMPLETION_WATCHER_UNIT]


def test_direct_systemd_install_refuses_active_managed_cron_before_any_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "uncreated_units"
    systemctl = FakeSystemctl()
    monkeypatch.setattr("runner_mcp.cron_autostart.cron_available", lambda: True)
    monkeypatch.setattr("runner_mcp.cron_autostart.has_managed_cron", lambda: True)

    with pytest.raises(AutostartError, match="parallel systemd activation"):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert not unit_dir.exists()
    assert systemctl.calls == []


def test_direct_systemd_install_refuses_unreadable_managed_cron(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.cron_autostart import CronAutostartError

    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "uncreated_units"
    systemctl = FakeSystemctl()

    def unavailable() -> bool:
        raise CronAutostartError("private crontab details")

    monkeypatch.setattr("runner_mcp.cron_autostart.cron_available", lambda: True)
    monkeypatch.setattr(
        "runner_mcp.cron_autostart.has_managed_cron", unavailable
    )

    with pytest.raises(AutostartError, match="managed cron status is unavailable"):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert not unit_dir.exists()
    assert systemctl.calls == []


def test_install_uses_fixed_systemctl_arrays_and_managed_files(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "units"
    systemctl = FakeSystemctl()

    installed = install_user_services(
        paths.config_dir,
        executable=executable,
        unit_dir=unit_dir,
        runner=systemctl,
        activation_permit=AutostartActivationPermit.clear(),
    )

    assert installed == [SERVER_UNIT]
    path = unit_dir / SERVER_UNIT
    assert path.is_file()
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert path.read_text().startswith(MANAGED_MARKER)
    assert systemctl.calls == [
        ["systemctl", "--user", "show-environment"],
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", SERVER_UNIT],
    ]


def test_install_refuses_to_replace_foreign_unit(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    unit_path = unit_dir / SERVER_UNIT
    foreign_content = "[Service]\nExecStart=/bin/false\n"
    unit_path.write_text(foreign_content)
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="not managed"):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert unit_path.read_text(encoding="utf-8") == foreign_content


@pytest.mark.parametrize(
    ("invalid_optional", "reason"),
    [
        ("foreign", "not managed"),
        ("dangling_symlink", "unit path is unsafe"),
    ],
)
def test_install_preflight_rejects_obsolete_foreign_unit_before_server_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_optional: str,
    reason: str,
) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    server = unit_dir / SERVER_UNIT
    previous = MANAGED_MARKER + "\noriginal trusted unit\n"
    server.write_text(previous, encoding="utf-8")
    server.chmod(0o600)
    obsolete = unit_dir / TUNNEL_UNIT
    if invalid_optional == "foreign":
        obsolete.write_text("[Service]\nExecStart=/bin/false\n", encoding="utf-8")
    else:
        obsolete.symlink_to(tmp_path / "not-existing")
    systemctl = FakeSystemctl()
    monkeypatch.setattr("runner_mcp.cron_autostart.cron_available", lambda: False)

    with pytest.raises(AutostartError, match=reason):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
            activation_permit=AutostartActivationPermit.clear(),
        )

    assert server.read_text(encoding="utf-8") == previous
    if invalid_optional == "foreign":
        assert obsolete.exists()
    else:
        assert obsolete.is_symlink()
    assert systemctl.calls == [["systemctl", "--user", "show-environment"]]


def test_write_managed_unit_uses_private_atomic_replace(tmp_path: Path) -> None:
    target = tmp_path / SERVER_UNIT
    target.write_text(MANAGED_MARKER + "\nold\n", encoding="utf-8")
    target.chmod(0o644)

    _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert target.read_text(encoding="utf-8") == MANAGED_MARKER + "\nnew\n"
    assert target.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.glob(f".{SERVER_UNIT}.*.tmp")) == []


@pytest.mark.parametrize("failure_point", ["fsync", "replace"])
def test_write_managed_unit_bounded_failure_preserves_previous_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    target = tmp_path / SERVER_UNIT
    previous = MANAGED_MARKER + "\nold\n"
    target.write_text(previous, encoding="utf-8")
    target.chmod(0o600)
    sensitive = str(tmp_path / "private-sensitive-value")

    def fail(*_args: object) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, failure_point, fail)

    with pytest.raises(AutostartError) as captured:
        _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert str(captured.value) == "autostart unit could not be written"
    assert sensitive not in str(captured.value)
    assert target.read_text(encoding="utf-8") == previous
    assert list(tmp_path.glob(f".{SERVER_UNIT}.*.tmp")) == []


def test_write_managed_unit_symlink_swap_cannot_touch_referent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / SERVER_UNIT
    target.write_text(MANAGED_MARKER + "\nold\n", encoding="utf-8")
    referent = tmp_path / "foreign.service"
    referent.write_text("foreign\n", encoding="utf-8")
    referent.chmod(0o640)
    referent_mode = referent.stat().st_mode & 0o777
    real_replace = secure_io_module.atomic_replace_private

    def swap_to_symlink_then_replace(path: Path, content: bytes) -> None:
        path.unlink()
        path.symlink_to(referent)
        real_replace(path, content)

    monkeypatch.setattr(
        autostart_module,
        "atomic_replace_private",
        swap_to_symlink_then_replace,
    )

    with pytest.raises(AutostartError, match="could not be written"):
        _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert target.is_symlink()
    assert referent.read_text(encoding="utf-8") == "foreign\n"
    assert referent.stat().st_mode & 0o777 == referent_mode


def test_status_is_safe_and_normalized(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text(MANAGED_MARKER + "\n")
    (unit_dir / SERVER_UNIT).chmod(0o600)
    systemctl = FakeSystemctl()
    systemctl.enabled.add(SERVER_UNIT)
    systemctl.active.add(SERVER_UNIT)

    rows = user_service_status(unit_dir=unit_dir, runner=systemctl)

    assert [row.public_dict() for row in rows] == [
        {
            "component": "server",
            "installed": True,
            "enabled": True,
            "active": True,
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


def test_install_refuses_symlinked_parent_without_unit_writes(tmp_path: Path) -> None:
    real = tmp_path / "real"
    (real / "systemd").mkdir(parents=True)
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    unit_dir = linked / "systemd" / "user"
    systemctl = FakeSystemctl()
    paths, executable = _private_config(tmp_path)
    with pytest.raises(AutostartError, match="must not be a symlink"):
        install_user_services(
            config_dir=paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
            activation_permit=AutostartActivationPermit.clear(),
        )
    assert not (real / "systemd" / "user").exists()
    assert systemctl.calls == [["systemctl", "--user", "show-environment"]]


def test_remove_refuses_symlinked_parent_without_systemctl_or_writes(tmp_path: Path) -> None:
    real = tmp_path / "real"
    unit_dir = real / "systemd" / "user"
    unit_dir.mkdir(parents=True)
    original = MANAGED_MARKER + "\n[Service]\nExecStart=/bin/true\n"
    target = unit_dir / SERVER_UNIT
    target.write_text(original, encoding="utf-8")
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    systemctl = FakeSystemctl()
    with pytest.raises(AutostartError, match="unit directory is unavailable"):
        remove_user_services(unit_dir=linked / "systemd" / "user", runner=systemctl)
    assert target.read_text(encoding="utf-8") == original
    assert systemctl.calls == []


def test_remove_absent_user_unit_tree_is_noop_without_writes(tmp_path: Path) -> None:
    missing = tmp_path / "absent" / "units"
    systemctl = FakeSystemctl()
    assert remove_user_services(unit_dir=missing, runner=systemctl) == []
    assert not missing.exists()
    assert not missing.parent.exists()
    assert systemctl.calls == []


def test_remove_only_deletes_runner_mcp_managed_units(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    managed = unit_dir / SERVER_UNIT
    managed.write_text(MANAGED_MARKER + "\n")
    managed.chmod(0o600)
    systemctl = FakeSystemctl()

    removed = remove_user_services(unit_dir=unit_dir, runner=systemctl)

    assert removed == [SERVER_UNIT]
    assert not managed.exists()
    assert ["systemctl", "--user", "disable", "--now", SERVER_UNIT] in systemctl.calls
    assert systemctl.calls[-1] == ["systemctl", "--user", "daemon-reload"]


def test_remove_preserves_unit_when_systemctl_disable_fails(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    target = unit_dir / SERVER_UNIT
    original = MANAGED_MARKER + "\n[Service]\nExecStart=/bin/true\n"
    target.write_text(original, encoding="utf-8")

    class RejectDisable(FakeSystemctl):
        def __call__(self, argv, **kwargs):
            result = super().__call__(argv, **kwargs)
            if argv[2:4] == ["disable", "--now"]:
                return subprocess.CompletedProcess(argv, 1, "", "synthetic failure")
            return result

    systemctl = RejectDisable()
    with pytest.raises(AutostartError, match="service operation failed"):
        remove_user_services(unit_dir=unit_dir, runner=systemctl)
    assert target.read_text(encoding="utf-8") == original
    assert systemctl.calls == [
        ["systemctl", "--user", "show-environment"],
        ["systemctl", "--user", "disable", "--now", SERVER_UNIT],
    ]


def test_remove_refuses_foreign_unit(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text("[Unit]\nDescription=foreign\n")
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="not managed"):
        remove_user_services(unit_dir=unit_dir, runner=systemctl)


def test_install_without_clear_permit_has_zero_systemd_or_file_mutation(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "must-not-exist"
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="activation is blocked"):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
        )

    assert systemctl.calls == []
    assert not unit_dir.exists()


def test_fabric_live_overview_unit_is_optional_and_contains_no_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, executable = _private_config(tmp_path)
    monkeypatch.setattr(
        autostart_module,
        "fabric_live_overview_configured",
        lambda _config_dir: True,
    )

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert FABRIC_LIVE_OVERVIEW_UNIT in units
    content = units[FABRIC_LIVE_OVERVIEW_UNIT]
    assert "fabric-live-overview" in content
    assert " run" in content
    assert "credential" not in content.casefold()
    assert "token" not in content.casefold()


def test_fabric_agent_qualification_unit_is_optional_and_contains_no_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, executable = _private_config(tmp_path)
    monkeypatch.setattr(
        autostart_module,
        "fabric_agent_qualification_configured",
        lambda _config_dir: True,
    )

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert FABRIC_AGENT_QUALIFICATION_UNIT in units
    content = units[FABRIC_AGENT_QUALIFICATION_UNIT]
    assert "fabric-agent-qualification" in content
    assert " run" in content
    assert "credential" not in content.casefold()
    assert "token" not in content.casefold()


def test_managed_user_units_refuse_dangling_symlink(tmp_path: Path) -> None:
    """A broken peer unit must not look absent to the cron installer."""
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    link = unit_dir / SERVER_UNIT
    referent = tmp_path / "missing-foreign-unit"
    link.symlink_to(referent)

    with pytest.raises(AutostartError, match="unit path is unsafe"):
        autostart_module.has_managed_user_units(unit_dir=unit_dir)

    assert link.is_symlink()
    assert not referent.exists()


@pytest.mark.parametrize("kind", ["foreign", "dangling_symlink"])
def test_remove_user_services_preflights_every_unit_before_mutation(
    tmp_path: Path,
    kind: str,
) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    server = unit_dir / SERVER_UNIT
    original = MANAGED_MARKER + "\n[Service]\nExecStart=/bin/true\n"
    server.write_text(original, encoding="utf-8")
    optional = unit_dir / TUNNEL_UNIT
    if kind == "foreign":
        optional.write_text("[Service]\nExecStart=/bin/false\n", encoding="utf-8")
    else:
        optional.symlink_to(tmp_path / "unresolved")
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="not managed|unit path is unsafe"):
        remove_user_services(unit_dir=unit_dir, runner=systemctl)

    assert server.read_text(encoding="utf-8") == original
    assert optional.is_symlink() if kind == "dangling_symlink" else optional.is_file()
    assert systemctl.calls == [["systemctl", "--user", "show-environment"]]


def test_systemd_user_status_does_not_create_absent_unit_tree(
    tmp_path: Path,
) -> None:
    """Read-only inspection must never bootstrap files or call systemctl."""
    unit_dir = tmp_path / "uncreated" / "units"
    systemctl = FakeSystemctl()

    rows = user_service_status(unit_dir=unit_dir, runner=systemctl)

    assert len(rows) == len(autostart_module.KNOWN_UNITS)
    assert all(not row.installed and not row.enabled and not row.active for row in rows)
    assert not unit_dir.exists()
    assert not unit_dir.parent.exists()
    assert systemctl.calls == []


@pytest.mark.parametrize("target_type", ["file", "symlink", "dangling_symlink"])
def test_systemd_user_status_rejects_unsafe_unit_dir_without_writes(
    tmp_path: Path,
    target_type: str,
) -> None:
    """Foreign entries cannot be overwritten or silently reclassified."""
    unit_dir = tmp_path / "units"
    referent = tmp_path / "referent"
    if target_type == "file":
        unit_dir.write_text("foreign", encoding="utf-8")
    elif target_type == "symlink":
        referent.mkdir()
        unit_dir.symlink_to(referent, target_is_directory=True)
    else:
        unit_dir.symlink_to(referent, target_is_directory=True)
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="unit directory is unavailable"):
        user_service_status(unit_dir=unit_dir, runner=systemctl)

    assert systemctl.calls == []
    if target_type == "file":
        assert unit_dir.read_text(encoding="utf-8") == "foreign"
    else:
        assert unit_dir.is_symlink()
        assert unit_dir.readlink() == referent
        assert not (referent / SERVER_UNIT).exists()


def test_systemd_user_status_rejects_dangling_unit_symlink_without_writes(
    tmp_path: Path,
) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    link = unit_dir / SERVER_UNIT
    referent = tmp_path / "foreign"
    link.symlink_to(referent)
    systemctl = FakeSystemctl()
    with pytest.raises(AutostartError, match="unit path is unsafe"):
        user_service_status(unit_dir=unit_dir, runner=systemctl)
    assert link.is_symlink()
    assert not referent.exists()
    # The read-only status may probe the user manager; it never modifies it.
    assert all("--now" not in command for command in systemctl.calls)


def test_systemd_user_status_does_not_misreport_down_when_session_bus_unreachable(
    tmp_path: Path,
) -> None:
    """`sudo -iu` may have unit files but no XDG_RUNTIME_DIR/user bus."""

    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text(MANAGED_MARKER + "\n")
    (unit_dir / SERVER_UNIT).chmod(0o600)

    class DisconnectedSystemd(FakeSystemctl):
        def __call__(self, argv, **kwargs):
            super().__call__(argv, **kwargs)
            if argv[2:] == ["show-environment"]:
                return subprocess.CompletedProcess(argv, 1, "", "private session error")
            raise AssertionError("Must fail closed before reading per-unit states")

    systemctl = DisconnectedSystemd()
    with pytest.raises(AutostartError, match="user manager is unreachable"):
        user_service_status(unit_dir=unit_dir, runner=systemctl)
    assert systemctl.calls == [["systemctl", "--user", "show-environment"]]


def test_systemd_user_status_can_report_genuinely_disabled_services(
    tmp_path: Path,
) -> None:
    """An accessible user manager may correctly report an inactive unit."""
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text(MANAGED_MARKER + "\n")
    (unit_dir / SERVER_UNIT).chmod(0o600)

    systemctl = FakeSystemctl()
    rows = user_service_status(unit_dir=unit_dir, runner=systemctl)
    server = next(row for row in rows if row.component == "server")

    assert server.installed
    assert not server.enabled
    assert not server.active
    assert systemctl.calls[0] == ["systemctl", "--user", "show-environment"]

# Fixed source-only A7 handoff; no service, timer, update or restart is triggered.
_OLD_QUALIFICATION_LAUNCHER = (
    "/home/fixture/.local/share/runner-mcp-candidates/"
    "0.1.38-old/bin/runner-mcp"
)
_NEW_QUALIFICATION_LAUNCHER = (
    "/home/fixture/.local/share/runner-mcp-candidates/"
    "0.1.131-new/install/venv/bin/runner-mcp"
)


def _qualification_override() -> bytes:
    return (
        "# old private override remains untouched\n"
        "[Service]\n"
        "ExecStart=\n"
        "ExecStart=" + _OLD_QUALIFICATION_LAUNCHER
        + " --config-dir /home/fixture/.config/runner-mcp"
        + " fabric-agent-qualification run\n"
    ).encode()


def _plan_qualification_override(original: bytes, **kwargs):
    return plan_qualification_override_swap(
        original_override=original,
        expected_original_sha256=kwargs.get(
            "expected_original_sha256", hashlib.sha256(original).hexdigest()
        ),
        original_launcher=kwargs.get(
            "original_launcher", _OLD_QUALIFICATION_LAUNCHER
        ),
        candidate_launcher=kwargs.get(
            "candidate_launcher", _NEW_QUALIFICATION_LAUNCHER
        ),
    )


def test_qualification_override_plan_exact_bytes_reversible_without_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _qualification_override()
    # Prove an in-memory-only plan: any attempted filesystem/service action is a defect.
    def forbidden(*args, **kwargs):
        raise AssertionError("planner must not perform any host operation")

    monkeypatch.setattr(autostart_module.subprocess, "run", forbidden)
    plan = _plan_qualification_override(original)
    assert plan.original_override == original
    assert plan.original_sha256 == hashlib.sha256(original).hexdigest()
    assert plan.candidate_sha256 == hashlib.sha256(plan.candidate_override).hexdigest()
    assert plan.change_scope == "one_fixed_execstart_executable"
    assert plan.candidate_override.count(b"ExecStart=") == 2
    assert plan.candidate_override == original.replace(
        _OLD_QUALIFICATION_LAUNCHER.encode(),
        _NEW_QUALIFICATION_LAUNCHER.encode(),
        1,
    )
    assert plan.candidate_override.replace(
        _NEW_QUALIFICATION_LAUNCHER.encode(),
        _OLD_QUALIFICATION_LAUNCHER.encode(),
        1,
    ) == original
    assert plan.activation_authorized is False
    assert plan.rollback_verified is False
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.replace(b"ExecStart=\n", b""),
        lambda s: s.replace(b"ExecStart=\n", b"ExecStart=\nExecStart=\n"),
        lambda s: s.replace(b"[Service]\n", b"[Service]\nEnvironment=X=y\n"),
        lambda s: s.replace(b"[Service]\n", b"[Install]\n"),
        lambda s: s.replace(b"fabric-agent-qualification run", b"server run"),
        lambda s: s.replace(b" --config-dir ", b" --config-dir /other --config-dir "),
        lambda s: s.replace(b" fabric-agent-qualification run", b"; restart run"),
        lambda s: s.replace(b"ExecStart=", b"ExecStartPre=", 1),
        lambda s: s + b"ExecStart=/bin/sh\n",
        lambda s: s[:-1],
        lambda s: s.replace(b"\n", b"\r\n"),
        lambda s: s + b"\x00",
        lambda s: s + b"\xff",
    ],
)
def test_qualification_override_plan_rejects_extra_or_unsafe_directives(
    mutation,
) -> None:
    original = mutation(_qualification_override())
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(original)


@pytest.mark.parametrize(
    "bad_launcher",
    [
        "runner-mcp",
        "/home/fixture/../escape/bin/runner-mcp",
        "/home/fixture//bad/bin/runner-mcp",
        "/home/fixture/bad;reboot/bin/runner-mcp",
        "/home/fixture/$HOME/bin/runner-mcp",
        "/home/fixture/%n/bin/runner-mcp",
        "/home/fixture/x y/bin/runner-mcp",
        "/home/fixture/bin/runner-mcp\\nExecStart=/bin/sh",
        "/home/fixture/bin/runner-mcp-other",
    ],
)
def test_qualification_override_plan_rejects_unqualified_candidate_path(
    bad_launcher: str,
) -> None:
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(
            _qualification_override(), candidate_launcher=bad_launcher
        )


def test_qualification_override_plan_denies_unpinned_or_same_release() -> None:
    original = _qualification_override()
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(
            original, expected_original_sha256="0" * 64
        )
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(
            original, candidate_launcher=_OLD_QUALIFICATION_LAUNCHER
        )
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(
            original, original_launcher=_NEW_QUALIFICATION_LAUNCHER
        )


@pytest.mark.parametrize("invalid", [b"", b"A" * 8193, "text", None])
def test_qualification_override_plan_requires_bounded_bytes(invalid) -> None:
    with pytest.raises(AutostartError, match="override plan is unqualified"):
        _plan_qualification_override(invalid)
