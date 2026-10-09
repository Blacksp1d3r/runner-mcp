"""Explicit service adapters are injected capabilities, not host auto-detection."""

from __future__ import annotations

import pytest

from runner_mcp.host_platform import HostPlatform
from runner_mcp.service_manager import ServiceManager


@pytest.mark.parametrize("platform", [HostPlatform.LINUX, HostPlatform.WINDOWS, HostPlatform.UNSUPPORTED])
def test_explicit_backend_does_not_fall_back_to_host_specific_default(
    monkeypatch: pytest.MonkeyPatch,
    platform: HostPlatform,
) -> None:
    monkeypatch.setattr("runner_mcp.service_manager.detect_host_platform", lambda: platform)
    backend = object()

    def reject_default() -> None:
        pytest.fail("Injected service backend must never be replaced by systemd")

    monkeypatch.setattr("runner_mcp.service_manager.SystemdUserBackend", reject_default)
    manager = object.__new__(ServiceManager)
    manager.backend = backend
    assert manager._backend() is backend
    assert manager._backend() is backend
