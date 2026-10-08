from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.artifact_custody import ContentAddressedArtifactCustody
from runner_mcp.bewind_ocr_qualification_source import (
    BewindOcrQualificationSourceProvisionError,
    BewindOcrQualificationSourceProvisioner,
    _EXPECTED_SHA256,
    _EXPECTED_SIZE_BYTES,
    _SOURCE_URL,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


class FakeResponse:
    def __init__(
        self,
        data: bytes,
        *,
        url: str = _SOURCE_URL,
        status: int = 200,
        content_type: str = "application/pdf",
    ) -> None:
        self._data = data
        self._url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, limit: int) -> bytes:
        return self._data[:limit]


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def config_dir(tmp_path: Path) -> Path:
    value = tmp_path / "config"
    value.mkdir(mode=0o700)
    value.chmod(0o700)
    return value


def provisioner(tmp_path: Path, data: bytes, opener):
    config = config_dir(tmp_path)
    return BewindOcrQualificationSourceProvisioner(
        safety=safety(tmp_path),
        config_dir=config,
        custody=ContentAddressedArtifactCustody(config_dir=config),
        opener=opener,
    )


def canonical_pdf_bytes() -> bytes:
    prefix = b"%PDF-1.7\n"
    return prefix + (b"x" * (_EXPECTED_SIZE_BYTES - len(prefix)))


def test_provision_downloads_fixed_source_into_custody_and_binding(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data = canonical_pdf_bytes()
    digest = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(
        "runner_mcp.bewind_ocr_qualification_source._EXPECTED_SHA256",
        digest,
    )
    calls = []

    def opener(request, *, timeout):
        calls.append((request.full_url, timeout))
        return FakeResponse(data)

    manager = provisioner(tmp_path, data, opener)

    result = manager.provision()

    assert calls == [(_SOURCE_URL, 60)]
    assert result["state"] == "ready"
    assert result["cache"] == "miss"
    assert result["bindingReady"] is True
    assert result["normalActivationEnabled"] is False
    binding_path = (
        manager.config_dir
        / "bewind-ocr-qualification"
        / "source-binding.json"
    )
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    assert binding["expected_sha256"] == digest
    assert binding["expected_size_bytes"] == _EXPECTED_SIZE_BYTES
    assert binding["source_id"] == "2026/02/03_1.pdf"
    assert binding_path.stat().st_mode & 0o777 == 0o600
    object_path = Path(binding["source_path"])
    assert object_path.read_bytes() == data
    assert object_path.stat().st_mode & 0o777 == 0o600


def test_existing_exact_cache_object_avoids_redownload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data = canonical_pdf_bytes()
    digest = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(
        "runner_mcp.bewind_ocr_qualification_source._EXPECTED_SHA256",
        digest,
    )
    config = config_dir(tmp_path)
    custody = ContentAddressedArtifactCustody(config_dir=config)
    custody.publish_bytes(
        data=data,
        expected_sha256=digest,
        expected_size_bytes=len(data),
    )

    def opener(*_args, **_kwargs):
        raise AssertionError("cache hit must not redownload")

    manager = BewindOcrQualificationSourceProvisioner(
        safety=safety(tmp_path),
        config_dir=config,
        custody=custody,
        opener=opener,
    )

    result = manager.provision()

    assert result["cache"] == "hit"
    assert result["bindingReady"] is True


@pytest.mark.parametrize(
    "final_url",
    [
        "http://www.ejustice.just.fgov.be/mopdf/2026/02/03_1.pdf",
        "https://example.invalid/mopdf/2026/02/03_1.pdf",
    ],
)
def test_redirect_outside_fixed_https_authority_fails_closed(
    tmp_path: Path,
    final_url: str,
) -> None:
    data = canonical_pdf_bytes()

    def opener(_request, *, timeout):
        assert timeout == 60
        return FakeResponse(data, url=final_url)

    manager = provisioner(tmp_path, data, opener)

    with pytest.raises(
        BewindOcrQualificationSourceProvisionError,
        match="redirect rejected",
    ):
        manager._download()


def test_wrong_size_and_digest_fail_before_custody(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data = canonical_pdf_bytes()
    digest = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(
        "runner_mcp.bewind_ocr_qualification_source._EXPECTED_SHA256",
        digest,
    )
    short = data[:-1]

    manager = provisioner(
        tmp_path,
        short,
        lambda _request, timeout: FakeResponse(short),
    )
    with pytest.raises(
        BewindOcrQualificationSourceProvisionError,
        match="size mismatch",
    ):
        manager.provision()

    wrong = bytearray(data)
    wrong[-1] = ord("y")
    manager2 = provisioner(
        tmp_path / "second",
        bytes(wrong),
        lambda _request, timeout: FakeResponse(bytes(wrong)),
    )
    with pytest.raises(
        BewindOcrQualificationSourceProvisionError,
        match="digest mismatch",
    ):
        manager2.provision()
