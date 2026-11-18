"""Disposable MCPServer interception tests, not real host authority."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from time import time

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from runner_mcp.host_tool_admission import QualifiedHostToolPolicy
from runner_mcp.host_tool_dispatch import HostAdmissionMCPServer, HostDispatchEvidence

REV = "a" * 40
SCHEMA = "b" * 64
ASSET = "service:primary"


class AuditSink:
    def __init__(self, *, fail=False):
        self.events = []
        self.fail = fail

    def append(self, event):
        if self.fail:
            raise OSError("private/audit/path/should-not-leak")
        self.events.append(event)


def _policy(*, host=ASSET, permitted=frozenset({"write_test"}), expiry=None):
    return QualifiedHostToolPolicy(
        service_asset_id=host,
        release_source_revision=REV,
        interface_schema_sha256=SCHEMA,
        permitted_tool_names=permitted,
        expires_at_epoch=expiry if expiry is not None else int(time()) + 3600,
    )


def _rig(*, policy=None, asset=ASSET, revision=REV, audit=None, provider_error=False):
    sink = audit or AuditSink()
    facts = HostDispatchEvidence(
        verified_service_asset_id=asset,
        runtime_source_revision=revision,
        policy=policy,
    )
    observed = {"count": 0}

    def provider():
        if provider_error:
            raise OSError("secret://provider/not-qualified")
        return facts

    async def digest(_):
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "host-admission-disposable",
        evidence_provider=provider,
        schema_digest_provider=digest,
        audit=sink,
    )

    @mcp.tool()
    def write_test(value: str) -> str:
        observed["count"] += 1
        return "written:" + value

    return mcp, observed, sink


def _invoke(mcp, value="safe"):
    return asyncio.run(mcp.call_tool("write_test", {"value": value}))


def test_qualified_private_policy_passes_to_original_sdk_handler_once():
    mcp, observed, audit = _rig(policy=_policy())
    response = _invoke(mcp)
    assert response
    assert observed["count"] == 1
    assert audit.events == []


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("missing", "host_policy_unavailable"),
        ("wrong_host", "host_identity_mismatch"),
        ("wrong_revision", "runtime_generation_mismatch"),
        ("expired", "host_policy_expired"),
        ("no_grant", "tool_not_granted_on_host"),
        ("bad_catalogue", "host_policy_catalogue_mismatch"),
        ("provider_error", "host_admission_evidence_unavailable"),
    ],
)
def test_denials_are_audited_before_any_side_effect(case, reason):
    policy = _policy()
    attrs = {"policy": policy}
    if case == "missing":
        attrs["policy"] = None
    elif case == "wrong_host":
        attrs["asset"] = "service:foreign"
    elif case == "wrong_revision":
        attrs["revision"] = "c" * 40
    elif case == "expired":
        attrs["policy"] = replace(policy, expires_at_epoch=1)
    elif case == "no_grant":
        attrs["policy"] = replace(policy, permitted_tool_names=frozenset())
    elif case == "bad_catalogue":
        attrs["policy"] = replace(policy, permitted_tool_names=frozenset({"foreign_tool"}))
    elif case == "provider_error":
        attrs["provider_error"] = True
    mcp, observed, sink = _rig(**attrs)
    with pytest.raises(ToolError, match="HOST_TOOL_NOT_PERMITTED"):
        _invoke(mcp, value="client:/etc/shadow")
    assert observed["count"] == 0
    assert len(sink.events) == 1
    assert sink.events[0].result == "denied:" + reason
    assert "shadow" not in str(sink.events[0])


def test_failing_audit_does_not_execute_tool_or_leak_exception():
    sink = AuditSink(fail=True)
    mcp, observed, _ = _rig(policy=None, audit=sink)
    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$") as exc:
        _invoke(mcp)
    assert "private" not in str(exc.value)
    assert observed["count"] == 0


def test_client_forged_host_and_policy_fields_are_not_trusted():
    mcp, observed, audit = _rig(policy=None)
    with pytest.raises(ToolError, match="HOST_TOOL_NOT_PERMITTED"):
        _invoke(mcp, value="client-says-host-and-policy-permitted")
    assert observed["count"] == 0
    assert len(audit.events) == 1


def test_qualified_tool_catalogue_unchanged_when_guard_installed():
    mcp, _, _ = _rig(policy=None)
    listed = asyncio.run(mcp.list_tools())
    assert {x.name for x in listed} == {"write_test"}


def test_wrong_actual_schema_digest_never_runs_tool():
    sink = AuditSink()
    observed = {"count": 0}

    async def wrong_schema(_):
        return "c" * 64

    mcp = HostAdmissionMCPServer(
        "bad-schema",
        evidence_provider=lambda: HostDispatchEvidence(ASSET, REV, _policy()),
        schema_digest_provider=wrong_schema,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        observed["count"] += 1
        return "unexpected"

    with pytest.raises(ToolError, match="HOST_TOOL_NOT_PERMITTED"):
        asyncio.run(mcp.call_tool("write_test", {}))
    assert observed["count"] == 0
    assert sink.events[0].result == "denied:runtime_generation_mismatch"


@pytest.mark.parametrize("rotation", ["revoked", "foreign_host", "new_revision", "replaced_policy"])
def test_private_owner_rotation_while_schema_awaits_denies_before_handler(rotation):
    sink = AuditSink()
    observed = {"calls": 0}
    owner = {"asset": ASSET, "revision": REV, "policy": _policy()}

    def private_owner():
        return HostDispatchEvidence(
            owner["asset"],
            owner["revision"],
            owner["policy"],
        )

    async def schema_observer(_):
        # This await represents an async catalogue/schema observation. The
        # external owner can revoke/rotate facts during this interruption.
        await asyncio.sleep(0)
        if rotation == "revoked":
            owner["policy"] = None
        elif rotation == "foreign_host":
            owner["asset"] = "service:foreign"
        elif rotation == "new_revision":
            owner["revision"] = "c" * 40
        else:
            owner["policy"] = replace(_policy(), expires_at_epoch=int(time()) + 7200)
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "rotating-owner",
        evidence_provider=private_owner,
        schema_digest_provider=schema_observer,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        observed["calls"] += 1
        return "must-not-write"

    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$"):
        asyncio.run(mcp.call_tool("write_test", {}))
    assert observed["calls"] == 0
    assert len(sink.events) == 1
    assert sink.events[0].result == "denied:host_admission_evidence_changed"


def test_private_owner_second_observation_unavailable_denies_before_handler():
    sink = AuditSink()
    observed = {"calls": 0}
    seen = {"observations": 0}

    def transient_owner():
        seen["observations"] += 1
        if seen["observations"] == 2:
            raise OSError("private/owner/secret/must-not-leak")
        return HostDispatchEvidence(ASSET, REV, _policy())

    async def schema_observer(_):
        await asyncio.sleep(0)
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "lost-owner",
        evidence_provider=transient_owner,
        schema_digest_provider=schema_observer,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        observed["calls"] += 1
        return "must-not-write"

    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$") as exc:
        asyncio.run(mcp.call_tool("write_test", {}))
    assert seen["observations"] == 2
    assert observed["calls"] == 0
    assert len(sink.events) == 1
    assert sink.events[0].result == "denied:host_admission_evidence_unavailable"
    assert "private/owner" not in str(exc.value)


def test_unchanged_private_owner_rechecked_twice_before_one_execution():
    sink = AuditSink()
    seen = {"observations": 0, "executions": 0}
    stable = HostDispatchEvidence(ASSET, REV, _policy())

    def private_owner():
        seen["observations"] += 1
        return stable

    async def schema_observer(_):
        await asyncio.sleep(0)
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "stable-owner",
        evidence_provider=private_owner,
        schema_digest_provider=schema_observer,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        seen["executions"] += 1
        return "complete"

    assert asyncio.run(mcp.call_tool("write_test", {}))
    assert seen == {"observations": 2, "executions": 1}
    assert sink.events == []


def test_unknown_client_tool_name_does_not_enter_existing_audit():
    sink = AuditSink()
    mcp, observed, _ = _rig(policy=_policy(), audit=sink)
    synthetic_secret = "private_token_client_supplied_never_log_123456"
    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$"):
        asyncio.run(mcp.call_tool(synthetic_secret, {"key": synthetic_secret}))
    assert observed["count"] == 0
    assert len(sink.events) == 1
    assert sink.events[0].tool == "unknown_tool"
    assert synthetic_secret not in repr(sink.events[0])


def test_provider_failure_does_not_log_unverified_tool_name():
    mcp, observed, sink = _rig(provider_error=True)
    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$"):
        _invoke(mcp)
    assert observed["count"] == 0
    assert len(sink.events) == 1
    # The provider failed before the SDK catalogue could be verified.
    assert sink.events[0].tool == "unknown_tool"
    assert sink.events[0].result == "denied:host_admission_evidence_unavailable"


@pytest.mark.parametrize("drift", ["schema", "registered_name"])
def test_sdk_catalogue_changed_during_async_digest_denies_without_handler(
    drift: str,
):
    """A single policy decision cannot combine different SDK generations."""
    sink = AuditSink()
    executed = {"count": 0}
    stable = HostDispatchEvidence(ASSET, REV, _policy())

    async def async_schema_observer(_):
        await asyncio.sleep(0)
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "changing-sdk-catalogue",
        evidence_provider=lambda: stable,
        schema_digest_provider=async_schema_observer,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        executed["count"] += 1
        return "must-not-write"

    original_list = mcp.list_tools
    read_count = {"n": 0}

    async def catalogue_observer():
        current = await original_list()
        read_count["n"] += 1
        if read_count["n"] == 2:
            if drift == "schema":
                return [
                    tool.model_copy(update={"input_schema": {"type": "object"}})
                    for tool in current
                ]
            return [
                tool.model_copy(update={"name": "different_registered_tool"})
                for tool in current
            ]
        return current

    mcp.list_tools = catalogue_observer
    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$"):
        asyncio.run(mcp.call_tool("write_test", {}))
    assert read_count["n"] == 2
    assert executed["count"] == 0
    assert len(sink.events) == 1
    assert sink.events[0].tool == "unknown_tool"
    assert sink.events[0].result == "denied:host_tool_catalogue_changed"


def test_identical_sdk_catalogue_after_async_digest_allows_one_handler():
    sink = AuditSink()
    count = {"executions": 0, "catalogue_reads": 0}
    stable = HostDispatchEvidence(ASSET, REV, _policy())

    async def async_schema_observer(_):
        await asyncio.sleep(0)
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "stable-sdk-catalogue",
        evidence_provider=lambda: stable,
        schema_digest_provider=async_schema_observer,
        audit=sink,
    )

    @mcp.tool()
    def write_test() -> str:
        count["executions"] += 1
        return "complete"

    original_list = mcp.list_tools

    async def stable_catalogue():
        count["catalogue_reads"] += 1
        return await original_list()

    mcp.list_tools = stable_catalogue
    result = asyncio.run(mcp.call_tool("write_test", {}))
    assert result
    assert count == {"executions": 1, "catalogue_reads": 2}
    assert sink.events == []


@pytest.mark.parametrize("mutation", ["top_level", "nested"])
def test_in_place_sdk_schema_mutation_during_digest_denies_before_handler(mutation):
    """SDK descriptor aliasing must not erase the original schema snapshot."""
    sink = AuditSink()
    executed = {"count": 0, "reads": 0}
    stable = HostDispatchEvidence(ASSET, REV, _policy())
    shared_tools = []

    async def mutable_schema_digest(_):
        await asyncio.sleep(0)
        schema = shared_tools[0].input_schema
        if mutation == "top_level":
            schema["x-test-schema-change"] = "changed"
        else:
            schema["properties"]["value"]["description"] = "changed"
        return SCHEMA

    mcp = HostAdmissionMCPServer(
        "in-place-sdk-schema",
        evidence_provider=lambda: stable,
        schema_digest_provider=mutable_schema_digest,
        audit=sink,
    )

    @mcp.tool()
    def write_test(value: str) -> str:
        executed["count"] += 1
        return "must-not-write:" + value

    # Model the SDK returning the SAME descriptors before and after the await.
    shared_tools.extend(asyncio.run(mcp.list_tools()))

    async def shared_catalogue():
        executed["reads"] += 1
        return shared_tools

    mcp.list_tools = shared_catalogue
    with pytest.raises(ToolError, match="^HOST_TOOL_NOT_PERMITTED$"):
        asyncio.run(mcp.call_tool("write_test", {"value": "safe"}))
    assert executed == {"count": 0, "reads": 2}
    assert len(sink.events) == 1
    assert sink.events[0].tool == "unknown_tool"
    assert sink.events[0].result == "denied:host_tool_catalogue_changed"
