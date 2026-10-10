from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "docs" / "standards" / "project_manifest_candidate.yml"
SCHEMA = ROOT / "docs" / "standards" / "project_manifest_candidate.schema.json"


def _fixture() -> tuple[dict, Draft202012Validator]:
    candidate = yaml.safe_load(PROPOSAL.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert isinstance(candidate, dict)
    assert isinstance(schema, dict)
    # Validate the actual published JSON Schema, not a hand-written subset of
    # its vocabulary. No network fetch or operational manifest is involved.
    Draft202012Validator.check_schema(schema)
    return candidate, Draft202012Validator(schema)


def test_unqualified_manifest_example_matches_strict_draft_schema() -> None:
    candidate, validator = _fixture()
    schema = validator.schema
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    validator.validate(candidate)
    assert candidate["proposal_state"] == "BLOCKED_AUTHORITY"
    assert set(candidate["source_of_truth"].values()) == {"UNKNOWN"}
    assert candidate["execution"]["auto_claim"] is False
    assert candidate["privacy"]["personal_data_in_git"] is False
    assert candidate["child_contract"] == ["TASK.md", "STATE.md"]
    # The proposal is not an operational root project.yml and its validation
    # cannot authorize the creation or execution of such a manifest.
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
        (("execution", "max_write_lanes"), True),
        (("execution", "protected_mutations"), "automatic"),
        (("privacy", "personal_data_in_git"), True),
        (("child_contract",), ["STATE.md", "TASK.md"]),
        (("child_contract",), "TASK.md"),
        (("roadmap",), "../other/ROADMAP.md"),
        (("mirrors", "github"), "qualified_primary"),
        (("project_id",), "wrong-project"),
        (("proposal_state",), {"nested": "BLOCKED_AUTHORITY"}),
    ],
)
def test_draft_schema_rejects_forged_authority(
    path: tuple[str, ...], replacement: object
) -> None:
    candidate, validator = _fixture()
    wrong = copy.deepcopy(candidate)
    target = wrong
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(ValidationError):
        validator.validate(wrong)


@pytest.mark.parametrize(
    ("field", "private_value"),
    [
        ("real_mount", "/some/private-location"),
        ("credential", "PRIVATE_VALUE"),
        ("executor", "generic_shell"),
        ("approved_by", "self"),
    ],
)
def test_draft_schema_rejects_unknown_private_or_authority_fields(
    field: str, private_value: str
) -> None:
    candidate, validator = _fixture()
    candidate[field] = private_value
    with pytest.raises(ValidationError):
        validator.validate(candidate)


@pytest.mark.parametrize(
    ("section", "new_key"),
    [
        ("source_of_truth", "private_path"),
        ("mirrors", "verified_local_primary"),
        ("execution", "target_host"),
        ("privacy", "token"),
    ],
)
def test_draft_schema_rejects_extra_nested_authority_fields(
    section: str, new_key: str
) -> None:
    candidate, validator = _fixture()
    candidate[section][new_key] = "untrusted"
    with pytest.raises(ValidationError):
        validator.validate(candidate)


@pytest.mark.parametrize(
    ("path",),
    [
        (("source_of_truth", "code"),),
        (("execution", "auto_claim"),),
        (("privacy", "synthetic_tests_only"),),
        (("proposal_state",),),
    ],
)
def test_draft_schema_rejects_missing_required_fields(
    path: tuple[str, ...],
) -> None:
    candidate, validator = _fixture()
    target = candidate
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    with pytest.raises(ValidationError):
        validator.validate(candidate)


def test_draft_schema_rejects_nonobject_document() -> None:
    _, validator = _fixture()
    for wrong in (None, [], "BLOCKED_AUTHORITY"):
        with pytest.raises(ValidationError):
            validator.validate(wrong)
