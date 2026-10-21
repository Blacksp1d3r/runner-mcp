"""Generation correlation without pretending to identify a host or wheel."""

from __future__ import annotations

import re

import pytest

import runner_mcp.serving_instance_epoch as epoch_module
from runner_mcp.serving_instance_epoch import ServingInstanceEpoch


def test_same_server_instance_epoch_is_stable_but_not_shared_with_another() -> None:
    first = ServingInstanceEpoch()
    second = ServingInstanceEpoch()
    value = first.value()
    assert re.fullmatch(r"[0-9a-f]{32}", value)
    assert first.value() == value
    assert second.value() != value
    assert not any(marker in value for marker in ("runner", "/", "private", "host"))


def test_forked_process_cannot_reuse_parent_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(epoch_module.os, "getpid", lambda: 1427)
    first = ServingInstanceEpoch()
    parent = first.value()
    monkeypatch.setattr(epoch_module.os, "getpid", lambda: 1428)
    child = first.value()
    assert parent != child
    assert first.value() == child


def test_public_epoch_does_not_echo_seed_or_process_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = b"synthetic-private-seed-not-a-real-secret"
    monkeypatch.setattr(epoch_module.secrets, "token_bytes", lambda _: secret)
    monkeypatch.setattr(epoch_module.os, "getpid", lambda: 1631)
    result = ServingInstanceEpoch().value()
    assert result != secret.hex()[:32]
    assert "1631" not in result
    assert "synthetic" not in result


@pytest.mark.parametrize("pid", [0, -1, 2**64])
def test_invalid_process_identity_rejected(
    monkeypatch: pytest.MonkeyPatch, pid: int,
) -> None:
    monkeypatch.setattr(epoch_module.os, "getpid", lambda: pid)
    with pytest.raises(RuntimeError, match="unavailable"):
        ServingInstanceEpoch().value()
