from __future__ import annotations

import json
from pathlib import Path

import pytest

from runner_mcp.ci_runner_lifecycle import (
    CIRunnerLifecycleError,
    inspect_ci_runner,
    parse_ci_runner_specs,
    plan_ci_runner,
)


def raw(root: Path, work: Path) -> str:
    return json.dumps(
        [
            {
                "alias": "aifordable-lab-ci",
                "repository": "Blacksp1d3r/AIfordable",
                "runner_name": "aifordable-lab-ci",
                "runner_root": str(root),
                "work_root": str(work),
                "labels": ["aifordable-ci"],
            }
        ]
    )


def test_config_is_exact_bounded_and_private_path_aware(tmp_path: Path) -> None:
    root = tmp_path / "runner"
    work = root / "_work"
    specs = parse_ci_runner_specs(raw(root, work))

    assert tuple(specs) == ("aifordable-lab-ci",)
    spec = specs["aifordable-lab-ci"]
    assert spec.repository == "Blacksp1d3r/AIfordable"
    assert spec.runner_name == "aifordable-lab-ci"
    assert spec.labels == ("aifordable-ci",)


def test_status_reports_bounded_state_without_paths(tmp_path: Path) -> None:
    root = tmp_path / "runner"
    work = root / "_work"
    root.mkdir()
    work.mkdir()
    (root / ".runner").write_text("private registration data", encoding="utf-8")

    spec = parse_ci_runner_specs(raw(root, work))["aifordable-lab-ci"]
    payload = inspect_ci_runner(spec).to_payload()

    assert payload == {
        "alias": "aifordable-lab-ci",
        "configured": True,
        "registered": True,
        "runner_root_ready": True,
        "work_root_ready": True,
    }
    rendered = repr(payload)
    assert str(tmp_path) not in rendered
    assert "private registration data" not in rendered


def test_plan_is_read_only_and_activation_reserved(tmp_path: Path) -> None:
    root = tmp_path / "runner"
    work = root / "_work"
    root.mkdir()
    work.mkdir()

    spec = parse_ci_runner_specs(raw(root, work))["aifordable-lab-ci"]
    payload = plan_ci_runner(spec).to_payload()

    assert payload == {
        "alias": "aifordable-lab-ci",
        "repository": "Blacksp1d3r/AIfordable",
        "runner_name": "aifordable-lab-ci",
        "labels": ["aifordable-ci"],
        "enrollment_required": True,
        "activation_supported": False,
    }


@pytest.mark.parametrize(
    "mutation",
    [
        {"runner_root": "relative/runner"},
        {"work_root": "relative/work"},
        {"repository": "not-a-repository"},
        {"alias": "../escape"},
        {"runner_name": "bad name"},
        {"labels": ["self-hosted", "aifordable-ci"]},
        {"labels": ["Linux", "aifordable-ci"]},
        {"labels": ["X64", "aifordable-ci"]},
        {"labels": ["aifordable-ci", "aifordable-ci"]},
    ],
)
def test_invalid_or_ambiguous_config_fails_closed(
    tmp_path: Path,
    mutation: dict[str, object],
) -> None:
    root = tmp_path / "runner"
    work = root / "_work"
    item: dict[str, object] = {
        "alias": "aifordable-lab-ci",
        "repository": "Blacksp1d3r/AIfordable",
        "runner_name": "aifordable-lab-ci",
        "runner_root": str(root),
        "work_root": str(work),
        "labels": ["Linux", "X64", "aifordable-ci"],
    }
    item.update(mutation)

    with pytest.raises(CIRunnerLifecycleError):
        parse_ci_runner_specs(json.dumps([item]))


def test_symlink_runner_root_is_never_ready(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "_work").mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    work = link / "_work"

    spec = parse_ci_runner_specs(raw(link, work))["aifordable-lab-ci"]
    status = inspect_ci_runner(spec)

    assert status.runner_root_ready is False
    assert status.registered is False



def test_work_root_must_be_inside_runner_root(tmp_path: Path) -> None:
    root = tmp_path / "runner"
    outside = tmp_path / "outside"

    with pytest.raises(CIRunnerLifecycleError, match="inside runner root"):
        parse_ci_runner_specs(raw(root, outside))
