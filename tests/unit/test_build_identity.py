from __future__ import annotations

import json
from pathlib import Path

import pytest

from runner_mcp.build_identity import (
    BuildIdentity,
    BuildIdentityError,
    bounded_build_identity_payload,
    installed_source_revision,
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


def test_installed_source_revision_reads_canonical_state(tmp_path: Path) -> None:
    commit = "a" * 40
    path = tmp_path / "self-update-state.json"
    path.write_text(json.dumps({"commit": commit, "installed_at": "2026-10-06T19:00:00+00:00"}), encoding="utf-8")
    path.chmod(0o600)

    assert installed_source_revision(tmp_path) == commit


def test_installed_source_revision_is_unknown_when_state_is_missing(
    tmp_path: Path,
) -> None:
    assert installed_source_revision(tmp_path) is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"commit": "bad"},
        [],
    ],
)
def test_installed_source_revision_rejects_malformed_state(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "self-update-state.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BuildIdentityError):
        installed_source_revision(tmp_path)


def test_installed_source_revision_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"commit": "a" * 40}), encoding="utf-8")
    (tmp_path / "self-update-state.json").symlink_to(target)

    with pytest.raises(BuildIdentityError, match="unsafe"):
        installed_source_revision(tmp_path)


def test_runner_mcp_identity_accepts_proven_source_revision() -> None:
    commit = "b" * 40

    identity = runner_mcp_build_identity("0.1.3", source_revision=commit)
    mcp_identity = runner_mcp_mcp_build_identity(
        "0.1.3",
        source_revision=commit,
    )

    assert identity.source_revision == commit
    assert mcp_identity.source_revision == commit

def test_bounded_identity_keeps_valid_identity_unchanged() -> None:
    identity = runner_mcp_build_identity("0.1.3", source_revision="a" * 40)
    assert bounded_build_identity_payload(lambda: identity) == identity.to_payload()


@pytest.mark.parametrize("error_type", [OSError, RuntimeError, TypeError, ValueError])
def test_bounded_identity_reports_unavailable_without_private_exception(
    error_type: type[Exception],
) -> None:
    def broken_provider() -> BuildIdentity:
        raise error_type("/private/config/state.json token=NEVER_EXPOSE")

    result = bounded_build_identity_payload(broken_provider)
    assert result == {
        "schemaVersion": "runner-mcp/build-identity-unavailable/v1",
        "state": "unavailable",
        "reasonCode": "build-identity-unavailable",
        "identityEvidenceComplete": False,
    }
    assert "NEVER_EXPOSE" not in str(result)


def test_bounded_identity_rejects_missing_provider_and_wrong_type() -> None:
    expected = bounded_build_identity_payload(None)
    assert expected["state"] == "unavailable"
    assert expected["identityEvidenceComplete"] is False
    assert bounded_build_identity_payload(lambda: {"source_revision": "a" * 40}) == expected


def test_bounded_identity_rejects_malformed_serialization(monkeypatch) -> None:
    identity = runner_mcp_build_identity("0.1.3")
    monkeypatch.setattr(BuildIdentity, "to_payload", lambda _self: {"private": "NEVER_EXPOSE"})
    assert bounded_build_identity_payload(lambda: identity) == {
        "schemaVersion": "runner-mcp/build-identity-unavailable/v1",
        "state": "unavailable",
        "reasonCode": "build-identity-unavailable",
        "identityEvidenceComplete": False,
    }
