from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.artifact_receipt_preflight import offline_artifact_receipt_preflight


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "module.py").write_bytes(b"safe module")
    wheel = tmp_path / "release.whl"
    wheel.write_bytes(b"fixed wheel bytes")
    receipt = tmp_path / "receipt.json"
    record = {
        "schema_version": "runner-mcp/offline-artifact-receipt/v1",
        "source_revision": "a" * 40,
        "wheel_sha256": _sha(wheel.read_bytes()),
        "modules": {"module.py": _sha(b"safe module")},
    }
    receipt.write_text(json.dumps(record), encoding="utf-8")
    receipt.chmod(0o600)
    return receipt, wheel, package, record


def test_matching_bytes_are_not_serving_attestation(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "offline_bytes_match"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


@pytest.mark.parametrize("mutation", ["wheel", "module", "revision", "digest", "schema", "missing"])
def test_fail_closed_receipt_mutations(tmp_path: Path, mutation: str):
    receipt, wheel, package, record = _fixture(tmp_path)
    if mutation == "wheel":
        wheel.write_bytes(b"replaced")
    elif mutation == "module":
        (package / "module.py").write_bytes(b"modified")
    elif mutation == "revision":
        record["source_revision"] = "not-a-commit"
    elif mutation == "digest":
        record["wheel_sha256"] = "b" * 64
    elif mutation == "schema":
        record["schema_version"] = "v999"
    else:
        receipt.unlink()
    if mutation in ("revision", "digest", "schema"):
        receipt.write_text(json.dumps(record), encoding="utf-8")
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


def test_rejects_module_symlink_and_parent_escape(tmp_path: Path):
    receipt, wheel, package, record = _fixture(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_bytes(b"safe module")
    (package / "module.py").unlink()
    (package / "module.py").symlink_to(outside)
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"
    record["modules"] = {"../outside.py": _sha(b"safe module")}
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


def test_rejects_large_receipt_and_extra_fields(tmp_path: Path):
    receipt, wheel, package, record = _fixture(tmp_path)
    record["untrusted"] = "unexpected"
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"
    receipt.write_bytes(b"x" * 65537)
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"

def test_rejects_partial_module_manifest(tmp_path: Path):
    receipt, wheel, package, record = _fixture(tmp_path)
    (package / "extra.py").write_bytes(b"unlisted file")
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"
    record["modules"] = {}
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


def test_rejects_symlink_package_root(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(package, target_is_directory=True)
    assert offline_artifact_receipt_preflight(receipt, wheel, alias)["state"] == "unverified"


def test_rejects_linked_subdirectory_even_when_manifest_matches(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "hidden.py").write_bytes(b"unsafe")
    (package / "linked").symlink_to(outside, target_is_directory=True)
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


def test_rejects_excessive_package_entries(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    for index in range(8193):
        (package / f"entry{index}").touch()
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


@pytest.mark.parametrize("mode", [0o640, 0o644, 0o660, 0o666])
def test_rejects_nonprivate_receipt_permissions(tmp_path: Path, mode: int):
    receipt, wheel, package, _ = _fixture(tmp_path)
    receipt.chmod(mode)
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


@pytest.mark.parametrize("extension", [".so", ".pyd", ".dll", ".dylib"])
def test_rejects_unaccounted_native_code(tmp_path: Path, extension: str):
    receipt, wheel, package, _ = _fixture(tmp_path)
    (package / f"extension{extension}").write_bytes(b"untracked native module")
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "unverified"


def test_rejects_manifest_claiming_non_python_module(tmp_path: Path):
    receipt, wheel, package, record = _fixture(tmp_path)
    record["modules"] = {"module.txt": _sha(b"safe module")}
    (package / "module.py").rename(package / "module.txt")
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


@pytest.mark.parametrize("target", ["receipt", "wheel"])
def test_rejects_symlinked_evidence_files(tmp_path: Path, target: str):
    receipt, wheel, package, _ = _fixture(tmp_path)
    selected = receipt if target == "receipt" else wheel
    original = tmp_path / f"{target}-original"
    selected.rename(original)
    selected.symlink_to(original)
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


def test_rejects_hardlinked_receipt(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    alias = tmp_path / "receipt-hardlink"
    alias.hardlink_to(receipt)
    assert offline_artifact_receipt_preflight(receipt, wheel, package)["state"] == "unverified"


def test_missing_manifest_module_fails_closed(tmp_path: Path):
    receipt, wheel, package, _ = _fixture(tmp_path)
    (package / "module.py").unlink()
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


@pytest.mark.parametrize("target", ["wheel", "module"])
def test_group_writable_artifact_is_unverified(tmp_path: Path, target: str):
    receipt, wheel, package, _ = _fixture(tmp_path)
    selected = wheel if target == "wheel" else package / "module.py"
    selected.chmod(0o664)
    result = offline_artifact_receipt_preflight(receipt, wheel, package)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


@pytest.mark.parametrize("selected", ["receipt", "wheel", "package"])
def test_standalone_receipt_refuses_symlinked_ancestor(
    tmp_path: Path, selected: str,
) -> None:
    receipt, wheel, package, _ = _fixture(tmp_path)
    linked = tmp_path / "linked-parent"
    linked.symlink_to(tmp_path, target_is_directory=True)
    chosen = {"receipt": receipt, "wheel": wheel, "package": package}
    chosen[selected] = linked / chosen[selected].relative_to(tmp_path)
    assert not chosen[selected].is_symlink()
    observed = offline_artifact_receipt_preflight(
        chosen["receipt"], chosen["wheel"], chosen["package"]
    )
    assert observed["state"] == "unverified"
    assert observed["active_build_provenance_verified"] is False
    assert observed["source_revision"] is None
    assert observed["artifact_digest"] is None


@pytest.mark.parametrize("selected", ["receipt", "wheel", "package"])
def test_standalone_receipt_refuses_relative_evidence(
    tmp_path: Path, selected: str,
) -> None:
    receipt, wheel, package, _ = _fixture(tmp_path)
    chosen = {"receipt": receipt, "wheel": wheel, "package": package}
    chosen[selected] = Path(chosen[selected].name)
    result = offline_artifact_receipt_preflight(
        chosen["receipt"], chosen["wheel"], chosen["package"]
    )
    assert result["state"] == "unverified"
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


@pytest.mark.parametrize("selected", ["receipt", "wheel", "package"])
def test_standalone_receipt_refuses_lexical_parent_alias(
    tmp_path: Path, selected: str,
) -> None:
    receipt, wheel, package, _ = _fixture(tmp_path)
    transit = tmp_path / "transit"
    transit.mkdir()
    chosen = {"receipt": receipt, "wheel": wheel, "package": package}
    chosen[selected] = transit / ".." / chosen[selected].name
    assert chosen[selected].exists()
    result = offline_artifact_receipt_preflight(
        chosen["receipt"], chosen["wheel"], chosen["package"]
    )
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False
