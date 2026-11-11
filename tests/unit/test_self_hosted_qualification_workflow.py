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
    events = text.split("on:\n", 1)[1].split("\npermissions:", 1)[0]

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

def test_main_release_workflows_never_cancel_previous_source_commit() -> None:
    """Bewaar een main-releasevalidatie bij een latere documentatiecommit.

    PR-branches mogen hun verouderde testgeneratie wel annuleren. De twee
    bestaande CI-workflows op de beschermde hoofdbranch mogen hun eerdere
    sourceversiecontrole niet als CANCELLED markeren door een opvolgende push.
    Dit is een statische regressietest, zonder nieuwe workflow of job.
    """
    base = Path(__file__).resolve().parents[2] / ".github" / "workflows"
    for name in ("validation.yml", "commit-attribution-policy.yml"):
        text = (base / name).read_text(encoding="utf-8")
        assert text.count("\nconcurrency:\n") == 1
        concurrency = text.split("\nconcurrency:\n", 1)[1].split("\njobs:", 1)[0]
        assert "  group:" in concurrency
        assert "github.ref" in concurrency
        assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in concurrency
        assert "cancel-in-progress: true" not in concurrency

def test_release_candidate_depends_on_demo_and_isolated_systemd() -> None:
    """Artifact kan niet voor de echte demo en disposable hersteltest verschijnen.

    De al bestaande main-validatiebron blijft leidend: geen tweede workflow,
    geen eigen publisher en geen gegenereerde artifact- of hosttoestemming.
    """
    root = Path(__file__).resolve().parents[2]
    text = (root / ".github" / "workflows" / "validation.yml").read_text(
        encoding="utf-8"
    )
    assert "\n  demo-smoke:\n" in text
    assert "\n  disposable-systemd-user:\n" in text
    assert "\n  release-artifact:\n" in text
    declaration = text.split("\n  release-artifact:\n", 1)[1].split("\n    steps:", 1)[0]
    assert "needs: [validate, demo-smoke, disposable-systemd-user]" in declaration
    assert "    needs: validate\n" not in declaration
