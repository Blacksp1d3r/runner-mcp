from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "self-hosted-qualification.yml"
)


def test_unadmitted_runner_qualification_is_never_automatically_queued() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    events = text.split("on:\\n", 1)[1].split("\\npermissions:", 1)[0]

    assert "workflow_dispatch:" in events
    assert "  push:" not in events
    assert "  pull_request:" not in events
    assert "github.event_name == 'workflow_dispatch'" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "      - runner-mcp-validation" in text
    assert "  contents: read" in text


def test_qualification_does_not_reuse_runner_dependency_or_publisher_cache() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "RUNNER_TOOL_CACHE" not in text
    assert ".complete" not in text
    assert "--no-cache-dir" in text
    assert "pip install" in text
    assert 'publisher_root="$RUNNER_TEMP/runner-mcp-publisher"' in text
    assert "sha256sum --check -" in text
    assert "mcp-publisher_linux_amd64.tar.gz" in text
    assert "persist-credentials: false" in text
    assert "ref: ${{ github.sha }}" in text
