from __future__ import annotations

from pathlib import Path

import yaml


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "self-hosted-qualification.yml"
)


def test_unadmitted_runner_qualification_is_never_automatically_queued() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert set(workflow["on"]) == {"workflow_dispatch"}
    job = workflow["jobs"]["qualify"]
    assert job["if"] == (
        "${{ github.event_name == 'workflow_dispatch' "
        "&& github.ref == 'refs/heads/main' }}"
    )
    assert job["runs-on"] == [
        "self-hosted",
        "Linux",
        "X64",
        "runner-mcp-validation",
    ]
    assert workflow["permissions"] == {"contents": "read"}


def test_qualification_does_not_reuse_runner_dependency_or_publisher_cache() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = yaml.load(text, Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["qualify"]["steps"]
    instructions = "\n".join(
        step.get("run", "")
        for step in steps
    )

    assert "RUNNER_TOOL_CACHE" not in text
    assert ".complete" not in text
    assert "no-cache-dir" in instructions
    assert "pip install" in instructions
    assert 'publisher_root="$RUNNER_TEMP/runner-mcp-publisher"' in instructions
    assert "sha256sum --check -" in instructions
    assert "mcp-publisher_linux_amd64.tar.gz" in instructions

    checkout = steps[0]
    assert checkout["with"]["persist-credentials"] == "false"
    assert checkout["with"]["ref"] == "${{ github.sha }}"
