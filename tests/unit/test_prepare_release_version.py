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
    def git_valid(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "b" * 40
        if "merge-base" in args:
            return "b" * 40
        if "show" in args:
            return '[project]\nversion = "0.1.3"'
        return ""
    monkeypatch.setattr(_MOD, "_git", git_valid)
    monkeypatch.setattr(sys, "argv", [
        "prepare_release_version.py", "--kind", "patch", "--expected-version",
        "0.1.4", "--expected-head", "a" * 40,
        "--expected-main", "b" * 40, "--apply",
    ])
    assert _MOD.main() == 0
    assert 'version = "0.1.5"' in (tmp_path / "pyproject.toml").read_text()
    assert json.loads((tmp_path / "server.json").read_text())["version"] == "0.1.5"
    assert json.loads((tmp_path / "glama.json").read_text())["version"] == "0.1.5"
    assert '__version__ = "0.1.5"' in (
        tmp_path / "src/runner_mcp/__init__.py"
    ).read_text()


def test_stale_main_ref_refuses_version_allocation(tmp_path, monkeypatch):
    _fixture(tmp_path)

    def git_stale(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "c" * 40
        return ""

    monkeypatch.setattr(_MOD, "_git", git_stale)
    with pytest.raises(_MOD.VersionAllocationError, match="tracked main ref changed"):
        _MOD.plan(
            root=tmp_path, kind="patch", expected_version="0.1.4",
            expected_head="a" * 40, expected_main="b" * 40
        )
    assert 'version = "0.1.4"' in (tmp_path / "pyproject.toml").read_text()


def test_main_higher_than_next_version_refuses(tmp_path, monkeypatch):
    _fixture(tmp_path)

    def git_future(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "b" * 40
        if "merge-base" in args:
            return "b" * 40
        if "show" in args:
            return '[project]\nversion = "0.1.5"'
        return ""

    monkeypatch.setattr(_MOD, "_git", git_future)
    with pytest.raises(_MOD.VersionAllocationError, match="does not exceed"):
        _MOD.plan(
            root=tmp_path, kind="patch", expected_version="0.1.4",
            expected_head="a" * 40, expected_main="b" * 40
        )


def test_main_lower_than_next_version_is_allowed(tmp_path, monkeypatch):
    _fixture(tmp_path)

    def git_expected(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "b" * 40
        if "merge-base" in args:
            return "b" * 40
        if "show" in args:
            return '[project]\nversion = "0.1.4"'
        return ""

    monkeypatch.setattr(_MOD, "_git", git_expected)
    assert _MOD.plan(
        root=tmp_path, kind="patch", expected_version="0.1.4",
        expected_head="a" * 40, expected_main="b" * 40
    )[0] == "0.1.5"


def test_apply_without_expected_main_does_not_write(tmp_path, monkeypatch):
    import sys

    _fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        _MOD, "_git", lambda *args: "a" * 40 if "rev-parse" in args else ""
    )
    monkeypatch.setattr(sys, "argv", [
        "prepare_release_version.py", "--kind", "patch",
        "--expected-version", "0.1.4", "--expected-head", "a" * 40,
        "--apply",
    ])
    assert _MOD.main() == 1
    assert 'version = "0.1.4"' in (tmp_path / "pyproject.toml").read_text()


def test_unrelated_main_ref_is_refused(tmp_path, monkeypatch):
    _fixture(tmp_path)

    def git_unrelated(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "b" * 40
        if "merge-base" in args:
            return "c" * 40
        return ""

    monkeypatch.setattr(_MOD, "_git", git_unrelated)
    with pytest.raises(_MOD.VersionAllocationError, match="not an ancestor"):
        _MOD.plan(
            root=tmp_path, kind="patch", expected_version="0.1.4",
            expected_head="a" * 40, expected_main="b" * 40,
        )


def test_write_failure_rolls_back_earlier_metadata(tmp_path, monkeypatch):
    import sys

    _fixture(tmp_path)
    before = {
        name: (tmp_path / name).read_bytes()
        for name in ("pyproject.toml", "server.json", "glama.json", "src/runner_mcp/__init__.py")
    }
    monkeypatch.chdir(tmp_path)

    def git_valid(*args):
        if "rev-parse" in args:
            return "a" * 40 if "HEAD" in args else "b" * 40
        if "merge-base" in args:
            return "b" * 40
        if "show" in args:
            return '[project]\nversion = "0.1.3"'
        return ""

    monkeypatch.setattr(_MOD, "_git", git_valid)
    real_write = Path.write_bytes
    fail_once = {"pending": True}

    def write_injected(self, data):
        if self.name == "server.json" and fail_once["pending"]:
            fail_once["pending"] = False
            raise OSError("synthetic write failure")
        return real_write(self, data)

    monkeypatch.setattr(Path, "write_bytes", write_injected)
    monkeypatch.setattr(sys, "argv", [
        "prepare_release_version.py", "--kind", "patch", "--expected-version",
        "0.1.4", "--expected-head", "a" * 40,
        "--expected-main", "b" * 40, "--apply",
    ])
    assert _MOD.main() == 1
    assert all((tmp_path / name).read_bytes() == original for name, original in before.items())
