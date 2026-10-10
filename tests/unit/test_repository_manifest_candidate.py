from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "docs" / "standards" / "project_manifest_candidate.yml"
SCHEMA = ROOT / "docs" / "standards" / "project_manifest_candidate.schema.json"


def _assert_draft_contract(schema: dict, value: object) -> None:
    """Validate only the small JSON-Schema vocabulary used by this proposal.

    This is an offline source test, not a runtime policy engine or an
    authorization to promote a project.yml.
    """
    if "const" in schema:
        expected = schema["const"]
        assert type(value) is type(expected) and value == expected
    if schema.get("type") == "object":
        assert isinstance(value, dict)
        keys = set(value)
        required = set(schema["required"])
        assert required <= keys
        properties = schema["properties"]
        if schema.get("additionalProperties") is False:
            assert keys <= set(properties)
        for key in keys:
            _assert_draft_contract(properties[key], value[key])
    elif schema.get("type") == "string":
        assert type(value) is str
        if "enum" in schema:
            assert value in schema["enum"]


def _fixture() -> tuple[dict, dict]:
    candidate = yaml.safe_load(PROPOSAL.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert isinstance(candidate, dict)
    assert isinstance(schema, dict)
    return candidate, schema


def test_unqualified_manifest_example_matches_strict_draft_schema() -> None:
    candidate, schema = _fixture()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    _assert_draft_contract(schema, candidate)
    assert candidate["proposal_state"] == "BLOCKED_AUTHORITY"
    assert set(candidate["source_of_truth"].values()) == {"UNKNOWN"}
    assert candidate["execution"]["auto_claim"] is False
    assert candidate["privacy"]["personal_data_in_git"] is False
    assert candidate["child_contract"] == ["TASK.md", "STATE.md"]
    # The proposal is not the root runtime project.yml, and no promotion
    # into one may be inferred by the existence of this documentation.
    assert PROPOSAL.name != "project.yml"
    assert PROPOSAL.parent != ROOT


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("proposal_state",), "QUALIFIED"),
        (("source_of_truth", "code"), "local_git"),
        (("source_of_truth", "evidence"), "local_evidence_registry"),
        (("source_of_truth", "coordination"), "local_queue"),
        (("execution", "auto_claim"), True),
        (("execution", "max_write_lanes"), 2),
        (("execution", "protected_mutations"), "automatic"),
        (("privacy", "personal_data_in_git"), True),
        (("child_contract",), ["STATE.md", "TASK.md"]),
        (("roadmap",), "../other/ROADMAP.md"),
        (("mirrors", "github"), "qualified_primary"),
        (("project_id",), "wrong-project"),
    ],
)
def test_draft_contract_rejects_forged_authority(
    path: tuple[str, ...], replacement: object
) -> None:
    candidate, schema = _fixture()
    wrong = copy.deepcopy(candidate)
    target = wrong
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(AssertionError):
        _assert_draft_contract(schema, wrong)


@pytest.mark.parametrize(
    ("field", "private_value"),
    [
        ("real_mount", "/srv/private-disk"),
        ("credential", "SECRET_VALUE"),
        ("executor", "generic_shell"),
        ("approved_by", "self"),
    ],
)
def test_draft_contract_rejects_unknown_private_or_authority_fields(
    field: str, private_value: str
) -> None:
    candidate, schema = _fixture()
    candidate[field] = private_value
    with pytest.raises(AssertionError):
        _assert_draft_contract(schema, candidate)
