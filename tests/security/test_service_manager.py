import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from runner_mcp.config import ProjectConfig, ProjectRegistry, ServiceConfig
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)
from runner_mcp.service_manager import (
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
