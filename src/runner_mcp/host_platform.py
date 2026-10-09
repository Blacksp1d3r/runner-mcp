from __future__ import annotations

import platform
from dataclasses import dataclass
from enum import StrEnum


class HostPlatform(StrEnum):
    LINUX = "linux"
    WINDOWS = "windows"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class HostPlatformContract:
    """Describe recognized host families, not permission to activate a runtime."""

    platform: HostPlatform
    service_backend_family: str
    permission_backend_family: str
    isolation_backend_candidates: tuple[str, ...]
    supported: bool
    service_adapter_implemented: bool

    def public_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform.value,
            "serviceBackendFamily": self.service_backend_family,
            "permissionBackendFamily": self.permission_backend_family,
            "isolationBackendCandidates": list(self.isolation_backend_candidates),
            "supported": self.supported,
            "serviceAdapterImplemented": self.service_adapter_implemented,
        }


def detect_host_platform(system_name: str | None = None) -> HostPlatform:
    detected = (system_name if system_name is not None else platform.system()).strip().casefold()
    if detected == "linux":
        return HostPlatform.LINUX
    if detected == "windows":
        return HostPlatform.WINDOWS
    return HostPlatform.UNSUPPORTED


def platform_contract(system_name: str | None = None) -> HostPlatformContract:
    host_platform = detect_host_platform(system_name)
    if host_platform is HostPlatform.LINUX:
        return HostPlatformContract(
            platform=host_platform,
            service_backend_family="systemd-user",
            permission_backend_family="posix",
            isolation_backend_candidates=("incus", "process"),
            supported=True,
            service_adapter_implemented=True,
        )
    if host_platform is HostPlatform.WINDOWS:
        return HostPlatformContract(
            platform=host_platform,
            service_backend_family="windows-service-control-manager",
            permission_backend_family="ntfs-acl",
            isolation_backend_candidates=("windows-job-object", "hyper-v"),
            supported=True,
            service_adapter_implemented=False,
        )
    return HostPlatformContract(
        platform=host_platform,
        service_backend_family="unsupported",
        permission_backend_family="unsupported",
        isolation_backend_candidates=(),
        supported=False,
        service_adapter_implemented=False,
    )
