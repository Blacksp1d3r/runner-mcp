"""Deterministic, fully local synthetic baseline for MCP message overhead.

No sockets, credentials, external systems, workers or provider APIs. This
measures JSON framing on the test host; it does NOT measure real MCP RTT,
end-to-end latency, network capacity, CPU/message or actual push delivery.
"""
from __future__ import annotations

import json
import math
import statistics
import time
from collections.abc import Callable
from typing import Any

_CLASSES = {"tiny": 128, "medium": 4096, "large": 65536}


def percentile_ns(samples: list[int], percentile: float) -> int:
    """Nearest-rank percentile with explicit nonempty finite nonnegative data."""
    if (
        not samples
        or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in samples)
        or not isinstance(percentile, (int, float))
        or isinstance(percentile, bool)
        or not math.isfinite(percentile)
        or not 0 < percentile <= 100
    ):
        raise ValueError("invalid benchmark samples or percentile")
    ordered = sorted(samples)
    return ordered[math.ceil((percentile / 100) * len(ordered)) - 1]


def synthetic_poll_detection_delay_ms(
    completion_offset_ms: int, *, polling_interval_ms: int = 500
) -> int:
    """Worst-phase deterministic poll detection delay, with initial poll at t=0."""
    if (
        isinstance(completion_offset_ms, bool)
        or not isinstance(completion_offset_ms, int)
        or completion_offset_ms < 0
        or isinstance(polling_interval_ms, bool)
        or not isinstance(polling_interval_ms, int)
        or not 1 <= polling_interval_ms <= 60000
    ):
        raise ValueError("invalid synthetic poll parameters")
    return (-completion_offset_ms) % polling_interval_ms


def summarize(samples_ns: list[int], elapsed_ns: int, *, bytes_per_call: int) -> dict[str, Any]:
    if not samples_ns or not isinstance(elapsed_ns, int) or elapsed_ns <= 0:
        raise ValueError("benchmark requires elapsed wall duration")
    if not isinstance(bytes_per_call, int) or bytes_per_call < 0:
        raise ValueError("invalid byte count")
    return {
        "samples": len(samples_ns),
        "p50_ns": percentile_ns(samples_ns, 50),
        "p95_ns": percentile_ns(samples_ns, 95),
        "p99_ns": percentile_ns(samples_ns, 99),
        "mean_ns": round(statistics.mean(samples_ns)),
        "calls_per_second": round(len(samples_ns) * 1_000_000_000 / elapsed_ns, 2),
        "bytes_per_call": bytes_per_call,
    }


def _time_operation(operation: Callable[[], object], repetitions: int) -> tuple[list[int], int]:
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 1 <= repetitions <= 10000:
        raise ValueError("repetitions must be between 1 and 10000")
    durations: list[int] = []
    start = time.perf_counter_ns()
    for _ in range(repetitions):
        t0 = time.perf_counter_ns()
        operation()
        durations.append(time.perf_counter_ns() - t0)
    return durations, max(1, time.perf_counter_ns() - start)


def benchmark_synthetic_framing(*, repetitions: int = 200) -> dict[str, Any]:
    """Measure only local serialization/deserialization, no MCP transport."""
    results: dict[str, Any] = {}
    for name, payload_bytes in _CLASSES.items():
        envelope = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "synthetic_read_only",
                "arguments": {"payload": "x" * payload_bytes, "trace_id": "0" * 32},
            },
        }
        encoded = json.dumps(
            envelope, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        encode_ns, encode_elapsed = _time_operation(
            lambda envelope=envelope: json.dumps(
                envelope, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode("utf-8"),
            repetitions,
        )
        decode_ns, decode_elapsed = _time_operation(
            lambda encoded=encoded: json.loads(encoded.decode("utf-8")), repetitions
        )
        results[name] = {
            "json_encode": summarize(encode_ns, encode_elapsed, bytes_per_call=len(encoded)),
            "json_decode": summarize(decode_ns, decode_elapsed, bytes_per_call=len(encoded)),
        }
    return {
        "schema_version": "runner-mcp/synthetic-fastpath-benchmark/v1",
        "measurement_scope": "local_json_only_not_mcp_rtt",
        "repetitions": repetitions,
        "payload_classes_bytes": dict(_CLASSES),
        "results": results,
        "polling_interval_ms": 500,
        "synthetic_polling_delay_ms": {
            "job_1_ms": synthetic_poll_detection_delay_ms(1),
            "job_100_ms": synthetic_poll_detection_delay_ms(100),
            "job_499_ms": synthetic_poll_detection_delay_ms(499),
            "job_500_ms": synthetic_poll_detection_delay_ms(500),
        },
    }
