from __future__ import annotations

import json
import multiprocessing
import os
import stat

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from runner_mcp.audit import AuditEvent, AuditLogger, utc_timestamp


def _append_many(path: str, prefix: str, count: int) -> None:
    logger = AuditLogger(Path(path))
    for index in range(count):
        logger.append(_event(f"{prefix}-{index}", "ok"))


def _event(request_id: str, result: str) -> AuditEvent:
    return AuditEvent(
        request_id=request_id,
        tool="project_status",
        project="example",
        actor="operator",
        result=result,
        timestamp="2026-09-22T00:00:00+00:00",
    )


def test_audit_logger_appends_json_lines_with_private_permissions(tmp_path) -> None:
    path = tmp_path / "nested" / "audit.jsonl"
    logger = AuditLogger(path)

    logger.append(_event("req-1", "ok"))
    logger.append(_event("req-2", "failed"))

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["request_id"] for row in rows] == ["req-1", "req-2"]
    assert [row["result"] for row in rows] == ["ok", "failed"]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_audit_logger_tightens_existing_file_permissions(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    path.write_text("", encoding="utf-8")
    path.chmod(0o644)

    AuditLogger(path).append(_event("req-1", "ok"))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_utc_timestamp_is_timezone_aware_utc() -> None:
    parsed = datetime.fromisoformat(utc_timestamp())

    assert parsed.utcoffset() == timedelta(0)


def test_audit_logger_refuses_symlink_without_touching_referent(tmp_path) -> None:
    target = tmp_path / "sentinel.txt"
    target.write_text("sentinel", encoding="utf-8")
    target.chmod(0o644)
    link = tmp_path / "audit.jsonl"
    link.symlink_to(target)

    with pytest.raises(OSError):
        AuditLogger(link).append(_event("req-link", "ok"))

    assert target.read_text(encoding="utf-8") == "sentinel"
    assert stat.S_IMODE(target.stat().st_mode) == 0o644


def test_audit_logger_fsyncs_before_success(tmp_path, monkeypatch) -> None:
    path = tmp_path / "audit.jsonl"
    seen: list[int] = []
    real_fsync = os.fsync

    def recording_fsync(fd: int) -> None:
        seen.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", recording_fsync)
    AuditLogger(path).append(_event("req-fsync", "ok"))

    assert len(seen) == 1


def test_audit_logger_propagates_fsync_failure(tmp_path, monkeypatch) -> None:
    path = tmp_path / "audit.jsonl"

    def failing_fsync(_fd: int) -> None:
        raise OSError("simulated durability failure")

    monkeypatch.setattr(os, "fsync", failing_fsync)

    with pytest.raises(OSError, match="simulated durability failure"):
        AuditLogger(path).append(_event("req-fsync-fail", "failed"))


def test_audit_logger_retries_short_writes(tmp_path, monkeypatch) -> None:
    path = tmp_path / "audit.jsonl"
    real_write = os.write
    calls = 0

    def short_write(fd: int, data) -> int:
        nonlocal calls
        calls += 1
        view = memoryview(data)
        if len(view) > 1:
            return real_write(fd, view[: max(1, len(view) // 2)])
        return real_write(fd, view)

    monkeypatch.setattr(os, "write", short_write)
    AuditLogger(path).append(_event("req-short", "ok"))

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["request_id"] for row in rows] == ["req-short"]
    assert calls > 1


def test_audit_logger_serializes_cross_process_records(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    processes = [
        multiprocessing.Process(target=_append_many, args=(str(path), prefix, 20))
        for prefix in ("left", "right")
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=15)
        assert process.exitcode == 0

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [row["request_id"] for row in rows]
    assert len(ids) == 40
    assert len(set(ids)) == 40
    assert set(ids) == {
        f"{prefix}-{index}"
        for prefix in ("left", "right")
        for index in range(20)
    }
