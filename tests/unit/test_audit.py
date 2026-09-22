from __future__ import annotations

import json
import stat
from datetime import datetime, timedelta

from runner_mcp.audit import AuditEvent, AuditLogger, utc_timestamp


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
