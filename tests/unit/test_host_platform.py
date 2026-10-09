from __future__ import annotations

from runner_mcp.host_platform import HostPlatform, detect_host_platform, platform_contract


def test_detect_host_platform_linux() -> None:
    assert detect_host_platform("Linux") is HostPlatform.LINUX


def test_detect_host_platform_windows() -> None:
    assert detect_host_platform("Windows") is HostPlatform.WINDOWS


def test_detect_host_platform_unknown_fails_closed() -> None:
    assert detect_host_platform("Darwin") is HostPlatform.UNSUPPORTED


def test_linux_contract_preserves_current_backend_families() -> None:
    contract = platform_contract("Linux")

    assert contract.platform is HostPlatform.LINUX
    assert contract.service_backend_family == "systemd-user"
    assert contract.permission_backend_family == "posix"
    assert contract.isolation_backend_candidates == ("incus", "process")
    assert contract.supported is True
    assert contract.service_adapter_implemented is True


def test_windows_contract_is_first_class_without_claiming_linux_backends() -> None:
    contract = platform_contract("Windows")

    assert contract.platform is HostPlatform.WINDOWS
    assert contract.service_backend_family == "windows-service-control-manager"
    assert contract.permission_backend_family == "ntfs-acl"
    assert contract.isolation_backend_candidates == ("windows-job-object", "hyper-v")
    assert contract.supported is True
    assert contract.service_adapter_implemented is False
    assert "systemd" not in contract.service_backend_family
    assert "incus" not in contract.isolation_backend_candidates


def test_public_contract_is_bounded_and_platform_neutral() -> None:
    assert platform_contract("Windows").public_dict() == {
        "platform": "windows",
        "serviceBackendFamily": "windows-service-control-manager",
        "permissionBackendFamily": "ntfs-acl",
        "isolationBackendCandidates": ["windows-job-object", "hyper-v"],
        "supported": True,
        "serviceAdapterImplemented": False,
    }


def test_unsupported_contract_fails_closed() -> None:
    contract = platform_contract("Plan9")

    assert contract.supported is False
    assert contract.service_adapter_implemented is False
    assert contract.service_backend_family == "unsupported"
    assert contract.permission_backend_family == "unsupported"
    assert contract.isolation_backend_candidates == ()
