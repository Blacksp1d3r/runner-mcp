from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from runner_mcp import fixed_coding_worker_actuator as actuator

CAPABILITY = "aifordable.subscription-coding-worker.lifecycle.v1"


@dataclass
class SyntheticHost:
    state: str = "INACTIVE"
    listen: str = "ABSENT"

    def __post_init__(self):
        self.calls: list[str] = []

    def action(self, operation: str) -> None:
        self.calls.append(operation)
        if operation in {"START", "RESTART"}:
            self.state = "ACTIVE"
            self.listen = "LOOPBACK_ONLY"
        elif operation == "STOP":
            self.state = "INACTIVE"
            self.listen = "ABSENT"

    def status(self) -> str:
        return self.state

    def listener(self) -> str:
        return self.listen


def fixed_intent(action: str = "STATUS", **changes):
    record = {
        "contract_version": "fabric.worker-lifecycle-intent.v1",
        "intent_id": "opaque-intent-01",
        "worker_ref": "pre-enrolled-worker-01",
        "capability_id": CAPABILITY,
        "action": action,
        "expected_registry_revision": 4,
        "lease_id": "lease-1",
        "owner_generation": 3,
        "fence_epoch": 7,
        "expires_at": int(time.time()) + 120,
        "authorization_ref": "central-decision-1",
        "idempotency_key": "fixed-key-1",
        "correlation_id": "request-1",
    }
    return {**record, **changes}


def test_default_no_fabric_authority_blocks_all_mutations():
    host = SyntheticHost()
    obj = actuator.FixedCodingWorkerActuator(host=host)
    for action in ("STATUS", "START", "STOP", "RESTART"):
        result = obj.execute(fixed_intent(action))
        assert result["state"] == "blocked"
        assert result["reasonCode"] == "fabric-authority-unavailable"
        assert result["mutationTriggered"] is False
    assert host.calls == []


@pytest.mark.parametrize("mutation", [
    {"user": "root"},
    {"unit": "any.service"},
    {"command": "/bin/sh"},
    {"environment": {"PATH": "/tmp"}},
    {"capability_id": "arbitrary"},
    {"contract_version": "unknown"},
    {"action": "EXEC"},
    {"action": ["START"]},
    {"worker_ref": "../private"},
    {"lease_id": "x" * 200},
    {"expires_at": 0},
    {"expires_at": int(time.time()) + 1000},
    {"expected_registry_revision": True},
    {"owner_generation": 0},
    {"fence_epoch": -1},
])
def test_untrusted_fields_expiry_or_injected_targets_fail_before_verifier(mutation):
    host = SyntheticHost()
    calls = []
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda raw: calls.append(raw) or True, host=host
    )
    outcome = obj.execute(fixed_intent("START", **mutation))
    assert outcome["state"] == "blocked"
    assert outcome["reasonCode"] == "invalid-fabric-intent"
    assert calls == []
    assert host.calls == []


def test_denied_central_lease_never_starts_worker():
    host = SyntheticHost()
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: False, host=host
    )
    outcome = obj.execute(fixed_intent("START"))
    assert outcome["reasonCode"] == "fabric-intent-not-admitted"
    assert host.calls == []


def test_fabric_verifier_failure_returns_bounded_block_not_secret():
    host = SyntheticHost()

    def fail(_):
        raise RuntimeError("/private/identity user-session-token=SECRET")

    obj = actuator.FixedCodingWorkerActuator(verify_fabric_intent=fail, host=host)
    outcome = obj.execute(fixed_intent("START"))
    assert outcome["state"] == "blocked"
    assert outcome["reasonCode"] == "fixed-actuator-unavailable"
    assert "/private/" not in str(outcome)
    assert "SECRET" not in str(outcome)
    assert host.calls == []


def test_status_is_read_only_and_public_safe():
    host = SyntheticHost(state="ACTIVE", listen="LOOPBACK_ONLY")
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    result = obj.execute(fixed_intent())
    assert result["state"] == "observed"
    assert result["observedState"] == "ACTIVE"
    assert result["listenerEvidence"] == "LOOPBACK_ONLY"
    assert result["mutationTriggered"] is False
    assert result["schedulerEnabled"] is False
    assert result["unitSelectionEnabled"] is False
    assert "aifordable-coder" not in str(result)
    assert host.calls == []


@pytest.mark.parametrize("action,expected_state,listener", [
    ("START", "ACTIVE", "LOOPBACK_ONLY"),
    ("STOP", "INACTIVE", "ABSENT"),
    ("RESTART", "ACTIVE", "LOOPBACK_ONLY"),
])
def test_only_exact_rootless_actions_produce_observed_terminal_evidence(
    action, expected_state, listener
):
    host = SyntheticHost()
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    result = obj.execute(fixed_intent(action))
    assert result["state"] == "observed"
    assert result["reasonCode"] == "fixed-action-observed"
    assert result["observedState"] == expected_state
    assert result["listenerEvidence"] == listener
    assert result["mutationTriggered"] is True
    assert host.calls == [action]


def test_unexpected_public_listener_blocks_success():
    host = SyntheticHost()
    host.action = lambda operation: setattr(host, "listen", "UNSAFE")
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    result = obj.execute(fixed_intent("START"))
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "listener-not-loopback"
    assert result["mutationTriggered"] is True


def test_systemd_action_return_alone_is_not_qualification():
    host = SyntheticHost()
    host.action = lambda _: host.calls.append("attempted")
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    result = obj.execute(fixed_intent("START"))
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "post-action-proof-incomplete"
    assert result["mutationTriggered"] is True
    assert host.calls == ["attempted"]


def test_wrong_identity_prevents_rootless_status_and_start(monkeypatch):
    host = actuator.RootlessCodingWorkerHost()
    monkeypatch.setattr(actuator.os, "geteuid", lambda: 1234567)
    monkeypatch.setattr(
        actuator.pwd, "getpwnam",
        lambda _: type("ServiceIdentity", (), {"pw_uid": 1234568})(),
    )
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    for action in ("STATUS", "START"):
        result = obj.execute(fixed_intent(action))
        assert result["state"] == "blocked"
        assert result["reasonCode"] == "dedicated-identity-unavailable"


def test_fixed_systemctl_command_has_no_cross_user_or_caller_selectors(monkeypatch):
    calls = []

    def invoke(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "LoadState=loaded\nActiveState=inactive\n", "")

    monkeypatch.setattr(
        actuator.RootlessCodingWorkerHost, "_environment",
        staticmethod(lambda: {"PATH": "/usr/bin:/bin"}),
    )
    monkeypatch.setattr(actuator.subprocess, "run", invoke)
    host = actuator.RootlessCodingWorkerHost()
    assert host.status() == "INACTIVE"
    host.action("START")
    assert calls[0][0] == [
        "/usr/bin/systemctl", "--user", "--no-pager", "show",
        "aifordable-subscription-coding-worker.service",
        "--property=LoadState", "--property=ActiveState", "--no-page",
    ]
    assert calls[1][0] == [
        "/usr/bin/systemctl", "--user", "--no-pager", "start",
        "aifordable-subscription-coding-worker.service",
    ]
    for cmd, kwargs in calls:
        assert "sudo" not in str(cmd)
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == 10


def test_listener_checks_only_exact_ipv4_loopback_and_rejects_wildcard(monkeypatch):
    samples = {
        "/proc/net/tcp": (
            "sl local_address rem_address st\n"
            "1: 0100007F:1F5E 00000000:0000 0A\n"
        ),
        "/proc/net/tcp6": "sl local_address rem_address st\n",
    }
    original = Path.read_text

    def read(self, **kwargs):
        if str(self) in samples:
            return samples[str(self)]
        return original(self, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    host = actuator.RootlessCodingWorkerHost()
    assert host.listener() == "LOOPBACK_ONLY"
    samples["/proc/net/tcp"] = (
        "sl local_address rem_address st\n"
        "1: 00000000:1F5E 00000000:0000 0A\n"
    )
    assert host.listener() == "UNSAFE"
    samples["/proc/net/tcp"] = "sl local_address rem_address st\n"
    assert host.listener() == "ABSENT"


def test_unknown_private_systemctl_selector_denied_even_inside_host(monkeypatch):
    calls = []
    monkeypatch.setattr(
        actuator.RootlessCodingWorkerHost, "_environment",
        staticmethod(lambda: calls.append("environment") or {}),
    )
    host = actuator.RootlessCodingWorkerHost()
    with pytest.raises(actuator.FixedActuatorError):
        host._systemctl("enable")
    assert calls == []


def test_exception_after_action_intent_does_not_claim_no_mutation():
    host = SyntheticHost()

    def partial(_operation):
        raise RuntimeError("/private/systemd attempted command, state unknown")

    host.action = partial
    obj = actuator.FixedCodingWorkerActuator(
        verify_fabric_intent=lambda _: True, host=host
    )
    result = obj.execute(fixed_intent("START"))
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "fixed-actuator-unavailable"
    assert result["mutationTriggered"] is True
    assert "/private/" not in str(result)
