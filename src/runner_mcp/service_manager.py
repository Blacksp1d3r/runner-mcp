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
from .operational_safety import ActionClass, OperatorSafetyGuard


class ServiceManagerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceState:
    load_state: str
    active_state: str
    sub_state: str


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

        return ServiceState(
            load_state=values["LoadState"],
            active_state=values["ActiveState"],
            sub_state=values["SubState"],
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
