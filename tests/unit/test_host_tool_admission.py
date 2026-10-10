"""Same advertised tools everywhere; host execution remains independently denied."""
from dataclasses import replace

import pytest

from runner_mcp.host_tool_admission import (
    HostToolPolicyError,
    QualifiedHostToolPolicy,
    evaluate_host_tool_admission,
)

REVISION = "a" * 40
SCHEMA = "b" * 64
NAMES = frozenset({
    "runtime_status",
    "queue_status",
    "bewind_ocr_qualification_run",
    "bewind_ocr_qualification_stage",
    "restart_service",
})


def policy(*, granted=frozenset({"runtime_status", "queue_status"})):
    return QualifiedHostToolPolicy(
        service_asset_id="service:primary",
        release_source_revision=REVISION,
        interface_schema_sha256=SCHEMA,
        permitted_tool_names=granted,
        expires_at_epoch=2_000,
    )


def evaluate(tool, *, permit=None, revision=REVISION, digest=SCHEMA, now=1_000):
    return evaluate_host_tool_admission(
        tool,
        registered_tool_names=NAMES,
        runtime_source_revision=revision,
        runtime_interface_schema_sha256=digest,
        policy=permit,
        now_epoch=now,
    )


def test_same_tool_names_but_different_local_rights():
    control = policy()
    lab = replace(control,
        service_asset_id="service:lab",
        permitted_tool_names=frozenset({
            "runtime_status", "queue_status",
            "bewind_ocr_qualification_run",
            "bewind_ocr_qualification_stage",
        }),
    )
    tool = "bewind_ocr_qualification_run"
    denied = evaluate(tool, permit=control)
    allowed = evaluate(tool, permit=lab)
    assert denied.allowed is False
    assert denied.response_code == "HOST_TOOL_NOT_PERMITTED"
    assert denied.reason_code == "tool_not_granted_on_host"
    assert allowed.allowed is True
    assert allowed.reason_code == "exact_host_capability_granted"
    assert allowed.response_code == "OK"
    # Both machines still present the same registered schema/name set.
    assert NAMES == NAMES


def test_missing_host_policy_is_explicit_denial_not_missing_tool():
    result = evaluate("runtime_status")
    assert result.to_public_payload() == {
        "allowed": False,
        "reasonCode": "host_policy_unavailable",
        "code": "HOST_TOOL_NOT_PERMITTED",
    }


@pytest.mark.parametrize(
    ("changed", "reason"),
    [
        ({"revision": "c" * 40}, "runtime_generation_mismatch"),
        ({"digest": "c" * 64}, "runtime_generation_mismatch"),
        ({"revision": None}, "runtime_generation_mismatch"),
        ({"digest": None}, "runtime_generation_mismatch"),
        ({"now": 2_000}, "host_policy_expired"),
        ({"now": 2_001}, "host_policy_expired"),
    ],
)
def test_old_or_unknown_runtime_and_expired_host_policy_fail_closed(
    changed, reason,
):
    result = evaluate("runtime_status", permit=policy(), **changed)
    assert result.allowed is False
    assert result.response_code == "HOST_TOOL_NOT_PERMITTED"
    assert result.reason_code == reason


def test_undeclared_tool_or_unqualified_catalogue_refused():
    unknown = evaluate("fabric_hidden_command", permit=policy())
    assert unknown.allowed is False
    assert unknown.reason_code == "tool_not_in_qualified_catalogue"

    extra = replace(
        policy(), permitted_tool_names=frozenset({
            "runtime_status", "fabric_hidden_command",
        }),
    )
    assert evaluate(
        "runtime_status", permit=extra
    ).reason_code == "host_policy_catalogue_mismatch"


def test_shared_high_risk_tool_is_not_implicitly_permitted():
    denied = evaluate("restart_service", permit=policy())
    assert denied.allowed is False
    assert denied.reason_code == "tool_not_granted_on_host"
    assert "restart_service" not in denied.to_public_payload().values()


@pytest.mark.parametrize(
    "field, bad",
    [
        ("service_asset_id", "bad host /"),
        ("release_source_revision", "old-release"),
        ("interface_schema_sha256", "unqualified"),
        ("permitted_tool_names", ["runtime_status"]),
        ("expires_at_epoch", True),
        ("expires_at_epoch", -1),
    ],
)
def test_malformed_host_authority_is_rejected(field, bad):
    with pytest.raises(HostToolPolicyError, match="invalid"):
        replace(policy(), **{field: bad})


def test_bad_client_inputs_never_create_permission():
    for extra in (
        {"registered_tool_names": frozenset({"runtime_status", "bad/path"})},
        {"now_epoch": True},
        {"tool_name": "caller supplied/exec"},
    ):
        args = {
            "tool_name": "runtime_status",
            "registered_tool_names": NAMES,
            "runtime_source_revision": REVISION,
            "runtime_interface_schema_sha256": SCHEMA,
            "policy": policy(),
            "now_epoch": 1_000,
        }
        args.update(extra)
        with pytest.raises(HostToolPolicyError, match="invalid"):
            evaluate_host_tool_admission(**args)
