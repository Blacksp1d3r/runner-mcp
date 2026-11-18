from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.generation_layout_preflight import offline_generation_layout_preflight

SOURCE = "a" * 40
WHEEL = "b" * 64


def _generation(tmp_path: Path) -> Path:
    path = tmp_path / f"generation-{SOURCE}-{WHEEL}"
    path.mkdir(mode=0o700)
    return path


def test_matching_generation_layout_never_claims_active_process(tmp_path: Path):
    generation = _generation(tmp_path)
    result = offline_generation_layout_preflight(generation, SOURCE, WHEEL)
    assert result["state"] == "offline_layout_match"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


@pytest.mark.parametrize("source,wheel", [("bad", WHEEL), (SOURCE, "bad"), ("c" * 40, WHEEL)])
def test_wrong_generation_identity_fail_closed(
    tmp_path: Path, source: str, wheel: str
):
    generation = _generation(tmp_path)
    assert (
        offline_generation_layout_preflight(generation, source, wheel)["state"]
        == "unverified"
    )


def test_symlink_generation_root_fails(tmp_path: Path):
    generation = _generation(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(generation, target_is_directory=True)
    assert offline_generation_layout_preflight(alias, SOURCE, WHEEL)["state"] == "unverified"


def test_symlink_grandparent_fails(tmp_path: Path):
    original = tmp_path / "real"
    original.mkdir()
    nested = original / "nested"
    nested.mkdir()
    generation = nested / f"generation-{SOURCE}-{WHEEL}"
    generation.mkdir()
    alias = tmp_path / "linked"
    alias.symlink_to(original, target_is_directory=True)
    assert (
        offline_generation_layout_preflight(
            alias / "nested" / generation.name, SOURCE, WHEEL
        )["state"]
        == "unverified"
    )


def test_world_writable_generation_rejected(tmp_path: Path):
    generation = _generation(tmp_path)
    generation.chmod(0o777)
    assert offline_generation_layout_preflight(generation, SOURCE, WHEEL)["state"] == "unverified"


def test_relative_generation_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    generation = _generation(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert (
        offline_generation_layout_preflight(Path(generation.name), SOURCE, WHEEL)[
            "state"
        ]
        == "unverified"
    )


def test_parent_traversal_rejected(tmp_path: Path):
    generation = _generation(tmp_path)
    path = tmp_path / "tmp" / ".." / generation.name
    assert offline_generation_layout_preflight(path, SOURCE, WHEEL)["state"] == "unverified"
