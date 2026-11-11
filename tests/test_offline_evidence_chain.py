from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.offline_evidence_chain import offline_evidence_chain_preflight
from runner_mcp.offline_receipt_writer import write_offline_receipt_candidate

SOURCE = "a" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path):
    wheel = tmp_path / "package.whl"
    wheel.write_bytes(b"wheel content")
    digest = _sha(wheel.read_bytes())
    generation = tmp_path / f"generation-{SOURCE}-{digest}"
    generation.mkdir(mode=0o700)
    package = generation / "runner_mcp"
    package.mkdir()
    (package / "module.py").write_bytes(b"module content")
    receipt = tmp_path / "receipt.json"
    assert write_offline_receipt_candidate(receipt, {
        "schema_version": "runner-mcp/offline-artifact-receipt/v1",
        "source_revision": SOURCE,
        "wheel_sha256": digest,
        "modules": {"module.py": _sha(b"module content")},
    })
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": "runner-mcp/builder-manifest/v1",
        "source_revision": SOURCE,
        "distribution_version": "0.1.14",
        "wheel_sha256": digest,
        "interface_schema_digest": "b" * 64,
    }), encoding="utf-8")
    return manifest, receipt, wheel, package, generation, _sha(manifest.read_bytes())


def test_valid_offline_chain_does_not_attest_serving_process(tmp_path: Path):
    result = offline_evidence_chain_preflight(*_fixture(tmp_path))
    assert result["state"] == "offline_candidate_chain_match"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


@pytest.mark.parametrize("mutation", ["manifest", "wheel", "module", "receipt", "generation"])
def test_mutations_break_offline_chain(tmp_path: Path, mutation: str):
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    if mutation == "manifest":
        manifest.write_text("{}", encoding="utf-8")
    elif mutation == "wheel":
        wheel.write_bytes(b"changed wheel")
    elif mutation == "module":
        (package / "module.py").write_bytes(b"changed module")
    elif mutation == "receipt":
        receipt.write_text("{}", encoding="utf-8")
    else:
        generation.rename(tmp_path / "renamed")
    answer = offline_evidence_chain_preflight(
        manifest, receipt, wheel, package, generation, pinned
    )
    assert answer["state"] == "unverified"
    assert answer["active_build_provenance_verified"] is False


def test_inconsistent_source_revision_fails_even_with_valid_individual_hashes(
    tmp_path: Path,
):
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    record = json.loads(receipt.read_text(encoding="utf-8"))
    record["source_revision"] = "c" * 40
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert offline_evidence_chain_preflight(
        manifest, receipt, wheel, package, generation, pinned
    )["state"] == "unverified"


def test_caller_supplied_wrong_pin_fails_closed(tmp_path: Path):
    manifest, receipt, wheel, package, generation, _ = _fixture(tmp_path)
    result = offline_evidence_chain_preflight(
        manifest, receipt, wheel, package, generation, "f" * 64
    )
    assert result["state"] == "unverified"


def test_consistent_but_external_package_is_not_generation_evidence(tmp_path: Path):
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    external = tmp_path / "external_package"
    package.rename(external)
    result = offline_evidence_chain_preflight(
        manifest, receipt, wheel, external, generation, pinned
    )
    assert result["state"] == "unverified"


def test_symlinked_parent_of_package_inside_generation_rejected(tmp_path: Path):
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    alias = generation / "redirect"
    alias.symlink_to(generation, target_is_directory=True)
    linked_package = alias / package.name
    result = offline_evidence_chain_preflight(
        manifest, receipt, wheel, linked_package, generation, pinned
    )
    assert result["state"] == "unverified"


def test_group_writable_installed_package_directory_is_unverified(tmp_path: Path):
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    package.chmod(0o775)
    result = offline_evidence_chain_preflight(
        manifest, receipt, wheel, package, generation, pinned
    )
    assert result["state"] == "unverified"


@pytest.mark.parametrize(
    "aliased",
    ["manifest", "receipt", "wheel", "installed_package", "generation"],
)
def test_offline_chain_rejects_symlinked_ancestor_of_any_evidence(
    tmp_path: Path, aliased: str,
) -> None:
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    linked = tmp_path / "linked-parent"
    linked.symlink_to(tmp_path, target_is_directory=True)
    evidence = {
        "manifest": manifest,
        "receipt": receipt,
        "wheel": wheel,
        "installed_package": package,
        "generation": generation,
    }
    evidence[aliased] = linked / evidence[aliased].relative_to(tmp_path)
    candidate = offline_evidence_chain_preflight(
        evidence["manifest"], evidence["receipt"], evidence["wheel"],
        evidence["installed_package"], evidence["generation"], pinned,
    )
    assert candidate["state"] == "unverified"
    assert candidate["active_build_provenance_verified"] is False
    assert candidate["source_revision"] is None
    assert candidate["artifact_digest"] is None


def test_offline_chain_refuses_lexical_parent_traversal_inside_generation(
    tmp_path: Path,
) -> None:
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    transit = generation / "transit"
    transit.mkdir(mode=0o700)
    alias = transit / ".." / package.name
    assert alias.is_dir() and not alias.is_symlink()
    result = offline_evidence_chain_preflight(
        manifest, receipt, wheel, alias, generation, pinned,
    )
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


@pytest.mark.parametrize("field", ["manifest", "receipt", "wheel", "installed_package", "generation"])
def test_offline_chain_refuses_relative_evidence_inputs(
    tmp_path: Path, field: str,
) -> None:
    manifest, receipt, wheel, package, generation, pinned = _fixture(tmp_path)
    evidence = {
        "manifest": manifest,
        "receipt": receipt,
        "wheel": wheel,
        "installed_package": package,
        "generation": generation,
    }
    evidence[field] = Path(evidence[field].name)
    result = offline_evidence_chain_preflight(
        evidence["manifest"], evidence["receipt"], evidence["wheel"],
        evidence["installed_package"], evidence["generation"], pinned,
    )
    assert result["state"] == "unverified"
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None
