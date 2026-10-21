"""Standalone first-host zipapp synthetic build and CLI denial tests."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.build_fabric_q7_first_host_zipapp import (
    ZipappBuildRefused,
    build_q7_first_host_zipapp,
)

_SOURCE = Path(__file__).resolve().parents[1]


def test_bounded_zipapp_build_is_deterministic_and_disconnected(tmp_path):
    outputs = [tmp_path / "one.pyz", tmp_path / "two.pyz"]
    digests = [
        build_q7_first_host_zipapp(source_root=_SOURCE, destination=path)
        for path in outputs
    ]
    assert digests[0] == digests[1]
    assert outputs[0].stat().st_mode & 0o777 == 0o600
    assert digests[0] == hashlib.sha256(outputs[0].read_bytes()).hexdigest()

    result = subprocess.run(
        [sys.executable, str(outputs[0]), "--help"],
        check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0
    assert "Usage: fabric-q7-first-host.pyz preflight | import" in result.stdout
    assert "NO_INSTALL" not in result.stdout


def test_duplicate_build_never_overwrites_original(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    original = target.read_bytes()
    with pytest.raises(ZipappBuildRefused):
        build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    assert target.read_bytes() == original


def test_missing_source_refuses_without_creating_artifact(tmp_path):
    target = tmp_path / "importer.pyz"
    with pytest.raises(ZipappBuildRefused):
        build_q7_first_host_zipapp(source_root=tmp_path, destination=target)
    assert not target.exists()


def test_unrecognized_invocation_denied_without_fetch_or_write(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    for command in [["evil"], ["--source", "/tmp/evil"], ["--token", "SECRET"]]:
        result = subprocess.run(
            [sys.executable, str(target), *command],
            check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 2
        assert result.stdout.strip() == "WAIT_UNSUPPORTED_ACTION"
    assert list(tmp_path.iterdir()) == [target]


def test_preflight_refuses_unconfigured_source_without_mutation(tmp_path):
    target = tmp_path / "importer.pyz"
    build_q7_first_host_zipapp(source_root=_SOURCE, destination=target)
    sandbox_home = tmp_path / "empty-home"
    sandbox_home.mkdir()
    result = subprocess.run(
        [sys.executable, str(target), "preflight"],
        check=False, cwd=tmp_path, capture_output=True, text=True, timeout=15,
        env={**os.environ, "HOME": str(sandbox_home)},
    )
    assert result.returncode != 0
    assert result.stdout.strip().startswith("WAIT_")
    assert list(sandbox_home.iterdir()) == []
