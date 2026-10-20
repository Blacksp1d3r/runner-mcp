"""Default service backend must never fall into Linux systemd on Windows."""

from __future__ import annotations

import pytest

from runner_mcp.host_platform import HostPlatform
from runner_mcp.service_manager import ServiceManager, ServiceManagerError


@pytest.mark.parametrize("platform", [HostPlatform.WINDOWS, HostPlatform.UNSUPPORTED])
def test_default_service_backend_rejects_non_linux_without_starting_systemctl(
    monkeypatch: pytest.MonkeyPatch,
    platform: HostPlatform,
) -> None:
    monkeypatch.setattr("runner_mcp.service_manager.detect_host_platform", lambda: platform)

    def forbid_systemd() -> None:
        pytest.fail("Linux backend must not be initialized on another host family")

    monkeypatch.setattr("runner_mcp.service_manager.SystemdUserBackend", forbid_systemd)
    manager = object.__new__(ServiceManager)
    manager.backend = None
    with pytest.raises(ServiceManagerError, match="unavailable for this platform"):
        manager._backend()


def test_default_service_backend_keeps_linux_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "runner_mcp.service_manager.detect_host_platform",
        lambda: HostPlatform.LINUX,
    )
    selected = object()
    monkeypatch.setattr(
        "runner_mcp.service_manager.SystemdUserBackend",
        lambda: selected,
    )
    manager = object.__new__(ServiceManager)
    manager.backend = None
    assert manager._backend() is selected
    assert manager._backend() is selected
