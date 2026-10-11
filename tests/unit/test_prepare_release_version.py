"""Version allocator does not deploy and refuses stale or ambiguous release state."""

import importlib.util
import json
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "scripts/prepare_release_version.py"
_SPEC = importlib.util.spec_from_file_location("runner_mcp_version_allocator", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


@pytest.mark.parametrize(("kind", "expected"), [
    ("patch", "0.1.5"),
    ("minor", "0.2.0"),
    ("major", "1.0.0"),
])
def test_next_version(kind, expected):
    assert _MOD.next_version("0.1.4", kind) == expected


def _fixture(tmp_path):
    (tmp_path / "src/runner_mcp").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.4"\n')
    (tmp_path / "server.json").write_text(
        json.dumps({"version": "0.1.4", "packages": [{"version": "0.1.4"}]})
    )
    (tmp_path / "glama.json").write_text(json.dumps({"version": "0.1.4"}))
    (tmp_path / "src/runner_mcp/__init__.py").write_text('__version__ = "0.1.4"\n')


def test_dry_run_renders_all_four_metadata_files(tmp_path, monkeypatch):
    _fixture(tmp_path)
    monkeypatch.setattr(_MOD, "_git", lambda *args: "a" * 40 if "rev-parse" in args else "")
    version, plan = _MOD.plan(
        root=tmp_path, kind="patch", expected_version="0.1.4", expected_head="a" * 40
    )
    assert version == "0.1.5"
    assert len(plan) == 4
    assert all(b"0.1.5" in content for content in plan.values())
    assert (tmp_path / "pyproject.toml").read_text().endswith('0.1.4"\n')


def test_stale_expected_revision_refuses_without_changes(tmp_path, monkeypatch):
    _fixture(tmp_path)
    monkeypatch.setattr(_MOD, "_git", lambda *args: "b" * 40)
    before = (tmp_path / "pyproject.toml").read_bytes()
    with pytest.raises(_MOD.VersionAllocationError, match="HEAD changed"):
        _MOD.plan(
            root=tmp_path, kind="minor",
            expected_version="0.1.4", expected_head="a" * 40
        )
    assert (tmp_path / "pyproject.toml").read_bytes() == before


def test_conflicting_version_refuses(tmp_path, monkeypatch):
    _fixture(tmp_path)
    monkeypatch.setattr(_MOD, "_git", lambda *args: "a" * 40 if "rev-parse" in args else "")
    with pytest.raises(_MOD.VersionAllocationError, match="source version has changed"):
        _MOD.plan(
            root=tmp_path, kind="patch",
            expected_version="0.1.3", expected_head="a" * 40
        )


def test_metadata_symlink_outside_repo_is_denied(tmp_path, monkeypatch):
    _fixture(tmp_path)
    outside = tmp_path.parent / "release-metadata-outside-guard.json"
    outside.write_text(json.dumps({"version": "0.1.4"}))
    glama = tmp_path / "glama.json"
    glama.unlink()
    glama.symlink_to(outside)
    monkeypatch.setattr(_MOD, "_git", lambda *args: "a" * 40 if "rev-parse" in args else "")
    with pytest.raises(_MOD.VersionAllocationError, match="unsafe"):
        _MOD.plan(
            root=tmp_path, kind="patch",
            expected_version="0.1.4", expected_head="a" * 40
        )
    assert json.loads(outside.read_text())["version"] == "0.1.4"


def test_cli_apply_updates_all_four_files(tmp_path, monkeypatch):
    import sys

    _fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_MOD, "_git", lambda *args: "a" * 40 if "rev-parse" in args else "")
    monkeypatch.setattr(sys, "argv", [
        "prepare_release_version.py", "--kind", "patch", "--expected-version",
        "0.1.4", "--expected-head", "a" * 40, "--apply",
    ])
    assert _MOD.main() == 0
    assert 'version = "0.1.5"' in (tmp_path / "pyproject.toml").read_text()
    assert json.loads((tmp_path / "server.json").read_text())["version"] == "0.1.5"
    assert json.loads((tmp_path / "glama.json").read_text())["version"] == "0.1.5"
    assert '__version__ = "0.1.5"' in (
        tmp_path / "src/runner_mcp/__init__.py"
    ).read_text()
