from __future__ import annotations

import os
import subprocess
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import ProjectRegistry, ServiceConfig
from .host_platform import HostPlatform, detect_host_platform
from .local_process_facts import LocalProcessFactsUnavailable, read_current_linux_process
from .operational_safety import ActionClass, OperatorSafetyGuard


class ServiceManagerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceState:
    load_state: str
    active_state: str
    sub_state: str
    main_pid: int | None = None


@dataclass(frozen=True, slots=True)
class RegisteredServiceObservation:
    """Unverified unit presence from an already-allowlisted registry binding.

    Not a canonical asset fact, a service-PID witness, or loaded-code evidence.
    A caller cannot infer a listener or host identity from this observation.
    """

    project: str
    service: str
    status: str  # observed | unknown | unsupported
    present: bool | None
    active: bool | None
    source: str = "registered-service-backend"


@dataclass(frozen=True, slots=True)
class RegisteredSelfProcessObservation:
    """Local-only same-process generation for a registered user systemd unit.

    This is not an asset authority, loaded wheel attestation, or socket proof.
    """

    project: str
    service: str
    status: str  # observed | unknown | unsupported
    generation: str | None = None
    network_namespace_inode: int | None = None
    scope: str = "this_running_process_only"
    source: str = "linux:registered-systemd-self"


class ServiceBackend(Protocol):
    def status(self, unit: str) -> ServiceState: ...

    def action(self, unit: str, action: str) -> None: ...


class HealthChecker(Protocol):
    def check(self, service: ServiceConfig) -> str: ...


def _detect_systemctl() -> Path:
    for candidate in (Path("/usr/bin/systemctl"), Path("/bin/systemctl")):
        if (
            candidate.exists()
            and candidate.is_file()
            and not candidate.is_symlink()
            and os.access(candidate, os.X_OK)
        ):
            return candidate
    raise ServiceManagerError("systemctl is unavailable")


class SystemdUserBackend:
    def __init__(
        self,
        *,
        executable: Path | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.executable = executable or _detect_systemctl()
        self.timeout_seconds = timeout_seconds

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        try:
            completed = subprocess.run(
                [str(self.executable), "--user", *arguments],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ServiceManagerError("Service manager command failed") from exc

        if completed.returncode != 0:
            raise ServiceManagerError("Service manager command failed")
        return completed

    def status(self, unit: str) -> ServiceState:
        completed = self._run(
            [
                "show",
                unit,
                "--property=LoadState",
                "--property=ActiveState",
                "--property=SubState",
                "--property=MainPID",
                "--no-page",
            ]
        )
        values: dict[str, str] = {}
        for line in completed.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key] = value

        required = ("LoadState", "ActiveState", "SubState")
        if any(key not in values for key in required):
            raise ServiceManagerError("Service manager returned incomplete status")

        raw_pid = values.get("MainPID", "")
        main_pid = (
            int(raw_pid)
            if raw_pid.isascii() and raw_pid.isdecimal() and len(raw_pid) <= 12
            else 0
        )
        return ServiceState(
            load_state=values["LoadState"],
            active_state=values["ActiveState"],
            sub_state=values["SubState"],
            main_pid=main_pid if main_pid > 1 else None,
        )

    def action(self, unit: str, action: str) -> None:
        if action not in {"start", "stop", "restart"}:
            raise ServiceManagerError("Unsupported service action")
        self._run([action, unit])


class HttpHealthChecker:
    def check(self, service: ServiceConfig) -> str:
        if service.health_url is None:
            return "not_configured"

        request = urllib.request.Request(
            str(service.health_url),
            method="GET",
            headers={"User-Agent": "Runner-MCP-healthcheck"},
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=service.health_timeout_seconds,
            ) as response:
                status = int(response.status)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
        except (urllib.error.URLError, TimeoutError, OSError):
            return "unhealthy"

        return (
            "healthy"
            if status == service.health_expected_status
            else "unhealthy"
        )


class ServiceManager:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        backend: ServiceBackend | None = None,
        health_checker: HealthChecker | None = None,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.backend = backend
        self.health_checker = health_checker or HttpHealthChecker()
        self._locks: dict[tuple[str, str], threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _backend(self) -> ServiceBackend:
        if self.backend is None:
            if detect_host_platform() is not HostPlatform.LINUX:
                raise ServiceManagerError("Service backend is unavailable for this platform")
            self.backend = SystemdUserBackend()
        return self.backend

    def _service(
        self,
        project: str,
        alias: str,
    ) -> ServiceConfig:
        config = self.registry.projects.get(project)
        if config is None:
            raise ServiceManagerError("Unknown or disabled project")
        service = config.services.get(alias)
        if service is None:
            raise ServiceManagerError("Unknown or disabled service")
        return service

    def _lock_for(self, project: str, alias: str) -> threading.Lock:
        key = (project, alias)
        with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock

    def list_services(self, project: str) -> list[dict[str, object]]:
        config = self.registry.projects.get(project)
        if config is None:
            raise ServiceManagerError("Unknown or disabled project")

        return [
            {
                "name": alias,
                "can_start": service.allow_start,
                "can_stop": service.allow_stop,
                "can_restart": service.allow_restart,
                "log_read": service.allow_log_read,
                "health_check": service.health_url is not None,
            }
            for alias, service in sorted(config.services.items())
        ]

    def status(self, project: str, alias: str) -> dict[str, object]:
        service = self._service(project, alias)
        state = self._backend().status(service.unit)
        health = self.health_checker.check(service)
        return {
            "project": project,
            "service": alias,
            "load_state": state.load_state,
            "active_state": state.active_state,
            "sub_state": state.sub_state,
            "health": health,
        }

    def observe_registered_service(
        self, project: str, alias: str
    ) -> RegisteredServiceObservation:
        """Read only one configured unit via the existing bounded backend.

        No health URL, arbitrary systemd unit, service action, process lookup,
        host scan or caller-controlled asset ID is involved. The result is
        deliberately NOT a canonical F10 fact or process/listener attestation.
        """
        service = self._service(project, alias)

        def result(
            status: str, present: bool | None = None, active: bool | None = None
        ) -> RegisteredServiceObservation:
            return RegisteredServiceObservation(
                project=project, service=alias, status=status,
                present=present, active=active,
            )

        try:
            backend = self._backend()
        except ServiceManagerError:
            # Default backend is absent on non-Linux/no-systemd systems.
            return result("unsupported" if self.backend is None else "unknown")
        try:
            state = backend.status(service.unit)
        except ServiceManagerError:
            return result("unknown")
        if not isinstance(state, ServiceState):
            return result("unknown")
        if state.load_state == "not-found":
            # Contradictory systemd evidence is not an absence proof.
            if state.active_state != "inactive":
                return result("unknown")
            return result("observed", present=False)
        if state.load_state != "loaded":
            return result("unknown")
        if state.active_state == "active":
            return result("observed", present=True, active=True)
        if state.active_state in {"inactive", "failed"}:
            return result("observed", present=True, active=False)
        if state.active_state in {"activating", "deactivating", "reloading"}:
            return result("observed", present=True)
        return result("unknown")


    def observe_registered_self_process(
        self, project: str, alias: str
    ) -> RegisteredSelfProcessObservation:
        """Bind one allowlisted unit to ONLY the process serving this call.

        Systemd's MainPID must equal our own pid both before and after the
        kernel snapshot. No arbitrary PID selector, /proc traversal, socket
        scan, network probe or service action is authorized here. An observed
        generation is neither externally witnessed nor a loaded build digest.
        """
        service = self._service(project, alias)

        def wait(status: str) -> RegisteredSelfProcessObservation:
            return RegisteredSelfProcessObservation(
                project=project, service=alias, status=status,
            )

        if detect_host_platform() is not HostPlatform.LINUX:
            return wait("unsupported")
        try:
            backend = self._backend()
        except ServiceManagerError:
            return wait("unsupported" if self.backend is None else "unknown")
        try:
            pid = os.getpid()
            before = backend.status(service.unit)
            if (
                not isinstance(before, ServiceState)
                or before.load_state != "loaded"
                or before.active_state != "active"
                or type(before.main_pid) is not int
                or before.main_pid != pid
            ):
                return wait("unknown")
            first = read_current_linux_process()
            after = backend.status(service.unit)
            second = read_current_linux_process()
            if (
                not isinstance(after, ServiceState)
                or after.load_state != "loaded"
                or after.active_state != "active"
                or after.main_pid != pid
                or first.process_id != pid
                or second.process_id != pid
                or first.generation != second.generation
                or first.network_namespace_inode != second.network_namespace_inode
            ):
                return wait("unknown")
            return RegisteredSelfProcessObservation(
                project=project,
                service=alias,
                status="observed",
                generation=first.generation,
                network_namespace_inode=first.network_namespace_inode,
            )
        except (ServiceManagerError, LocalProcessFactsUnavailable, OSError, ValueError):
            return wait("unknown")


    @staticmethod
    def _action_allowed(service: ServiceConfig, action: str) -> bool:
        if action == "start":
            return service.allow_start
        if action == "stop":
            return service.allow_stop
        if action == "restart":
            return service.allow_restart
        return False

    def action(
        self,
        project: str,
        alias: str,
        action: str,
    ) -> dict[str, object]:
        service = self._service(project, alias)
        if action not in {"start", "stop", "restart"}:
            raise ServiceManagerError("Unsupported service action")
        if not self._action_allowed(service, action):
            raise ServiceManagerError("Service action is not allowed")

        project_config = self.registry.projects.get(project)
        if project_config is None:
            raise ServiceManagerError("Unknown or disabled project")
        self.safety.assert_project_action_allowed(
            ActionClass.SERVICE,
            environment=project_config.environment,
        )

        lock = self._lock_for(project, alias)
        if not lock.acquire(blocking=False):
            raise ServiceManagerError("Another service action is already in progress")
        try:
            # Re-check immediately before the mutating call.
            self.safety.assert_project_action_allowed(
                ActionClass.SERVICE,
                environment=project_config.environment,
            )
            backend = self._backend()
            backend.action(service.unit, action)
            state = backend.status(service.unit)
            health = self.health_checker.check(service)
        finally:
            lock.release()

        return {
            "project": project,
            "service": alias,
            "action": action,
            "load_state": state.load_state,
            "active_state": state.active_state,
            "sub_state": state.sub_state,
            "health": health,
        }
