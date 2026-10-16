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
