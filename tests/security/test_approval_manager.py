import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner_mcp import approval_manager as approval_module
from runner_mcp import secure_io as secure_io_module
from runner_mcp.approval_manager import ApprovalError, ApprovalManager


def manager(tmp_path: Path, *, ttl: int = 600) -> ApprovalManager:
    return ApprovalManager(root=tmp_path / "approvals", ttl_seconds=ttl)


def test_request_creates_private_single_use_plan(tmp_path: Path) -> None:
    approvals = manager(tmp_path)
    result = approvals.request(
        action="deploy",
        project="demo",
        binding={"commit": "a" * 40},
        summary={"commit": "a" * 40, "environment": "staging"},
    )
    approval_id = result["approval_id"]
    path = tmp_path / "approvals" / f"{approval_id}.json"

    assert result["state"] == "pending"
    assert result["single_use"] is True
    assert stat.S_IMODE((tmp_path / "approvals").stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert "binding_fingerprint" not in result


def test_approval_requires_local_transition_before_consume(tmp_path: Path) -> None:
    approvals = manager(tmp_path)
    requested = approvals.request(
        action="migration",
        project="demo",
        binding={"profile": "v1"},
        summary={"backup_required": True},
    )

    with pytest.raises(ApprovalError, match="not approved"):
        approvals.consume(
            requested["approval_id"],
            action="migration",
            project="demo",
            binding={"profile": "v1"},
        )

    approved = approvals.approve(requested["approval_id"])
    assert approved["state"] == "approved"
    consumed = approvals.consume(
        requested["approval_id"],
        action="migration",
        project="demo",
        binding={"profile": "v1"},
    )
    assert consumed["state"] == "consumed"


def test_consumed_approval_cannot_be_replayed(tmp_path: Path) -> None:
    approvals = manager(tmp_path)
    requested = approvals.request(
        action="code_rollback",
        project="demo",
        binding={"current": "new", "target": "old"},
        summary={"target": "old"},
    )
    approvals.approve(requested["approval_id"])
    approvals.consume(
        requested["approval_id"],
        action="code_rollback",
        project="demo",
        binding={"current": "new", "target": "old"},
    )

    with pytest.raises(ApprovalError, match="not approved"):
        approvals.consume(
            requested["approval_id"],
            action="code_rollback",
            project="demo",
            binding={"current": "new", "target": "old"},
        )


def test_approval_is_bound_to_action_project_and_plan(tmp_path: Path) -> None:
    approvals = manager(tmp_path)
    requested = approvals.request(
        action="deploy",
        project="demo",
        binding={"commit": "a" * 40},
        summary={"commit": "a" * 40},
    )
    approvals.approve(requested["approval_id"])

    with pytest.raises(ApprovalError, match="does not match"):
        approvals.consume(
            requested["approval_id"],
            action="deploy",
            project="other",
            binding={"commit": "a" * 40},
        )

    with pytest.raises(ApprovalError, match="plan changed"):
        approvals.consume(
            requested["approval_id"],
            action="deploy",
            project="demo",
            binding={"commit": "b" * 40},
        )


def test_expired_approval_cannot_be_approved_or_consumed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    monkeypatch.setattr(approval_module, "utc_now", lambda: now)
    approvals = manager(tmp_path, ttl=60)
    requested = approvals.request(
        action="deploy",
        project="demo",
        binding={"commit": "a" * 40},
        summary={},
    )
    monkeypatch.setattr(approval_module, "utc_now", lambda: now + timedelta(seconds=61))

    assert approvals.status(requested["approval_id"])["state"] == "expired"
    with pytest.raises(ApprovalError, match="expired"):
        approvals.approve(requested["approval_id"])


def test_approval_file_symlink_is_rejected(tmp_path: Path) -> None:
    approvals = manager(tmp_path)
    requested = approvals.request(
        action="deploy",
        project="demo",
        binding={"commit": "a" * 40},
        summary={},
    )
    path = tmp_path / "approvals" / f"{requested['approval_id']}.json"
    outside = tmp_path / "outside.json"
    outside.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    path.symlink_to(outside)

    with pytest.raises(ApprovalError, match="Unknown approval"):
        approvals.status(requested["approval_id"])


def test_approval_write_failure_is_bounded_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approvals = manager(tmp_path)
    sensitive = str(tmp_path / "private-approval-path")

    def fail_fsync(_fd: int) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, "fsync", fail_fsync)

    with pytest.raises(ApprovalError) as captured:
        approvals.request(
            action="deploy",
            project="demo",
            binding={"commit": "a" * 40},
            summary={},
        )

    assert str(captured.value) == "Approval file could not be written"
    assert sensitive not in str(captured.value)
    assert list(approvals.root.glob("*.json")) == []
    assert list(approvals.root.glob(".*.tmp")) == []
