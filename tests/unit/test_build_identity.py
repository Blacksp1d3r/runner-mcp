from __future__ import annotations

import json
from pathlib import Path

import pytest

from runner_mcp.build_identity import (
    BuildIdentity,
    BuildIdentityError,
    bounded_build_identity_payload,
    fail_closed_runtime_provenance,
    installed_source_revision,
    last_self_update_revision,
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


def test_last_self_update_revision_reads_historical_state(tmp_path: Path) -> None:
    commit = "a" * 40
    path = tmp_path / "self-update-state.json"
    path.write_text(json.dumps({"commit": commit, "installed_at": "2026-10-06T19:00:00+00:00"}), encoding="utf-8")
    path.chmod(0o600)

    assert last_self_update_revision(tmp_path) == commit
    assert installed_source_revision(tmp_path) is None


def test_last_self_update_revision_is_unknown_when_state_is_missing(
    tmp_path: Path,
) -> None:
    assert last_self_update_revision(tmp_path) is None
    assert installed_source_revision(tmp_path) is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"commit": "bad"},
        [],
    ],
)
def test_last_self_update_revision_rejects_malformed_state(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "self-update-state.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BuildIdentityError):
        last_self_update_revision(tmp_path)


def test_last_self_update_revision_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"commit": "a" * 40}), encoding="utf-8")
    (tmp_path / "self-update-state.json").symlink_to(target)

    with pytest.raises(BuildIdentityError, match="unsafe"):
        last_self_update_revision(tmp_path)
    assert installed_source_revision(tmp_path) is None



@pytest.mark.parametrize("historical_commit", ["a" * 40, "b" * 40])
def test_active_source_never_uses_stale_self_update_marker(
    tmp_path: Path, historical_commit: str
) -> None:
    (tmp_path / "self-update-state.json").write_text(
        json.dumps({"commit": historical_commit}), encoding="utf-8"
    )
    assert last_self_update_revision(tmp_path) == historical_commit
    assert installed_source_revision(tmp_path) is None


def test_active_source_ignores_even_broken_historical_transaction(
    tmp_path: Path,
) -> None:
    (tmp_path / "self-update-state.json").write_text(
        "malformed historical state", encoding="utf-8"
    )
    assert installed_source_revision(tmp_path) is None


def test_manual_wheel_update_must_not_claim_old_commit(
    tmp_path: Path,
) -> None:
    # A prior self-update marker remains after a separately installed wheel.
    (tmp_path / "self-update-state.json").write_text(
        json.dumps({"commit": "a" * 40}), encoding="utf-8"
    )
    observed = runner_mcp_mcp_build_identity(
        "0.1.7",
        source_revision=installed_source_revision(tmp_path),
    )
    assert observed.build_version == "0.1.7"
    assert observed.source_revision is None
    assert observed.artifact_digest is None



def test_runtime_managers_cannot_override_serving_build_version_or_commit() -> None:
    payload = {
        "version": "0.1.3",
        "source_commit": "a" * 40,
        "last_installed_commit": "a" * 40,
        "active_runtime_revision": "a" * 40,
        "source_baseline_aligned": True,
        "runtime_activation_aligned": True,
        "self_update_ready": True,
    }
    result = fail_closed_runtime_provenance(
        payload,
        loaded_version="0.1.7",
        installed_distribution_version="0.1.8",
    )
    assert result["version"] == "0.1.7"
    assert result["installed_distribution_version"] == "0.1.8"
    assert result["active_build_provenance_verified"] is False
    assert result["active_artifact_revision"] is None
    assert result["active_artifact_digest"] is None
    assert result["source_commit"] is None
    assert result["last_installed_commit"] is None
    assert result["active_runtime_revision"] is None
    assert result["self_update_history_source_commit"] == "a" * 40
    assert result["self_update_history_last_installed_commit"] == "a" * 40
    assert result["self_update_history_active_runtime_revision"] == "a" * 40
    assert result["self_update_history_source_baseline_aligned"] is True
    assert result["self_update_history_runtime_activation_aligned"] is True
    assert result["self_update_ready"] is False
    assert payload["source_commit"] == "a" * 40


@pytest.mark.parametrize("bad_version", ["", "private" + chr(10) + "value", "a" * 129])
def test_runtime_identity_sanitizer_rejects_malformed_versions(
    bad_version: str,
) -> None:
    with pytest.raises(BuildIdentityError):
        fail_closed_runtime_provenance(
            {"version": "0.1.3"},
            loaded_version=bad_version,
            installed_distribution_version="0.1.7",
        )


def test_loaded_server_version_does_not_follow_later_dist_info_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import runner_mcp
    from runner_mcp import server

    loaded = server._loaded_package_version
    assert loaded == runner_mcp.__version__
    monkeypatch.setattr(server, "version", lambda _name: "99.99.99")
    assert server._loaded_package_version == loaded


def test_active_source_rejects_invalid_config_input() -> None:
    with pytest.raises(BuildIdentityError):
        installed_source_revision("untrusted")  # type: ignore[arg-type]

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


@pytest.mark.parametrize(
    "error_type",
    [OSError, RuntimeError, TypeError, ValueError, KeyError, IndexError, AttributeError],
)
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


@pytest.mark.parametrize("error_type", [KeyError, IndexError, AttributeError])
def test_bounded_identity_cannot_leak_broken_serialization(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    identity = runner_mcp_build_identity("0.1.102")

    def broken_serialization(_self: BuildIdentity) -> dict[str, object]:
        raise error_type("/private/original-serving-wheel token=NEVER_EXPOSE")

    monkeypatch.setattr(BuildIdentity, "to_payload", broken_serialization)
    result = bounded_build_identity_payload(lambda: identity)
    assert result["state"] == "unavailable"
    assert result["identityEvidenceComplete"] is False
    assert result["reasonCode"] == "build-identity-unavailable"
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
@pytest.mark.parametrize("reported_ready", [True, False, None, "true", 1, {}])
@pytest.mark.parametrize(
    ("loaded_version", "installed_version"),
    [("0.1.38", "0.1.38"), ("0.1.38", "0.1.52")],
)
def test_unverified_active_generation_never_inherits_manager_update_ready(
    reported_ready: object,
    loaded_version: str,
    installed_version: str,
) -> None:
    manager_state = {
        "self_update_ready": reported_ready,
        "active_build_provenance_verified": True,
        "active_artifact_revision": "a" * 40,
        "active_artifact_digest": "b" * 64,
        "source_commit": "c" * 40,
        "runtime_activation_aligned": True,
    }
    observed = fail_closed_runtime_provenance(
        manager_state,
        loaded_version=loaded_version,
        installed_distribution_version=installed_version,
    )
    assert observed["version"] == loaded_version
    assert observed["installed_distribution_version"] == installed_version
    assert observed["self_update_ready"] is False
    assert observed["active_build_provenance_verified"] is False
    assert observed["active_artifact_revision"] is None
    assert observed["active_artifact_digest"] is None
    assert observed["source_commit"] is None
    assert observed["self_update_history_source_commit"] == "c" * 40
    assert observed["runtime_activation_aligned"] is None
    assert manager_state["self_update_ready"] == reported_ready


@pytest.mark.parametrize(
    ("loaded_version", "installed_version", "equal"),
    [
        ("0.1.38", "0.1.38", True),
        ("0.1.38", "0.1.3", False),
        ("0.1.38", "0.1.75", False),
    ],
)
def test_669_runtime_answer_never_infers_host_or_wheel_identity_from_versions(
    loaded_version: str, installed_version: str, equal: bool
) -> None:
    # A separately installed CLI, or a second host serving the same version,
    # must not be interpreted as proof of the responder's wheel or other roles.
    manager = {
        "version": "99.99.99",
        "reply_identity_scope": "all_hosts_verified",
        "reply_source_host_verified": True,
        "loaded_module_wheel_identity_verified": True,
        "six_role_process_roster_verified": True,
        "loaded_installed_versions_equal": not equal,
        "self_update_ready": True,
    }
    observed = fail_closed_runtime_provenance(
        manager,
        loaded_version=loaded_version,
        installed_distribution_version=installed_version,
    )
    assert observed["version"] == loaded_version
    assert observed["installed_distribution_version"] == installed_version
    assert observed["loaded_installed_versions_equal"] is equal
    assert observed["reply_identity_scope"] == "this_connected_process_only"
    assert observed["reply_source_host_verified"] is False
    assert observed["loaded_module_wheel_identity_verified"] is False
    assert observed["six_role_process_roster_verified"] is False
    assert observed["active_build_provenance_verified"] is False
    assert observed["active_artifact_revision"] is None
    assert observed["active_artifact_digest"] is None
    assert observed["self_update_ready"] is False
    assert manager["reply_source_host_verified"] is True


@pytest.mark.parametrize(
    "manager_epoch",
    ["f" * 32, None, True, "invalid", {"foreign": "host"}],
)
def test_669_serving_epoch_cannot_be_overwritten_by_status_managers(
    manager_epoch: object,
) -> None:
    # The current process binds the value, not a merged/historical status
    # manager or a separate same-version Runner-MCP instance.
    forged_status = {
        "serving_instance_epoch": manager_epoch,
        "serving_instance_epoch_authenticated": True,
        "version": "0.1.3",
        "active_artifact_digest": "f" * 64,
        "self_update_ready": True,
    }
    response = fail_closed_runtime_provenance(
        forged_status,
        loaded_version="0.1.77",
        installed_distribution_version="0.1.77",
        serving_instance_epoch="a" * 32,
    )
    assert response["serving_instance_epoch"] == "a" * 32
    assert response["serving_instance_epoch_authenticated"] is False
    assert response["reply_identity_scope"] == "this_connected_process_only"
    assert response["active_artifact_digest"] is None
    assert response["self_update_ready"] is False
    assert forged_status["serving_instance_epoch"] == manager_epoch
    assert forged_status["serving_instance_epoch_authenticated"] is True


@pytest.mark.parametrize("bad_epoch", ["short", "A" * 32, "", "0" * 33, 1, True, b"a" * 32])
def test_669_invalid_caller_serving_epochs_are_rejected(
    bad_epoch: object,
) -> None:
    with pytest.raises(BuildIdentityError, match="serving instance epoch"):
        fail_closed_runtime_provenance(
            {},
            loaded_version="0.1.77",
            installed_distribution_version="0.1.77",
            serving_instance_epoch=bad_epoch,  # type: ignore[arg-type]
        )


def test_669_legacy_call_with_no_trusted_epoch_clears_manager_claims() -> None:
    response = fail_closed_runtime_provenance(
        {"serving_instance_epoch": "f" * 32, "serving_instance_epoch_authenticated": True},
        loaded_version="0.1.38",
        installed_distribution_version="0.1.38",
    )
    assert response["serving_instance_epoch"] is None
    assert response["serving_instance_epoch_authenticated"] is False
