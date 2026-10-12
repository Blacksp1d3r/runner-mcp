"""Synthetic negative contract tests; does not test live routing or auth."""
import copy

import pytest

from runner_mcp.tool_identity_registry import (
    RegistryContractError,
    canonical_digest,
    validate_registry,
)


def registry():
    return {"schemaVersion": "runner-mcp/tool-id-registry/v1",
            "namespace": "com.aifordable.runner-mcp", "tools": [
        {"tool_id": "RMCP-000001", "tool_name": "synthetic_read", "contract_revision": 1,
         "input_schema_sha256": "a"*64, "output_schema_sha256": "b"*64,
         "permission_class": "read", "status": "active"}]}

def test_valid_and_canonical_hash():
    assert validate_registry(registry()) == (("com.aifordable.runner-mcp", "RMCP-000001", 1),)
    assert canonical_digest({"z": 1, "a": [1,2]}) == canonical_digest({"a": [1,2], "z": 1})

@pytest.mark.parametrize("mutation", ["duplicate", "foreign", "bool_revision", "wrong_digest",
                                        "name_collision", "invalid_permission"])
def test_bad_registry_fails_closed(mutation):
    item = registry()
    entry = item["tools"][0]
    if mutation == "duplicate": item["tools"].append(copy.deepcopy(entry))
    elif mutation == "foreign": item["namespace"] = "foreign"
    elif mutation == "bool_revision": entry["contract_revision"] = True
    elif mutation == "wrong_digest": entry["input_schema_sha256"] = "bad"
    elif mutation == "name_collision":
        clone = copy.deepcopy(entry); clone["tool_id"] = "RMCP-000002"
        item["tools"].append(clone)
    else: entry["permission_class"] = "superuser"
    with pytest.raises(RegistryContractError):
        validate_registry(item)

def test_immutable_retirement_and_revision():
    previous = registry()
    changed = registry(); changed["tools"][0]["status"] = "retired"
    with pytest.raises(RegistryContractError):
        validate_registry(changed, previous=previous)
    changed = registry(); changed["tools"][0]["output_schema_sha256"] = "f"*64
    with pytest.raises(RegistryContractError):
        validate_registry(changed, previous=previous)
    changed = registry(); clone = copy.deepcopy(changed["tools"][0])
    clone["contract_revision"] = 2; clone["output_schema_sha256"] = "f"*64
    changed["tools"].append(clone)
    assert len(validate_registry(changed, previous=previous)) == 2

def test_bad_json_rejected():
    with pytest.raises(RegistryContractError):
        canonical_digest({"invalid": float("nan")})


def test_same_id_cannot_alias_second_name_in_new_revision():
    current = registry()
    alias = copy.deepcopy(current["tools"][0])
    alias["contract_revision"] = 2
    alias["tool_name"] = "different_operation"
    current["tools"].append(alias)
    with pytest.raises(RegistryContractError, match="multiple tool names"):
        validate_registry(current)


@pytest.mark.parametrize("field,value", [
    ("permission_class", []),
    ("status", {"unexpected": True}),
])
def test_malformed_policy_descriptor_fails_closed(field, value):
    current = registry()
    current["tools"][0][field] = value
    with pytest.raises(RegistryContractError, match="invalid policy descriptor"):
        validate_registry(current)
