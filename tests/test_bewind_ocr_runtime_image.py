from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from runner_mcp.bewind_ocr_runtime_image import (
    BewindOcrRuntimeImagePrepareError,
    BewindOcrRuntimeImagePreparer,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def trusted_image(fingerprint: str = "a" * 64) -> dict:
    return {
        "fingerprint": fingerprint,
        "type": "virtual-machine",
        "aliases": [{"name": "aifordable/bewind-ocr-runtime-v1"}],
        "properties": {
            "aifordable.profile": "bewind-ocr-runtime-v1",
            "aifordable.runtime": "ocrmypdf-tesseract-nld-fra-deu-ready",
            "aifordable.user": "fabric:1000:1000",
            "aifordable.base": "aifordable/bewind-ocr-podman-v1",
            "aifordable.languages": "nld+fra+deu",
        },
    }


def completed(stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess([], returncode, stdout, "")


def test_existing_trusted_image_is_idempotent(tmp_path: Path) -> None:
    calls = []

    def runner(argv, **_kwargs):
        calls.append(argv)
        if argv[1:4] == ("image", "list", "--format=json"):
            return completed(json.dumps([trusted_image()]))
        raise AssertionError(argv)

    result = BewindOcrRuntimeImagePreparer(
        safety=safety(tmp_path),
        hostname_provider=lambda: "aifordable-lab",
        runner=runner,
    ).prepare()

    assert result["state"] == "ready"
    assert result["cache"] == "hit"
    assert result["normalActivationEnabled"] is False
    assert len(calls) == 1


def test_wrong_runtime_metadata_fails_closed(tmp_path: Path) -> None:
    bad = trusted_image()
    bad["properties"]["aifordable.runtime"] = "podman-rootless-ready"

    def runner(argv, **_kwargs):
        if argv[1:4] == ("image", "list", "--format=json"):
            return completed(json.dumps([bad]))
        raise AssertionError(argv)

    with pytest.raises(
        BewindOcrRuntimeImagePrepareError,
        match="metadata_mismatch",
    ):
        BewindOcrRuntimeImagePreparer(
            safety=safety(tmp_path),
            hostname_provider=lambda: "aifordable-lab",
            runner=runner,
        ).prepare()


def test_preparer_uses_fixed_install_and_publishes_profile(tmp_path: Path) -> None:
    calls = []
    inventories = iter([[], [], [trusted_image("b" * 64)]])

    def runner(argv, **_kwargs):
        calls.append(argv)
        args = argv[1:]
        if args == ("image", "list", "--format=json"):
            return completed(json.dumps(next(inventories)))
        if args == ("list", "--format=json"):
            return completed("[]")
        if args[:3] == ("exec", "rf-bewind-ocr-runtime-builder", "--"):
            if args[-2:] == ("tesseract", "--list-langs"):
                return completed("List of available languages (3):\nnld\nfra\ndeu\n")
            return completed()
        return completed()

    result = BewindOcrRuntimeImagePreparer(
        safety=safety(tmp_path),
        hostname_provider=lambda: "aifordable-lab",
        runner=runner,
        sleep=lambda _seconds: None,
    ).prepare()

    assert result["state"] == "prepared"
    assert result["cache"] == "miss"
    flattened = [tuple(call[1:]) for call in calls]
    assert (
        "launch",
        "local:aifordable/bewind-ocr-podman-v1",
        "rf-bewind-ocr-runtime-builder",
        "--vm",
    ) in flattened
    install = next(
        args for args in flattened
        if "apt-get" in args and "install" in args
    )
    assert "ocrmypdf" in install
    assert "tesseract-ocr-nld" in install
    assert "tesseract-ocr-fra" in install
    assert "tesseract-ocr-deu" in install
    assert "poppler-utils" in install
    assert (
        "publish",
        "rf-bewind-ocr-runtime-builder",
        "--alias",
        "aifordable/bewind-ocr-runtime-v1",
    ) in flattened
    assert any(
        args[:3] == ("image", "set-property", "aifordable/bewind-ocr-runtime-v1")
        and "aifordable.runtime" in args
        for args in flattened
    )


def test_wrong_host_is_rejected_without_incus(tmp_path: Path) -> None:
    def runner(*_args, **_kwargs):
        raise AssertionError("must not call incus")

    with pytest.raises(
        BewindOcrRuntimeImagePrepareError,
        match="host_mismatch",
    ):
        BewindOcrRuntimeImagePreparer(
            safety=safety(tmp_path),
            hostname_provider=lambda: "other-worker",
            runner=runner,
        ).prepare()
