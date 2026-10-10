"""Fixed, rootless Claude subscription worker actuator (non-public Fabric child).

This module is intentionally NOT registered as an MCP service/tool or an
independent lifecycle controller. Fabric owns admission, leases/fencing and
scheduling. A first-party verifier plus dedicated-user local installation are
mandatory before use; never route through same-user ServiceManager or sudo.
"""

from __future__ import annotations

import os
import pwd
import re
import stat
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

_UNIT = "aifordable-subscription-coding-worker.service"
_USER = "aifordable-coder"
_CAPABILITY = "aifordable.subscription-coding-worker.lifecycle.v1"
_CONTRACT = "fabric.worker-lifecycle-intent.v1"
_SCHEMA = "runner-mcp/fixed-coding-worker-actuator/v1"
_SYSTEMCTL = Path("/usr/bin/systemctl")
_PORT = 8030
_FIELDS = frozenset({
    "contract_version", "intent_id", "worker_ref", "capability_id", "action",
    "expected_registry_revision", "lease_id", "owner_generation",
    "fence_epoch", "expires_at", "authorization_ref", "idempotency_key",
    "correlation_id",
})
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class FixedActuatorError(RuntimeError):
    """A local failure that is never copied into public tool results."""


class FixedServiceHost(Protocol):
    def status(self) -> str: ...
    def action(self, operation: str) -> None: ...
    def listener(self) -> str: ...


class RootlessCodingWorkerHost:
    """Call systemd ONLY while already running as the dedicated worker user."""

    @staticmethod
    def _environment() -> dict[str, str]:
        try:
            uid = pwd.getpwnam(_USER).pw_uid
        except KeyError as exc:
            raise FixedActuatorError("dedicated user unavailable") from exc
        if uid == 0 or os.geteuid() != uid:
            raise FixedActuatorError("wrong local service identity")
        runtime = Path("/run/user") / str(uid)
        bus = runtime / "bus"
        try:
            runtime_info = runtime.lstat()
            bus_info = bus.lstat()
        except OSError as exc:
            raise FixedActuatorError("dedicated systemd manager unavailable") from exc
        if (
            not stat.S_ISDIR(runtime_info.st_mode)
            or runtime_info.st_uid != uid
            or runtime_info.st_mode & 0o077
            or not stat.S_ISSOCK(bus_info.st_mode)
            or bus_info.st_uid != uid
            or _SYSTEMCTL.is_symlink()
            or not _SYSTEMCTL.is_file()
        ):
            raise FixedActuatorError("dedicated manager identity invalid")
        return {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "XDG_RUNTIME_DIR": str(runtime),
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={bus}",
        }

    def _systemctl(self, operation: str) -> str:
        # No caller can supply even a private arbitrary systemctl argument.
        if operation == "STATUS":
            args = [
                "show", _UNIT, "--property=LoadState",
                "--property=ActiveState", "--no-page",
            ]
        elif operation in {"START", "STOP", "RESTART"}:
            args = [operation.lower(), _UNIT]
        else:
            raise FixedActuatorError("unsupported fixed action")
        environment = self._environment()
        try:
            result = subprocess.run(
                [str(_SYSTEMCTL), "--user", "--no-pager", *args],
                env=environment,
                shell=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FixedActuatorError("fixed service command unavailable") from exc
        if result.returncode != 0:
            raise FixedActuatorError("fixed service command failed")
        return result.stdout

    def status(self) -> str:
        lines = self._systemctl("STATUS").splitlines()
        values: dict[str, str] = {}
        for line in lines:
            key, sep, value = line.partition("=")
            if sep and key in {"LoadState", "ActiveState"} and key not in values:
                values[key] = value
        if values.get("LoadState") != "loaded":
            raise FixedActuatorError("fixed service not loaded")
        state = values.get("ActiveState")
        if state == "active":
            return "ACTIVE"
        if state == "inactive":
            return "INACTIVE"
        if state == "failed":
            return "FAILED"
        if state in {"activating", "deactivating"}:
            return "TRANSITIONING"
        raise FixedActuatorError("fixed service state unavailable")

    def action(self, operation: str) -> None:
        if operation not in {"START", "STOP", "RESTART"}:
            raise FixedActuatorError("unsupported fixed action")
        self._systemctl(operation)

    def listener(self) -> str:
        # An exact loopback-only observation; no URL, token, socket
        # ownership or raw kernel output enters the public result.
        found = False
        for filename in ("/proc/net/tcp", "/proc/net/tcp6"):
            try:
                lines = Path(filename).read_text(encoding="ascii").splitlines()[1:]
            except (OSError, UnicodeError) as exc:
                raise FixedActuatorError("listener observation unavailable") from exc
            for line in lines:
                columns = line.split()
                if len(columns) < 4 or columns[3] != "0A":
                    continue
                host_port = columns[1].split(":")
                if len(host_port) != 2:
                    raise FixedActuatorError("listener observation malformed")
                try:
                    port = int(host_port[1], 16)
                except ValueError as exc:
                    raise FixedActuatorError("listener observation malformed") from exc
                if port != _PORT:
                    continue
                if filename.endswith("tcp6") or host_port[0] != "0100007F":
                    return "UNSAFE"
                found = True
        return "LOOPBACK_ONLY" if found else "ABSENT"


def _safe_intent(intent: object, now: int) -> bool:
    if not isinstance(intent, Mapping) or set(intent) != _FIELDS:
        return False
    action = intent.get("action")
    if not isinstance(action, str) or action not in {"STATUS", "START", "STOP", "RESTART"}:
        return False
    if intent.get("contract_version") != _CONTRACT:
        return False
    if intent.get("capability_id") != _CAPABILITY:
        return False
    for key in (
        "intent_id", "worker_ref", "lease_id", "authorization_ref",
        "idempotency_key", "correlation_id",
    ):
        value = intent.get(key)
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            return False
    for key in ("expected_registry_revision", "owner_generation", "fence_epoch"):
        value = intent.get(key)
        if type(value) is not int or value < 1:
            return False
    expires = intent.get("expires_at")
    # Validity is short, but only Fabric's trusted verifier can attest
    # authenticated time, registry revision, lease and fence.
    return type(expires) is int and now < expires <= now + 300


def _result(state: str, reason: str, *, observed: str = "UNKNOWN", listener: str = "UNKNOWN",
            mutation: bool = False) -> dict[str, Any]:
    return {
        "schemaVersion": _SCHEMA,
        "state": state,
        "reasonCode": reason,
        "observedState": observed,
        "listenerEvidence": listener,
        "mutationTriggered": mutation,
        "unitSelectionEnabled": False,
        "identitySelectionEnabled": False,
        "schedulerEnabled": False,
    }


class FixedCodingWorkerActuator:
    """Prebound fixed-host mechanism; Fabric owns all admission decisions."""

    def __init__(
        self,
        *,
        verify_fabric_intent: Callable[[Mapping[str, object]], bool] | None = None,
        host: FixedServiceHost | None = None,
    ) -> None:
        self._verify = verify_fabric_intent
        self._host = host or RootlessCodingWorkerHost()

    def execute(self, intent: object) -> dict[str, Any]:
        if not _safe_intent(intent, int(time.time())):
            return _result("blocked", "invalid-fabric-intent")
        if self._verify is None:
            return _result("blocked", "fabric-authority-unavailable")
        attempted_mutation = False
        try:
            if self._verify(intent) is not True:
                return _result("blocked", "fabric-intent-not-admitted")
            # Only the user account owning the rootless worker may execute.
            # Do not use sudo, account switching or arbitrary unit selectors.
            if not isinstance(self._host, RootlessCodingWorkerHost):
                # Non-production synthetic hosts support tests only; the
                # live integration must explicitly install the real host.
                pass
            elif os.geteuid() != pwd.getpwnam(_USER).pw_uid:
                return _result("blocked", "dedicated-identity-unavailable")
            action = intent["action"]
            # Observe the local unit AND port before mutating it. An
            # unrelated process can listen on the expected loopback port,
            # so listener presence alone must never authorize start/stop.
            before_state = self._host.status()
            before_listener = self._host.listener()
            if before_listener == "UNSAFE":
                return _result(
                    "blocked", "listener-not-loopback",
                    observed=before_state,
                )
            if (
                (before_state, before_listener)
                not in {("INACTIVE", "ABSENT"), ("ACTIVE", "LOOPBACK_ONLY")}
                and action != "STATUS"
            ):
                return _result(
                    "blocked", "pre-action-state-conflict",
                    observed=before_state, listener=before_listener,
                )
            if action == "START" and (before_state, before_listener) != ("INACTIVE", "ABSENT"):
                return _result(
                    "blocked", "pre-action-state-conflict",
                    observed=before_state, listener=before_listener,
                )
            if action in {"STOP", "RESTART"} and (
                before_state, before_listener
            ) != ("ACTIVE", "LOOPBACK_ONLY"):
                return _result(
                    "blocked", "pre-action-state-conflict",
                    observed=before_state, listener=before_listener,
                )
            if action != "STATUS":
                attempted_mutation = True
                self._host.action(action)
                state = self._host.status()
                listener = self._host.listener()
            else:
                state = before_state
                listener = before_listener
        except (OSError, RuntimeError, ValueError, TypeError, KeyError):
            return _result(
                "blocked", "fixed-actuator-unavailable",
                mutation=attempted_mutation,
            )
        if listener == "UNSAFE":
            return _result(
                "blocked", "listener-not-loopback",
                observed=state, mutation=action != "STATUS",
            )
        if action == "STATUS":
            return _result(
                "observed", "read-only-observation",
                observed=state, listener=listener,
            )
        if action in {"START", "RESTART"} and state == "ACTIVE" and listener == "LOOPBACK_ONLY":
            return _result(
                "observed", "fixed-action-observed",
                observed=state, listener=listener, mutation=True,
            )
        if action == "STOP" and state == "INACTIVE" and listener == "ABSENT":
            return _result(
                "observed", "fixed-action-observed",
                observed=state, listener=listener, mutation=True,
            )
        # A command dispatched to systemd is not proof of an accepted end
        # state; never report successful service activation on partial proof.
        return _result(
            "blocked", "post-action-proof-incomplete",
            observed=state, listener=listener, mutation=action != "STATUS",
        )
