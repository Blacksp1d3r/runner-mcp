"""Pure fail-closed comparison of independently witnessed MCP tool contracts.

This helper MUST NOT grant dispatch authority. Registry and witnessed inventory
MUST be supplied by independently authenticated sources; request-declared names,
versions, namespace markers and hashes alone never authenticate identity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_NAMESPACE = "com.aifordable.runner-mcp"
_ID = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_NAME = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


class ToolIdentityReason(StrEnum):
    READY = "READY"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    TOOL_DISABLED = "TOOL_DISABLED"
    RUNTIME_UNREACHABLE = "RUNTIME_UNREACHABLE"
    UNTRUSTED_TOOL_IDENTITY = "UNTRUSTED_TOOL_IDENTITY"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    STALE_INVENTORY = "STALE_INVENTORY"


@dataclass(frozen=True, slots=True)
class ToolContract:
    tool_name: str
    stable_id: str
    schema_digest: str
    revision: int
    enabled: bool = True


def classify_tool_contract(
    expected: ToolContract | None,
    observed: ToolContract | None,
    *,
    namespace: str,
    registry_trusted: bool,
    observed_authenticated: bool,
    runtime_reachable: bool,
    inventory_fresh: bool,
) -> ToolIdentityReason:
    """Classify pre-dispatch compatibility without executing any tool.

    READY means ONLY that contract metadata compares equal. Dispatch must still
    enforce actual serving process, caller, tenant, host and operation policy.
    """
    if any(
        not isinstance(flag, bool)
        for flag in (
            registry_trusted,
            observed_authenticated,
            runtime_reachable,
            inventory_fresh,
        )
    ):
        return ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    if not runtime_reachable:
        return ToolIdentityReason.RUNTIME_UNREACHABLE
    if not registry_trusted or not observed_authenticated or namespace != _NAMESPACE:
        return ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    if not inventory_fresh:
        return ToolIdentityReason.STALE_INVENTORY
    if expected is None:
        return ToolIdentityReason.UNKNOWN_TOOL
    if observed is None:
        return ToolIdentityReason.VERSION_MISMATCH
    if not isinstance(expected, ToolContract) or not isinstance(observed, ToolContract):
        return ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    for contract in (expected, observed):
        if (
            not isinstance(contract.tool_name, str)
            or not _NAME.fullmatch(contract.tool_name)
            or not isinstance(contract.stable_id, str)
            or not _ID.fullmatch(contract.stable_id)
            or not isinstance(contract.schema_digest, str)
            or not _HASH.fullmatch(contract.schema_digest)
            or isinstance(contract.revision, bool)
            or not isinstance(contract.revision, int)
            or not 1 <= contract.revision <= 65535
            or not isinstance(contract.enabled, bool)
        ):
            return ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    if (
        expected.tool_name != observed.tool_name
        or expected.stable_id != observed.stable_id
    ):
        return ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY
    if not expected.enabled or not observed.enabled:
        return ToolIdentityReason.TOOL_DISABLED
    if expected.revision != observed.revision:
        return ToolIdentityReason.VERSION_MISMATCH
    if expected.schema_digest != observed.schema_digest:
        return ToolIdentityReason.SCHEMA_MISMATCH
    return ToolIdentityReason.READY
