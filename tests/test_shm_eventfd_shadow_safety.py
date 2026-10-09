"""Bounded failure and ordinary completion for the shadow eventfd benchmark."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_shm_eventfd_shadow.py"
_LINUX_EVENTFD = sys.platform == "linux" and hasattr(os, "memfd_create") and hasattr(os, "eventfd")


@pytest.mark.skipif(not _LINUX_EVENTFD, reason="Linux-only synthetic transport")
def test_shadow_worker_completes_single_synthetic_roundtrip() -> None:
    benchmark = runpy.run_path(str(_SCRIPT))
    result = benchmark["_benchmark_shared_memory"](1, 32, 0)
    assert result["latency_ms"]["p50"] >= 0


@pytest.mark.skipif(not _LINUX_EVENTFD, reason="Linux-only synthetic transport")
def test_shadow_worker_timeout_fails_closed_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark = runpy.run_path(str(_SCRIPT))
    monkeypatch.setattr(
        benchmark["select"],
        "select",
        lambda *_args, **_kwargs: ([], [], []),
    )
    with pytest.raises(RuntimeError, match="response timed out"):
        benchmark["_benchmark_shared_memory"](1, 32, 0)
