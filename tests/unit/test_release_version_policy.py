"""Every shipping code/tool change must carry its own monotonically increasing version."""

import importlib.util
import json
from pathlib import Path

import pytest

_GATE_FILE = Path(__file__).resolve().parents[2] / "scripts/check_release_version.py"
_SPEC = importlib.util.spec_from_file_location("runner_mcp_release_gate", _GATE_FILE)
assert _SPEC is not None and _SPEC.loader is not None
_GATE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GATE)
check_metadata = _GATE.check_metadata
needs_bump = _GATE.needs_bump
version_tuple = _GATE.version_tuple
append_github_output = _GATE.append_github_output
verify = _GATE.verify


@pytest.mark.parametrize("path", [
    "src/runner_mcp/cli.py", "src/runner_mcp/new_tool.py",
    "scripts/release-check.sh", "install.sh", "install-operator.sh",
    ".github/workflows/validation.yml", ".github/actions/local/action.yml",
    "pyproject.toml", "server.json",
])
def test_shipping_paths_require_version(path):
    assert needs_bump([path])


def test_handover_and_test_only_do_not_require_new_binary_version():
    assert not needs_bump([
        "docs/README.md", "roadmap/children/TASK.md",
        "handover/AGENT_EXCHANGE.md", "tests/unit/test_x.py",
    ])


@pytest.mark.parametrize("v", ["0.1.3+abc", "v0.1.4", "0.1", "0.1.3.dev2", ""])
def test_non_numeric_version_rejected(v):
    with pytest.raises(ValueError):
        version_tuple(v)


def test_ordered_versions_and_no_reuse():
    assert version_tuple("0.1.4") > version_tuple("0.1.3")
    assert not version_tuple("0.1.3") > version_tuple("0.1.3")


def test_package_metadata_must_match():
    pyproject = b'[project]\nversion="0.1.4"\n'
    good = {"version": "0.1.4", "packages": [{"version": "0.1.4"}]}
    assert check_metadata(pyproject, json.dumps(good).encode()) == (0, 1, 4)
    good["packages"][0]["version"] = "0.1.3"
    with pytest.raises(ValueError, match="package version differs"):
        check_metadata(pyproject, json.dumps(good).encode())


def test_metadata_must_match_runtime_and_discovery(tmp_path, monkeypatch):
    (tmp_path / "src/runner_mcp").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="0.1.4"\n')
    (tmp_path / "server.json").write_text(
        json.dumps({"version": "0.1.4", "packages": [{"version": "0.1.4"}]})
    )
    (tmp_path / "src/runner_mcp/__init__.py").write_text('__version__ = "0.1.4"\n')
    (tmp_path / "glama.json").write_text(json.dumps({"version": "0.1.4"}))
    monkeypatch.chdir(tmp_path)
    assert verify(None) == ((0, 1, 4), False)
    (tmp_path / "glama.json").write_text(json.dumps({"version": "0.1.3"}))
    with pytest.raises(ValueError, match="discovery metadata"):
        verify(None)


def test_new_tool_same_version_fails_against_main(tmp_path, monkeypatch):
    (tmp_path / "src/runner_mcp").mkdir(parents=True)
    old_py = b'[project]\nversion="0.1.4"\n'
    old_server = json.dumps(
        {"version": "0.1.4", "packages": [{"version": "0.1.4"}]}
    ).encode()
    (tmp_path / "pyproject.toml").write_bytes(old_py)
    (tmp_path / "server.json").write_bytes(old_server)
    (tmp_path / "src/runner_mcp/__init__.py").write_text('__version__ = "0.1.4"\n')
    (tmp_path / "glama.json").write_text(json.dumps({"version": "0.1.4"}))
    monkeypatch.chdir(tmp_path)

    def fake_git(*args):
        if args[0] == "show":
            return old_py if args[1].endswith(":pyproject.toml") else old_server
        if args[0] == "diff":
            return b"src/runner_mcp/new_tool.py\0"
        raise AssertionError("unexpected git arguments")

    monkeypatch.setattr(_GATE, "git", fake_git)
    with pytest.raises(ValueError, match="without a new version"):
        verify("a" * 40)


def test_candidate_output_uses_single_source_classification(tmp_path, monkeypatch):
    result = tmp_path / "github-output"
    result.write_text("")
    monkeypatch.setenv("GITHUB_OUTPUT", str(result))
    append_github_output((0, 1, 4), True)
    assert result.read_text().splitlines() == ["release=true", "version=0.1.4"]


def test_documentation_only_candidate_output(tmp_path, monkeypatch):
    result = tmp_path / "github-output"
    result.write_text("")
    monkeypatch.setenv("GITHUB_OUTPUT", str(result))
    append_github_output((0, 1, 4), False)
    assert result.read_text().splitlines() == ["release=false", "version=0.1.4"]


def test_candidate_output_without_gha_context_fails_closed(monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    with pytest.raises(ValueError, match="GITHUB_OUTPUT"):
        append_github_output((0, 1, 4), True)
