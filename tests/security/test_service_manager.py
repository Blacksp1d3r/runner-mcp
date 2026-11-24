import os
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from runner_mcp.config import ProjectConfig, ProjectRegistry, ServiceConfig
from runner_mcp.host_platform import HostPlatform
from runner_mcp.local_process_facts import LinuxProcessFacts, LocalProcessFactsUnavailable
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)
from runner_mcp.service_manager import (
    RegisteredSelfListenerObservation,
    RegisteredSelfProcessObservation,
    RegisteredServiceObservation,
    ServiceManager,
    ServiceManagerError,
    ServiceState,
    SystemdUserBackend,
)


class FakeBackend:
    def __init__(self) -> None:
        self.actions: list[tuple[str, str]] = []
        self.status_units: list[str] = []
        self.state = ServiceState("loaded", "active", "running")

    def status(self, unit: str) -> ServiceState:
        self.status_units.append(unit)
        return self.state

    def action(self, unit: str, action: str) -> None:
        self.actions.append((unit, action))


class FakeHealth:
    def __init__(self, result: str = "healthy") -> None:
        self.result = result

    def check(self, service: ServiceConfig) -> str:
        return self.result if service.health_url is not None else "not_configured"


def registry_with_service(
    root: Path,
    *,
    allow_start: bool = False,
    allow_stop: bool = False,
    allow_restart: bool = True,
    health_url: str | None = "http://127.0.0.1:9999/health",
) -> ProjectRegistry:
    root.mkdir(parents=True, exist_ok=True)
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
                        allow_start=allow_start,
                        allow_stop=allow_stop,
                        allow_restart=allow_restart,
                    )
                },
            )
        }
    )


def guard(tmp_path: Path, *, stopped: bool = False) -> OperatorSafetyGuard:
    stop_file = tmp_path / "operator.stop"
    if stopped:
        stop_file.write_text("stop\n", encoding="utf-8")
    return OperatorSafetyGuard(
        stop_file=stop_file,
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def test_service_listing_hides_private_unit_and_health_url(tmp_path: Path) -> None:
    registry = registry_with_service(tmp_path / "project")
    manager = ServiceManager(
        registry=registry,
        safety=guard(tmp_path),
        backend=FakeBackend(),
        health_checker=FakeHealth(),
    )

    listed = manager.list_services("demo")

    assert listed == [
        {
            "name": "web",
            "can_start": False,
            "can_stop": False,
            "can_restart": True,
            "log_read": False,
            "health_check": True,
        }
    ]
    assert "private-web.service" not in repr(listed)
    assert "127.0.0.1" not in repr(listed)


def test_status_returns_alias_only(tmp_path: Path) -> None:
    registry = registry_with_service(tmp_path / "project")
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry,
        safety=guard(tmp_path),
        backend=backend,
        health_checker=FakeHealth(),
    )

    result = manager.status("demo", "web")

    assert result["service"] == "web"
    assert result["active_state"] == "active"
    assert result["health"] == "healthy"
    assert backend.status_units == ["private-web.service"]
    assert "private-web.service" not in repr(result)


def test_read_only_status_remains_available_during_emergency_stop(tmp_path: Path) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path, stopped=True),
        backend=FakeBackend(),
        health_checker=FakeHealth(),
    )

    result = manager.status("demo", "web")

    assert result["active_state"] == "active"


def test_restart_requires_explicit_permission_and_uses_private_unit(tmp_path: Path) -> None:
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project", allow_restart=True),
        safety=guard(tmp_path),
        backend=backend,
        health_checker=FakeHealth(),
    )

    result = manager.action("demo", "web", "restart")

    assert backend.actions == [("private-web.service", "restart")]
    assert result["service"] == "web"
    assert result["action"] == "restart"
    assert "private-web.service" not in repr(result)


def test_disallowed_start_never_reaches_backend(tmp_path: Path) -> None:
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project", allow_start=False),
        safety=guard(tmp_path),
        backend=backend,
        health_checker=FakeHealth(),
    )

    with pytest.raises(ServiceManagerError, match="not allowed"):
        manager.action("demo", "web", "start")

    assert backend.actions == []


def test_emergency_stop_blocks_mutating_service_action(tmp_path: Path) -> None:
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project", allow_restart=True),
        safety=guard(tmp_path, stopped=True),
        backend=backend,
        health_checker=FakeHealth(),
    )

    with pytest.raises(OperatorStopActive):
        manager.action("demo", "web", "restart")

    assert backend.actions == []


def test_unknown_service_alias_is_rejected(tmp_path: Path) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path),
        backend=FakeBackend(),
        health_checker=FakeHealth(),
    )

    with pytest.raises(ServiceManagerError, match="Unknown or disabled service"):
        manager.status("demo", "missing")


def test_service_unit_rejects_command_injection_characters() -> None:
    with pytest.raises(ValidationError, match="unsupported characters"):
        ServiceConfig(unit="demo.service;touch")


def test_service_health_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ValidationError, match="must not contain credentials"):
        ServiceConfig(unit="demo.service", health_url="https://user:pass@example.invalid/health")


def test_systemd_backend_uses_fixed_argument_array_without_shell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "systemctl"
    executable.write_text("test\n", encoding="utf-8")
    executable.chmod(0o755)
    calls: list[tuple[list[str], dict]] = []

    def fake_run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="LoadState=loaded\nActiveState=active\nSubState=running\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    backend = SystemdUserBackend(executable=executable)

    state = backend.status("demo.service")

    assert state.active_state == "active"
    arguments, kwargs = calls[0]
    assert arguments[:3] == [str(executable), "--user", "show"]
    assert "demo.service" in arguments
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["timeout"] == 10.0


def test_systemd_backend_does_not_return_raw_failure_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "systemctl"
    executable.write_text("test\n", encoding="utf-8")
    executable.chmod(0o755)

    def fake_run(arguments, **kwargs):
        return subprocess.CompletedProcess(
            arguments,
            1,
            stdout="",
            stderr="private-unit-name and internal details",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    backend = SystemdUserBackend(executable=executable)

    with pytest.raises(ServiceManagerError) as exc:
        backend.status("demo.service")

    assert "private-unit-name" not in str(exc.value)
    assert "internal details" not in str(exc.value)


def test_systemd_backend_rejects_unknown_action_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "systemctl"
    executable.write_text("test\n", encoding="utf-8")
    executable.chmod(0o755)
    called = False

    def fake_run(arguments, **kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    backend = SystemdUserBackend(executable=executable)

    with pytest.raises(ServiceManagerError, match="Unsupported"):
        backend.action("demo.service", "reload-or-something")

    assert called is False


@pytest.mark.parametrize(
    ("load", "active", "status", "present", "running"),
    [
        ("loaded", "active", "observed", True, True),
        ("loaded", "inactive", "observed", True, False),
        ("loaded", "failed", "observed", True, False),
        ("loaded", "activating", "observed", True, None),
        ("not-found", "inactive", "observed", False, None),
        ("not-found", "active", "unknown", None, None),
        ("masked", "inactive", "unknown", None, None),
        ("loaded", "unexpected", "unknown", None, None),
    ],
)
def test_registered_service_presence_maps_only_known_systemd_states(
    tmp_path: Path, load: str, active: str, status: str,
    present: bool | None, running: bool | None,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState(load, active, "unused-private-substate")

    class NoHealth:
        def check(self, _service):
            pytest.fail("presence observation must not perform an HTTP health check")

    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path, stopped=True),
        backend=backend,
        health_checker=NoHealth(),
    )
    result = manager.observe_registered_service("demo", "web")
    assert result == RegisteredServiceObservation(
        project="demo", service="web", status=status,
        present=present, active=running,
    )
    assert backend.status_units == ["private-web.service"]
    assert backend.actions == []
    assert "private-web.service" not in repr(result)
    assert "unused-private" not in repr(result)


def test_registered_service_presence_rejects_undeclared_alias_before_read(
    tmp_path: Path,
) -> None:
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    with pytest.raises(ServiceManagerError, match="Unknown or disabled service"):
        manager.observe_registered_service("demo", "undeclared")
    assert backend.status_units == []
    assert backend.actions == []


def test_registered_service_presence_returns_unknown_when_backend_fails(
    tmp_path: Path,
) -> None:
    class DeniedBackend(FakeBackend):
        def status(self, _unit):
            raise ServiceManagerError("private backend failure")

    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=DeniedBackend(),
    )
    observation = manager.observe_registered_service("demo", "web")
    assert observation.status == "unknown"
    assert observation.present is None and observation.active is None
    assert "private backend failure" not in repr(observation)


def test_registered_service_presence_without_linux_backend_is_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.host_platform import HostPlatform

    monkeypatch.setattr(
        "runner_mcp.service_manager.detect_host_platform",
        lambda: HostPlatform.UNSUPPORTED,
    )
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=None,
    )
    observation = manager.observe_registered_service("demo", "web")
    assert observation.status == "unsupported"
    assert observation.present is None and observation.active is None
    assert manager.backend is None


def test_registered_service_presence_missing_systemctl_is_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runner_mcp.host_platform import HostPlatform

    monkeypatch.setattr(
        "runner_mcp.service_manager.detect_host_platform",
        lambda: HostPlatform.LINUX,
    )

    def no_systemctl():
        raise ServiceManagerError("systemctl missing")

    monkeypatch.setattr("runner_mcp.service_manager._detect_systemctl", no_systemctl)
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=None,
    )
    observation = manager.observe_registered_service("demo", "web")
    assert observation.status == "unsupported"
    assert observation.present is None and observation.active is None
    assert manager.backend is None


def test_registered_self_process_only_when_systemd_mainpid_is_current_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState("loaded", "active", "running", os.getpid())
    read_count = 0

    def read_fake() -> LinuxProcessFacts:
        nonlocal read_count
        read_count += 1
        return LinuxProcessFacts(
            boot_id="12345678-1234-1234-1234-123456789abc",
            process_id=os.getpid(),
            start_ticks=98444,
            network_namespace_inode=4026531840,
        )

    monkeypatch.setattr("runner_mcp.service_manager.read_current_linux_process", read_fake)
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path, stopped=True),
        backend=backend,
        health_checker=FakeHealth(),
    )
    observation = manager.observe_registered_self_process("demo", "web")
    assert observation == RegisteredSelfProcessObservation(
        project="demo", service="web", status="observed",
        generation=f"12345678-1234-1234-1234-123456789abc:{os.getpid()}:98444",
        network_namespace_inode=4026531840,
    )
    assert backend.status_units == ["private-web.service", "private-web.service"]
    assert backend.actions == []
    assert read_count == 2
    assert "private-web.service" not in repr(observation)


def test_registered_self_process_other_service_pid_never_reads_proc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState("loaded", "active", "running", os.getpid() + 100)

    def deny_proc():
        pytest.fail("must not read another unit's process")

    monkeypatch.setattr("runner_mcp.service_manager.read_current_linux_process", deny_proc)
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    assert manager.observe_registered_self_process("demo", "web").status == "unknown"
    assert backend.status_units == ["private-web.service"]
    assert backend.actions == []


@pytest.mark.parametrize("mainpid", [None, 0, True, "123", -1])
def test_registered_self_process_invalid_mainpid_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mainpid,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState("loaded", "active", "running", mainpid)
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_linux_process",
        lambda: pytest.fail("untrusted systemd pid must not reach proc"),
    )
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    assert manager.observe_registered_self_process("demo", "web").status == "unknown"


def test_registered_self_process_fails_on_systemd_mainpid_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ChangingBackend(FakeBackend):
        def status(self, unit):
            result = super().status(unit)
            if len(self.status_units) == 2:
                return ServiceState("loaded", "active", "running", os.getpid() + 1)
            return result

    backend = ChangingBackend()
    backend.state = ServiceState("loaded", "active", "running", os.getpid())
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_linux_process",
        lambda: LinuxProcessFacts(
            "12345678-1234-1234-1234-123456789abc", os.getpid(), 88
        ),
    )
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    obs = manager.observe_registered_self_process("demo", "web")
    assert obs.status == "unknown"
    assert obs.generation is None
    assert len(backend.status_units) == 2


@pytest.mark.parametrize("race", ["startticks", "network_namespace"])
def test_registered_self_process_pid_or_namespace_race_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, race: str,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState("loaded", "active", "running", os.getpid())
    calls = 0

    def racing_reader() -> LinuxProcessFacts:
        nonlocal calls
        calls += 1
        return LinuxProcessFacts(
            "12345678-1234-1234-1234-123456789abc",
            os.getpid(),
            88 + (calls == 2 and race == "startticks"),
            network_namespace_inode=1840 + (calls == 2 and race == "network_namespace"),
        )

    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_linux_process", racing_reader
    )
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    obs = manager.observe_registered_self_process("demo", "web")
    assert obs.status == "unknown"
    assert obs.generation is None


def test_registered_self_process_missing_kernel_evidence_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeBackend()
    backend.state = ServiceState("loaded", "active", "running", os.getpid())

    def denied():
        raise LocalProcessFactsUnavailable("private kernel error")

    monkeypatch.setattr("runner_mcp.service_manager.read_current_linux_process", denied)
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    obs = manager.observe_registered_self_process("demo", "web")
    assert obs.status == "unknown"
    assert "private kernel error" not in repr(obs)


def test_registered_self_process_missing_systemd_is_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.service_manager.detect_host_platform", lambda: HostPlatform.LINUX
    )

    def unavailable():
        raise ServiceManagerError("no systemd")

    monkeypatch.setattr("runner_mcp.service_manager._detect_systemctl", unavailable)
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=None,
    )
    assert manager.observe_registered_self_process("demo", "web").status == "unsupported"


def test_registered_self_process_nonlinux_does_not_access_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.service_manager.detect_host_platform", lambda: HostPlatform.WINDOWS
    )
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    assert manager.observe_registered_self_process("demo", "web").status == "unsupported"
    assert backend.status_units == []


def test_registered_self_process_unknown_alias_fails_before_systemd(
    tmp_path: Path,
) -> None:
    backend = FakeBackend()
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=backend,
    )
    with pytest.raises(ServiceManagerError, match="Unknown or disabled service"):
        manager.observe_registered_self_process("demo", "foreign")
    assert backend.status_units == []


@pytest.mark.parametrize("pid_token", ["abc", "true", "-1", "999999999999999999", "0"])
def test_systemd_mainpid_invalid_is_not_exposed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pid_token: str,
) -> None:
    executable = tmp_path / "systemctl"
    executable.write_text("fixture\n", encoding="utf-8")
    executable.chmod(0o755)

    def fixed_show(arguments, **kwargs):
        assert "--property=MainPID" in arguments
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(
            arguments, 0,
            stdout=(
                "LoadState=loaded\nActiveState=active\n"
                "SubState=running\nMainPID=" + pid_token + "\n"
            ),
            stderr="private hidden content",
        )

    monkeypatch.setattr(subprocess, "run", fixed_show)
    state = SystemdUserBackend(executable=executable).status("registered.service")
    assert state.main_pid is None


def test_registered_self_listener_positive_rechecks_same_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path, stopped=True),
        backend=FakeBackend(),
    )
    self_fact = RegisteredSelfProcessObservation(
        project="demo", service="web", status="observed",
        generation="fixture-boot:123:456", network_namespace_inode=1840
    )
    calls = []

    def own_process(*args):
        calls.append("process")
        return self_fact

    def kernel_listeners():
        calls.append("tcp")
        return (("tcp4", 8080),)

    monkeypatch.setattr(manager, "observe_registered_self_process", own_process)
    monkeypatch.setattr("runner_mcp.service_manager.read_current_self_tcp_listeners", kernel_listeners)
    obs = manager.observe_registered_self_listeners("demo", "web")
    assert obs == RegisteredSelfListenerObservation(
        project="demo", service="web", status="observed",
        generation=self_fact.generation, network_namespace_inode=1840,
        listeners=(("tcp4", 8080),),
    )
    assert calls == ["process", "tcp", "process"]


def test_registered_self_listener_different_pid_or_no_systemd_skips_tcp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=FakeBackend(),
    )
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_self_tcp_listeners",
        lambda: pytest.fail("foreign or unsupported process must not read /proc/self/net"),
    )
    for state in ("unknown", "unsupported"):
        monkeypatch.setattr(
            manager, "observe_registered_self_process",
            lambda *_args: RegisteredSelfProcessObservation(
                project="demo", service="web", status=state
            ),
        )
        assert manager.observe_registered_self_listeners("demo", "web").status == state


@pytest.mark.parametrize("listener_result", [None, ()])
def test_registered_self_listener_missing_or_empty_kernel_evidence_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, listener_result
) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=FakeBackend(),
    )
    monkeypatch.setattr(
        manager, "observe_registered_self_process",
        lambda *_args: RegisteredSelfProcessObservation(
            "demo", "web", "observed", "boot:10:20", 1840,
        ),
    )
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_self_tcp_listeners",
        lambda: listener_result,
    )
    obs = manager.observe_registered_self_listeners("demo", "web")
    assert obs.status == "unknown" and obs.listeners == ()


@pytest.mark.parametrize("difference", ["generation", "namespace", "status"])
def test_registered_self_listener_generation_race_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, difference: str
) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=FakeBackend(),
    )
    calls = 0

    def changing(*_args):
        nonlocal calls
        calls += 1
        return RegisteredSelfProcessObservation(
            "demo", "web",
            "unknown" if calls == 2 and difference == "status" else "observed",
            "boot:10:21" if calls == 2 and difference == "generation" else "boot:10:20",
            1841 if calls == 2 and difference == "namespace" else 1840,
        )

    monkeypatch.setattr(manager, "observe_registered_self_process", changing)
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_self_tcp_listeners",
        lambda: (("tcp6", 8080),),
    )
    obs = manager.observe_registered_self_listeners("demo", "web")
    assert obs.status == "unknown" and obs.listeners == ()


def test_registered_self_listener_unregistered_service_never_reads_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = ServiceManager(
        registry=registry_with_service(tmp_path / "project"),
        safety=guard(tmp_path), backend=FakeBackend(),
    )
    monkeypatch.setattr(
        "runner_mcp.service_manager.read_current_self_tcp_listeners",
        lambda: pytest.fail("unregistered alias cannot read netns"),
    )
    with pytest.raises(ServiceManagerError, match="Unknown or disabled service"):
        manager.observe_registered_self_listeners("demo", "missing")
