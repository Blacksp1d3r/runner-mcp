"""Offline #662 release-reservation and regression tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "check_release_reservation.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("release_reservation", SCRIPT)
assert spec is not None and spec.loader is not None
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)

MAIN = "a" * 40
HEAD = "b" * 40


def _run(**replacements: object) -> None:
    fields = {
        "main_sha": MAIN,
        "event_base_sha": MAIN,
        "event_head_sha": HEAD,
        "checkout_pr_sha": HEAD,
        "main_version": "0.1.41",
        "proposed_version": "0.1.42",
        "competing_versions": {743: "0.1.41", 745: "0.1.43"},
        "own_number": 760,
    }
    fields.update(replacements)
    admission.validate(**fields)


def test_first_unique_next_patch_accepted() -> None:
    _run()


@pytest.mark.parametrize(
    "changes",
    [
        {"proposed_version": "0.1.41"},
        {"proposed_version": "0.1.40"},
        {"proposed_version": "0.1.43"},
        {"proposed_version": "0.2.0"},
        {"proposed_version": "0.1.42.dev1"},
        {"main_version": "0.1.42"},
        {"main_sha": "invalid"},
        {"event_base_sha": "c" * 40},
        {"event_head_sha": "c" * 40},
        {"checkout_pr_sha": "c" * 40},
        {"own_number": 0},
        {"own_number": True},
        {"competing_versions": {743: "0.1.42"}},
        {"competing_versions": {745: "0.1.42", 746: "0.1.42"}},
        {"competing_versions": {760: "0.1.42"}},
        {"competing_versions": {744: "bad-version"}},
    ],
)
def test_stale_wrong_or_competing_candidate_refuses(changes: dict) -> None:
    with pytest.raises((admission.AdmissionError, ValueError)):
        _run(**changes)


def test_duplicate_json_fields_fail_closed() -> None:
    with pytest.raises(admission.AdmissionError):
        admission._json(b'{"head":"a","head":"b"}')


def test_source_version_requires_canonical_toml() -> None:
    assert admission._project_version(
        b'[project]\nversion = "0.1.42"\n'
    ) == "0.1.42"
    with pytest.raises(admission.AdmissionError):
        admission._project_version(b"[project]\nversion = true\n")


def test_non_pr_event_does_not_reserve_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    assert admission.run() == "SKIP non-PR"


def test_bad_read_only_api_response_is_not_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_path: str, _token: str) -> object:
        raise admission.AdmissionError("GitHub evidence unavailable")

    monkeypatch.setattr(admission, "_api", unavailable)
    with pytest.raises(admission.AdmissionError):
        admission._main_head("synthetic")


def test_negative_duplicate_head_and_invalid_inventory_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def bad_rows(_path: str, _token: str) -> object:
        return [{"number": False, "draft": False, "base": {"ref": "main"}}]

    monkeypatch.setattr(admission, "_api", bad_rows)
    with pytest.raises(admission.AdmissionError):
        admission._contenders("synthetic", own_number=760)


def test_failed_main_head_authentication_never_uses_other_host_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid(_path: str, _token: str) -> object:
        return {"commit": {"sha": None}}

    monkeypatch.setattr(admission, "_api", invalid)
    with pytest.raises(admission.AdmissionError):
        admission._main_head("synthetic")


def test_readonly_preflight_has_no_host_mutation_or_public_promotion() -> None:
    _run()
    assert not hasattr(admission, "install")
    assert not hasattr(admission, "deploy")



def test_draft_and_stacked_prs_do_not_claim_active_merge_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {"number": 743, "state": "open", "draft": False, "base": {"ref": "main"}, "head": {"sha": "c" * 40}},
        {"number": 745, "state": "open", "draft": False, "base": {"ref": "other-branch"}, "head": {"sha": "d" * 40}},
        {"number": 750, "state": "open", "draft": True, "base": {"ref": "main"}, "head": {"sha": "e" * 40}},
        {"number": 760, "state": "open", "draft": False, "base": {"ref": "main"}, "head": {"sha": "b" * 40}},
    ]
    monkeypatch.setattr(admission, "_api", lambda *_: rows)
    seen: list[str] = []

    def version(_token: str, sha: str) -> str:
        seen.append(sha)
        return "0.1.42"

    monkeypatch.setattr(admission, "_version_at", version)
    assert admission._contenders("synthetic", 760) == {743: "0.1.42"}
    assert seen == ["c" * 40]


def test_documentation_only_pr_skips_without_api_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    event = {
        "pull_request": {
            "number": 760,
            "base": {"ref": "main", "sha": MAIN},
            "head": {"sha": HEAD},
        }
    }
    marker = tmp_path / "event.json"
    marker.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REPOSITORY", admission.REPO)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(marker))
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic")
    monkeypatch.setattr(admission, "_git", lambda *_: "handover/CURRENT_STATE.md")

    def should_not_call(_token: str) -> str:
        raise AssertionError("docs-only PR must not consume source-release authority")

    monkeypatch.setattr(admission, "_main_head", should_not_call)
    assert admission.run() == "SKIP docs-only"


@pytest.mark.parametrize(
    "payload",
    [
        {"encoding": "none", "content": "aW52YWxpZA=="},
        {"encoding": "base64", "content": "!" * 100_000},
        {"encoding": "base64", "content": "%%%"},
    ],
)
def test_bad_project_metadata_cannot_supply_release_identity(
    monkeypatch: pytest.MonkeyPatch, payload: dict
) -> None:
    monkeypatch.setattr(admission, "_api", lambda *_: payload)
    with pytest.raises(admission.AdmissionError):
        admission._version_at("synthetic", MAIN)



def test_oldest_ready_pr_wins_duplicate_version_without_mutual_deadlock() -> None:
    _run(
        own_number=743,
        competing_versions={745: "0.1.42", 760: "0.1.42"},
    )
    with pytest.raises(admission.AdmissionError, match="prioritized to PR #743"):
        _run(
            own_number=745,
            competing_versions={743: "0.1.42", 760: "0.1.42"},
        )


@pytest.mark.parametrize(
    "bad",
    [
        {"number": 760, "state": "closed", "draft": False},
        {"number": 760, "state": "open", "draft": True},
        {"number": 760, "state": "open", "draft": False, "head": {"sha": "c" * 40}},
        {"number": 760, "state": "open", "draft": False, "base": {"ref": "other"}},
        {"number": 760, "state": "open", "draft": False, "base": {"sha": "c" * 40}},
    ],
)
def test_current_pr_identity_must_still_be_open_and_match_exact_head(
    monkeypatch: pytest.MonkeyPatch,
    bad: dict[str, object],
) -> None:
    candidate = {
        "number": 760,
        "state": "open",
        "draft": False,
        "base": {"ref": "main", "sha": MAIN},
        "head": {"sha": HEAD},
    }
    candidate.update(bad)
    monkeypatch.setattr(admission, "_api", lambda *_: candidate)
    with pytest.raises(admission.AdmissionError):
        admission._check_current_pr("synthetic", 760, MAIN, HEAD)


def test_current_pr_identity_accepts_exact_ready_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = {
        "number": 760,
        "state": "open",
        "draft": False,
        "base": {"ref": "main", "sha": MAIN},
        "head": {"sha": HEAD},
    }
    monkeypatch.setattr(admission, "_api", lambda *_: current)
    admission._check_current_pr("synthetic", 760, MAIN, HEAD)


@pytest.mark.parametrize("fault", ["unknown-draft", "unknown-base", "duplicated"])
def test_partial_or_repeated_inventory_cannot_make_fake_unique_version(
    monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    item = {
        "number": 744, "state": "open", "draft": False,
        "base": {"ref": "main"}, "head": {"sha": "c" * 40},
    }
    if fault == "unknown-draft":
        item.pop("draft")
    if fault == "unknown-base":
        item.pop("base")
    rows = [item, dict(item)] if fault == "duplicated" else [item]
    monkeypatch.setattr(admission, "_api", lambda *_: rows)
    monkeypatch.setattr(admission, "_version_at", lambda *_: "0.1.42")
    with pytest.raises(admission.AdmissionError):
        admission._contenders("synthetic", 760)
