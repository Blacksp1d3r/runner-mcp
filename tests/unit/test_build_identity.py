from __future__ import annotations

import pytest

from runner_mcp.build_identity import (
    BuildIdentity,
    BuildIdentityError,
    runner_mcp_build_identity,
    runner_mcp_mcp_build_identity,
)


def test_runner_mcp_identity_keeps_unproven_provenance_explicit() -> None:
    identity = runner_mcp_build_identity("0.1.3")

    assert identity.to_payload() == {
        "component_id": "runner-mcp",
        "build_version": "0.1.3",
        "source_revision": None,
        "artifact_digest": None,
        "protocol_min": None,
        "protocol_max": None,
        "interface_schema_digest": None,
    }


def test_runner_mcp_mcp_identity_uses_installed_handshake_range() -> None:
    from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS

    identity = runner_mcp_mcp_build_identity(
        "0.1.3",
        interface_schema_digest="a" * 64,
    )

    assert identity.component_id == "runner-mcp"
    assert identity.build_version == "0.1.3"
    assert identity.protocol_min == HANDSHAKE_PROTOCOL_VERSIONS[0]
    assert identity.protocol_max == HANDSHAKE_PROTOCOL_VERSIONS[-1]
    assert identity.interface_schema_digest == "a" * 64
    assert identity.source_revision is None
    assert identity.artifact_digest is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"component_id": "INVALID SPACE", "build_version": "0.1.3"},
        {
            "component_id": "runner-mcp",
            "build_version": "0.1.3",
            "source_revision": "bad",
        },
        {
            "component_id": "runner-mcp",
            "build_version": "0.1.3",
            "artifact_digest": "bad",
        },
        {
            "component_id": "runner-mcp",
            "build_version": "0.1.3",
            "protocol_min": "v1",
            "protocol_max": None,
        },
        {
            "component_id": "runner-mcp",
            "build_version": "0.1.3",
            "interface_schema_digest": "bad",
        },
    ],
)
def test_invalid_build_identity_fails_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(BuildIdentityError):
        BuildIdentity(**kwargs)
