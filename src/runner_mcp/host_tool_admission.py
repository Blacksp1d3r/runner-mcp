"""Fail-closed host-local MCP tool admission contract (SOURCE ONLY).

Each installation must advertise the same approved Runner-MCP tool catalogue.
Individual hosts may DENY execution without deleting an advertised tool.
This module only evaluates an independently verified host policy; neither a
caller-supplied hostname nor an advertised tool name grants authority.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_TOOL = re.compile(r"^[a-z][a-z0-9_]{2,95}$")
_ASSET = re.compile(r"^[a-z][a-z0-9:._-]{1,127}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_TOOLS = 256
_DENIAL_CODE = "HOST_TOOL_NOT_PERMITTED"


class HostToolPolicyError(ValueError):
    """Malformed or unqualified private host policy."""


@dataclass(frozen=True, slots=True)
class QualifiedHostToolPolicy:
    """Host-local permit data ONLY after external identity/provenance checks.

    This dataclass is deliberately not a signature, credential, source of
    host identity, or public MCP input contract. It must be constructed by
    a trusted local Fabric provisioner from a verified release/binding.
    """

    service_asset_id: str
    release_source_revision: str
    interface_schema_sha256: str
    permitted_tool_names: frozenset[str]
    expires_at_epoch: int

    def __post_init__(self) -> None:
        if (
            type(self.service_asset_id) is not str
            or _ASSET.fullmatch(self.service_asset_id) is None
            or type(self.release_source_revision) is not str
            or _COMMIT.fullmatch(self.release_source_revision) is None
            or type(self.interface_schema_sha256) is not str
            or _DIGEST.fullmatch(self.interface_schema_sha256) is None
            or type(self.permitted_tool_names) is not frozenset
            or len(self.permitted_tool_names) > _MAX_TOOLS
            or any(
                type(tool) is not str
                or _TOOL.fullmatch(tool) is None
                for tool in self.permitted_tool_names
            )
            or type(self.expires_at_epoch) is not int
            or self.expires_at_epoch <= 0
        ):
            raise HostToolPolicyError("host tool policy is invalid")


@dataclass(frozen=True, slots=True)
class HostToolAdmission:
    allowed: bool
    reason_code: str
    response_code: str

    def to_public_payload(self) -> dict[str, object]:
        """Fixed, path-free tool denial appropriate for audited MCP surfaces."""
        return {
            "allowed": self.allowed,
            "reasonCode": self.reason_code,
            "code": self.response_code,
        }


def evaluate_host_tool_admission(
    tool_name: str,
    *,
    registered_tool_names: frozenset[str],
    verified_service_asset_id: str | None,
    runtime_source_revision: str | None,
    runtime_interface_schema_sha256: str | None,
    policy: QualifiedHostToolPolicy | None,
    now_epoch: int,
) -> HostToolAdmission:
    """Return fixed denial unless every independent local fact agrees.

    Verified service identity must come from trusted local provenance, never
    from caller tool inputs, untrusted environment or the policy itself.
    The trusted host identity, policy signature, active process generation,
    exact registered MCP `tools/list`, lifecycle lease and audit write are
    external prerequisites. A positive result does NOT bypass existing
    OperatorSafetyGuard, Fabric policy/lease/fence or high-risk approval gates.
    """
    if (
        type(tool_name) is not str
        or _TOOL.fullmatch(tool_name) is None
        or type(registered_tool_names) is not frozenset
        or len(registered_tool_names) > _MAX_TOOLS
        or any(
            type(name) is not str or _TOOL.fullmatch(name) is None
            for name in registered_tool_names
        )
        or type(now_epoch) is not int
        or now_epoch < 0
        or (policy is not None and not isinstance(policy, QualifiedHostToolPolicy))
    ):
        raise HostToolPolicyError("invalid host tool admission evidence")

    def deny(reason: str) -> HostToolAdmission:
        return HostToolAdmission(False, reason, _DENIAL_CODE)

    if tool_name not in registered_tool_names:
        return deny("tool_not_in_qualified_catalogue")
    if policy is None:
        return deny("host_policy_unavailable")
    if (
        type(verified_service_asset_id) is not str
        or _ASSET.fullmatch(verified_service_asset_id) is None
        or verified_service_asset_id != policy.service_asset_id
    ):
        return deny("host_identity_mismatch")
    if now_epoch >= policy.expires_at_epoch:
        return deny("host_policy_expired")
    if (
        type(runtime_source_revision) is not str
        or _COMMIT.fullmatch(runtime_source_revision) is None
        or type(runtime_interface_schema_sha256) is not str
        or _DIGEST.fullmatch(runtime_interface_schema_sha256) is None
        or runtime_source_revision != policy.release_source_revision
        or runtime_interface_schema_sha256
        != policy.interface_schema_sha256
    ):
        return deny("runtime_generation_mismatch")
    if not policy.permitted_tool_names.issubset(registered_tool_names):
        return deny("host_policy_catalogue_mismatch")
    if tool_name not in policy.permitted_tool_names:
        return deny("tool_not_granted_on_host")
    return HostToolAdmission(True, "exact_host_capability_granted", "OK")
