from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.ci_runner_guest_enrollment import (
    CIRunnerGuestEnrollmentError,
    CIRunnerGuestSpec,
    CIRunnerRegistrationSecret,
)
from runner_mcp.ci_runner_guest_fabric_transport import (
    CIRunnerGuestFabricTransport,
)
from runner_mcp.ci_runner_secret_handoff import (
    CIRunnerSecretHandoffStore,
)
from runner_mcp.fabric_bridge import FabricBridgeClient, FabricBridgeError


def spec() -> CIRunnerGuestSpec:
    return CIRunnerGuestSpec(
        alias="aifordable-lab-ci",
        repository="Blacksp1d3r/AIfordable",
        runner_name="aifordable-lab-ci",
        labels=("aifordable-ci",),
        transport_binding_key="aifordable-lab-ci",
    )


def store(tmp_path: Path) -> CIRunnerSecretHandoffStore:
    root = tmp_path / "handoff"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return CIRunnerSecretHandoffStore(
        root=root,
        now=lambda: 1000.0,
        random_bytes=lambda _size: b"\xab" * 16,
    )


class FakeFabric(FabricBridgeClient):
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.ids: list[str] = []

    def ci_runner_guest_enroll(self, handoff_id: str):
        self.ids.append(handoff_id)
        if self.error is not None:
            raise self.error
        return self.result


def good_result(**overrides):
    value = {
        "contract_version": (
            "runner.fabric/ci-runner-guest-execution/v1alpha1"
        ),
        "operation": "enroll",
        "state": "registered",
        "runner_name": "aifordable-lab-ci",
        "registered": True,
        "running": False,
        "isolation_green": True,
        "network_green": True,
        "mutation_enabled": True,
    }
    value.update(overrides)
    return value


def test_transport_sends_only_opaque_handoff_id(
    tmp_path: Path,
) -> None:
    handoffs = store(tmp_path)
    fabric = FakeFabric(good_result())
    transport = CIRunnerGuestFabricTransport(
        handoffs=handoffs,
        fabric=fabric,
    )
    secret = CIRunnerRegistrationSecret("s" * 32)

    result = transport.enroll(spec(), secret)

    assert result.state == "registered"
    assert result.registered is True
    assert fabric.ids == ["ab" * 16]
    assert secret.value not in repr(fabric.ids)


def test_bridge_failure_discards_unconsumed_handoff(
    tmp_path: Path,
) -> None:
    handoffs = store(tmp_path)
    fabric = FakeFabric(
        error=FabricBridgeError("private bridge failure")
    )
    transport = CIRunnerGuestFabricTransport(
        handoffs=handoffs,
        fabric=fabric,
    )

    with pytest.raises(
        CIRunnerGuestEnrollmentError,
        match="Fabric enrollment is unavailable",
    ):
        transport.enroll(
            spec(),
            CIRunnerRegistrationSecret("s" * 32),
        )

    assert not (tmp_path / "handoff" / ("ab" * 16)).exists()


@pytest.mark.parametrize(
    "mutation",
    [
        {"runner_name": "wrong-runner"},
        {"operation": "start"},
        {"state": "blocked"},
        {"registered": False},
        {"running": True},
    ],
)
def test_transport_requires_exact_enrollment_postconditions(
    tmp_path: Path,
    mutation: dict,
) -> None:
    transport = CIRunnerGuestFabricTransport(
        handoffs=store(tmp_path),
        fabric=FakeFabric(good_result(**mutation)),
    )

    with pytest.raises(CIRunnerGuestEnrollmentError):
        transport.enroll(
            spec(),
            CIRunnerRegistrationSecret("s" * 32),
        )


def test_handoff_store_discard_removes_safe_record_without_read(
    tmp_path: Path,
) -> None:
    handoffs = store(tmp_path)
    handoff = handoffs.create(CIRunnerRegistrationSecret("s" * 32))

    assert handoffs.discard(handoff.handoff_id) is True
    assert handoffs.discard(handoff.handoff_id) is False
