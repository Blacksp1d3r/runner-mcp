"""Source-only bounded tool registry collision and witness consistency preflight.

The provenance of registry entries must be authenticated independently. This
module verifies structural consistency, not request authorization or server
identity. It never executes tools or performs network I/O.
"""
from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from runner_mcp.tool_identity_classifier import (
    ToolContract,
    ToolIdentityReason,
    classify_tool_contract,
)


class ToolInventoryReason(StrEnum):
    READY = "READY"
    UNTRUSTED_INVENTORY = "UNTRUSTED_INVENTORY"
    STALE_INVENTORY = "STALE_INVENTORY"
    DUPLICATE_TOOL_ID = "DUPLICATE_TOOL_ID"
    DUPLICATE_TOOL_NAME = "DUPLICATE_TOOL_NAME"
    INVALID_TOOL_CONTRACT = "INVALID_TOOL_CONTRACT"
    INVENTORY_MISMATCH = "INVENTORY_MISMATCH"
    INVENTORY_TOO_LARGE = "INVENTORY_TOO_LARGE"


def classify_tool_inventory(
    expected: Sequence[ToolContract],
    observed: Sequence[ToolContract],
    *,
    registry_trusted: bool,
    observed_authenticated: bool,
    inventory_fresh: bool,
) -> ToolInventoryReason:
    """Compare two bounded inventories; READY is never execution authority."""
    if any(
        not isinstance(value, bool)
        for value in (registry_trusted, observed_authenticated, inventory_fresh)
    ):
        return ToolInventoryReason.UNTRUSTED_INVENTORY
    if not registry_trusted or not observed_authenticated:
        return ToolInventoryReason.UNTRUSTED_INVENTORY
    if not inventory_fresh:
        return ToolInventoryReason.STALE_INVENTORY
    if (
        not isinstance(expected, (list, tuple))
        or not isinstance(observed, (list, tuple))
    ):
        return ToolInventoryReason.INVALID_TOOL_CONTRACT
    if len(expected) > 256 or len(observed) > 256:
        return ToolInventoryReason.INVENTORY_TOO_LARGE
    indexed: list[dict[str, ToolContract]] = []
    for collection in (expected, observed):
        names: dict[str, ToolContract] = {}
        stable_ids: set[str] = set()
        for contract in collection:
            if not isinstance(contract, ToolContract):
                return ToolInventoryReason.INVALID_TOOL_CONTRACT
            reason = classify_tool_contract(
                contract,
                contract,
                namespace="com.aifordable.runner-mcp",
                registry_trusted=True,
                observed_authenticated=True,
                runtime_reachable=True,
                inventory_fresh=True,
            )
            if reason is ToolIdentityReason.UNTRUSTED_TOOL_IDENTITY:
                return ToolInventoryReason.INVALID_TOOL_CONTRACT
            if contract.stable_id in stable_ids:
                return ToolInventoryReason.DUPLICATE_TOOL_ID
            if contract.tool_name in names:
                return ToolInventoryReason.DUPLICATE_TOOL_NAME
            stable_ids.add(contract.stable_id)
            names[contract.tool_name] = contract
        indexed.append(names)
    registry, witness = indexed
    if registry.keys() != witness.keys():
        return ToolInventoryReason.INVENTORY_MISMATCH
    for name, contract in registry.items():
        reason = classify_tool_contract(
            contract,
            witness[name],
            namespace="com.aifordable.runner-mcp",
            registry_trusted=True,
            observed_authenticated=True,
            runtime_reachable=True,
            inventory_fresh=True,
        )
        if reason is not ToolIdentityReason.READY:
            return ToolInventoryReason.INVENTORY_MISMATCH
    return ToolInventoryReason.READY
