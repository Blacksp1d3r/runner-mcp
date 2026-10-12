"""The release baseline and wheel must agree without executing arbitrary tools."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

_FILE = Path(__file__).resolve().parents[2] / "scripts/attest_tool_catalogue.py"
_SPEC = importlib.util.spec_from_file_location("runner_mcp_tool_attestation", _FILE)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def _source(name="example"):
    return f"def register(mcp):\n    @mcp.tool()\n    def {name}():\n        return 'ok'\n".encode()


def _manifest(*names):
    return {
        "schemaVersion": "runner-mcp/tool-catalogue-baseline/v1",
        "sourceFile": "src/runner_mcp/server.py",
        "minimumToolCount": 70,
        "tools": sorted(names),
    }


def test_registered_tools_parsed_without_executing_code():
    assert _MOD.registered_tool_names(_source()) == ["example"]


def test_duplicate_registration_rejected():
    content = _source() + _source()
    with pytest.raises(_MOD.CatalogueError, match="duplicate"):
        _MOD.registered_tool_names(content)


def test_decorators_with_dynamic_args_require_review():
    content = b"def register(mcp):\n    @mcp.tool(name=compute())\n    def example():\n        pass\n"
    with pytest.raises(_MOD.CatalogueError, match="nonliteral"):
        _MOD.registered_tool_names(content)


def test_manifest_drift_detected():
    with pytest.raises(_MOD.CatalogueError, match="diverges"):
        _MOD.verify_baseline(["example"], _manifest("unexpected"))


def test_missing_wheel_server_member_rejected(tmp_path):
    path = tmp_path / "wheel.whl"
    with zipfile.ZipFile(path, "w") as wheel:
        wheel.writestr("runner_mcp/cli.py", b"# test\n")
    baseline = json.loads(_MOD.BASELINE.read_text(encoding="utf-8"))
    with pytest.raises(_MOD.CatalogueError, match="missing"):
        _MOD.tool_receipt(
            source=_MOD.SOURCE.read_bytes(), manifest=baseline, wheel_file=path
        )


def test_source_baseline_matches_approved_70_tools():
    baseline = json.loads(_MOD.BASELINE.read_text(encoding="utf-8"))
    source = _MOD.SOURCE.read_bytes()
    names = _MOD.registered_tool_names(source)
    assert len(names) == 70
    _MOD.verify_baseline(names, baseline)
    receipt = _MOD.tool_receipt(source=source, manifest=baseline, wheel_file=None)
    assert receipt["toolCount"] == 70
    assert receipt["clientToolExposureVerified"] is False
    assert receipt["liveServerUpdated"] is False
