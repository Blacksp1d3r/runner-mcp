"""Every shipping code/tool change must carry its own monotonically increasing version."""

import json

import pytest

from scripts.check_release_version import check_metadata, needs_bump, version_tuple


@pytest.mark.parametrize("path", [
    "src/runner_mcp/cli.py", "src/runner_mcp/new_tool.py",
    "scripts/release-check.sh", "install.sh",
    ".github/workflows/validation.yml", "pyproject.toml", "server.json",
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
