from __future__ import annotations

import argparse
import json
import math
import statistics
import struct
import time
from collections.abc import Callable
from typing import Any

_BINARY_HEADER = struct.Struct("!BBHQ16sI")
_VERSION = 1
_MESSAGE_CLASS = 1
_FLAGS = 0x0001
_CORRELATION = bytes.fromhex("00112233445566778899aabbccddeeff")
_MAX_PAYLOAD_BYTES = 1_000_000


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[rank]


def _measure(
    iterations: int,
    operation: Callable[[], Any],
) -> dict[str, object]:
    samples_us: list[float] = []
    cpu_start = time.process_time_ns()
    for _ in range(iterations):
        before = time.perf_counter_ns()
        operation()
        after = time.perf_counter_ns()
        samples_us.append((after - before) / 1000)
    cpu_elapsed_ns = time.process_time_ns() - cpu_start
    return {
        "process_cpu_us_per_op": round(cpu_elapsed_ns / iterations / 1000, 4),
        "latency_us": {
            "min": round(min(samples_us), 4),
            "mean": round(statistics.fmean(samples_us), 4),
            "p50": round(_percentile(samples_us, 0.50), 4),
            "p95": round(_percentile(samples_us, 0.95), 4),
            "p99": round(_percentile(samples_us, 0.99), 4),
            "max": round(max(samples_us), 4),
        },
    }


def _json_encode(sequence: int, payload: str) -> bytes:
    return json.dumps(
        {
            "version": _VERSION,
            "class": _MESSAGE_CLASS,
            "flags": _FLAGS,
            "sequence": sequence,
            "correlation": _CORRELATION.hex(),
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _json_decode(raw: bytes) -> tuple[int, bytes]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("benchmark JSON envelope is invalid")
    if (
        value.get("version") != _VERSION
        or value.get("class") != _MESSAGE_CLASS
        or value.get("flags") != _FLAGS
        or value.get("correlation") != _CORRELATION.hex()
    ):
        raise ValueError("benchmark JSON envelope identity mismatch")
    sequence = value.get("sequence")
    payload = value.get("payload")
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("benchmark JSON sequence is invalid")
    if not isinstance(payload, str):
        raise TypeError("benchmark JSON payload is invalid")
    return sequence, payload.encode("ascii")


def _binary_encode(sequence: int, payload: bytes) -> bytes:
    if len(payload) > _MAX_PAYLOAD_BYTES:
        raise ValueError("benchmark binary payload exceeds maximum")
    return _BINARY_HEADER.pack(
        _VERSION,
        _MESSAGE_CLASS,
        _FLAGS,
        sequence,
        _CORRELATION,
        len(payload),
    ) + payload


def _binary_decode(raw: bytes) -> tuple[int, bytes]:
    if len(raw) < _BINARY_HEADER.size:
        raise ValueError("benchmark binary envelope is truncated")
    version, message_class, flags, sequence, correlation, payload_length = (
        _BINARY_HEADER.unpack_from(raw)
    )
    if (
        version != _VERSION
        or message_class != _MESSAGE_CLASS
        or flags != _FLAGS
        or correlation != _CORRELATION
    ):
        raise ValueError("benchmark binary envelope identity mismatch")
    if payload_length > _MAX_PAYLOAD_BYTES:
        raise ValueError("benchmark binary payload exceeds maximum")
    expected_length = _BINARY_HEADER.size + payload_length
    if len(raw) != expected_length:
        raise ValueError("benchmark binary envelope length mismatch")
    return sequence, raw[_BINARY_HEADER.size:]


def _relative(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, float]:
    base_latency = baseline["latency_us"]
    candidate_latency = candidate["latency_us"]
    if not isinstance(base_latency, dict) or not isinstance(candidate_latency, dict):
        raise TypeError("benchmark latency result is invalid")
    result: dict[str, float] = {}
    for key in ("mean", "p50", "p95", "p99"):
        base = float(base_latency[key])
        cand = float(candidate_latency[key])
        result[f"{key}_speedup_x"] = round(base / cand, 3)
        result[f"{key}_reduction_percent"] = round((1 - cand / base) * 100, 2)
    return result


def _run(iterations: int, payload_bytes: int) -> dict[str, object]:
    payload_text = "x" * payload_bytes
    payload_raw = payload_text.encode("ascii")
    sequence = 42

    json_sample = _json_encode(sequence, payload_text)
    binary_sample = _binary_encode(sequence, payload_raw)

    json_encode = _measure(
        iterations,
        lambda: _json_encode(sequence, payload_text),
    )
    json_decode = _measure(
        iterations,
        lambda: _json_decode(json_sample),
    )
    binary_encode = _measure(
        iterations,
        lambda: _binary_encode(sequence, payload_raw),
    )
    binary_decode = _measure(
        iterations,
        lambda: _binary_decode(binary_sample),
    )

    if _json_decode(json_sample) != (sequence, payload_raw):
        raise RuntimeError("benchmark JSON roundtrip failed")
    if _binary_decode(binary_sample) != (sequence, payload_raw):
        raise RuntimeError("benchmark binary roundtrip failed")

    return {
        "schema_version": "faster13/envelope-shadow/v1",
        "iterations": iterations,
        "payload_bytes_requested": payload_bytes,
        "encoded_bytes": {
            "json": len(json_sample),
            "binary": len(binary_sample),
            "binary_reduction_percent": round(
                (1 - len(binary_sample) / len(json_sample)) * 100,
                2,
            ),
        },
        "json": {
            "encode": json_encode,
            "decode": json_decode,
        },
        "binary": {
            "header_bytes": _BINARY_HEADER.size,
            "encode": binary_encode,
            "decode": binary_decode,
        },
        "comparisons": {
            "binary_encode_vs_json": _relative(json_encode, binary_encode),
            "binary_decode_vs_json": _relative(json_decode, binary_decode),
        },
        "shadow_mode": {
            "synthetic_only": True,
            "runtime_integration": False,
            "third_party_dependencies": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shadow benchmark comparing canonical compact JSON with a fixed "
            "binary EVENT/CONTROL envelope. No runtime integration is performed."
        )
    )
    parser.add_argument("--iterations", type=int, default=5_000)
    parser.add_argument("--payload-bytes", type=int, default=256)
    args = parser.parse_args()

    if not 1 <= args.iterations <= 100_000:
        parser.error("--iterations must be between 1 and 100000")
    if not 0 <= args.payload_bytes <= _MAX_PAYLOAD_BYTES:
        parser.error("--payload-bytes is outside the supported range")

    print(
        json.dumps(
            _run(args.iterations, args.payload_bytes),
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
