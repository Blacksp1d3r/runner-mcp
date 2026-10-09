"""Fail-closed CLI boundary checks for the shadow-only Faster-13 benchmark."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_local_mcp_transport.py"


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (["--iterations", "0"], "--iterations"),
        (["--warmup", "-1"], "--warmup"),
        (["--payload-bytes", "1000001"], "--payload-bytes"),
        (["--pause-ms", "-1"], "--pause-ms"),
        (["--max-load-per-cpu", "0"], "--max-load-per-cpu"),
        (["--iterations", "abc"], "invalid int value"),
    ],
)
def test_rejects_unsafe_arguments_before_any_benchmark_run(
    arguments: list[str],
    expected: str,
) -> None:
    completed = subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 2
    assert expected in completed.stderr
    assert completed.stdout == ""


def test_help_does_not_run_benchmark() -> None:
    completed = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0
    assert "No external endpoint is accepted" in completed.stdout
