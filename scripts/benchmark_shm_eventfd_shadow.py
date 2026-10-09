from __future__ import annotations

import argparse
import json
import math
import mmap
import multiprocessing as mp
import os
import select
import statistics
import struct
import time
from collections.abc import Callable
from typing import Any

_MAX_PAYLOAD_BYTES = 900_000
_HEADER = struct.Struct("!II")
_HEADER_SIZE = _HEADER.size
_SLOT_SIZE = _HEADER_SIZE + _MAX_PAYLOAD_BYTES
_MAPPING_SIZE = _SLOT_SIZE * 2


def _load_gate(max_load_per_cpu: float) -> dict[str, object]:
    cpu_count = max(1, os.cpu_count() or 1)
    one_minute_load, _, _ = os.getloadavg()
    load_per_cpu = one_minute_load / cpu_count
    if load_per_cpu > max_load_per_cpu:
        raise RuntimeError(
            "benchmark refused: host load exceeds the configured shadow-mode gate"
        )
    return {
        "logical_cpus": cpu_count,
        "one_minute_load": round(one_minute_load, 3),
        "load_per_cpu": round(load_per_cpu, 4),
        "max_load_per_cpu": max_load_per_cpu,
    }


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[rank]


def _measure(
    iterations: int,
    operation: Callable[[int], Any],
    *,
    pause_seconds: float,
) -> dict[str, object]:
    samples_ms: list[float] = []
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter()
    for sequence in range(iterations):
        before = time.perf_counter_ns()
        operation(sequence)
        after = time.perf_counter_ns()
        samples_ms.append((after - before) / 1_000_000)
        if pause_seconds:
            time.sleep(pause_seconds)
    wall_elapsed = time.perf_counter() - wall_start
    cpu_elapsed_ns = time.process_time_ns() - cpu_start
    return {
        "paced_elapsed_seconds": round(wall_elapsed, 6),
        "paced_calls_per_second": round(iterations / wall_elapsed, 2),
        "process_cpu_us_per_call": round(cpu_elapsed_ns / iterations / 1000, 3),
        "latency_ms": {
            "min": round(min(samples_ms), 4),
            "mean": round(statistics.fmean(samples_ms), 4),
            "p50": round(_percentile(samples_ms, 0.50), 4),
            "p95": round(_percentile(samples_ms, 0.95), 4),
            "p99": round(_percentile(samples_ms, 0.99), 4),
            "max": round(max(samples_ms), 4),
        },
    }


def _payload(sequence: int, payload_bytes: int) -> bytes:
    return json.dumps(
        {
            "schema": "faster13/event-control/v1",
            "sequence": sequence,
            "correlation": "benchmark-shadow",
            "payload": "x" * payload_bytes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_slot(
    mapping: mmap.mmap,
    offset: int,
    sequence: int,
    payload: bytes,
) -> None:
    if len(payload) > _MAX_PAYLOAD_BYTES:
        raise ValueError("benchmark payload exceeds maximum")
    mapping[offset : offset + _HEADER_SIZE] = _HEADER.pack(sequence, len(payload))
    start = offset + _HEADER_SIZE
    mapping[start : start + len(payload)] = payload


def _read_slot(mapping: mmap.mmap, offset: int) -> tuple[int, bytes]:
    sequence, length = _HEADER.unpack(mapping[offset : offset + _HEADER_SIZE])
    if length > _MAX_PAYLOAD_BYTES:
        raise RuntimeError("benchmark shared-memory payload exceeds maximum")
    start = offset + _HEADER_SIZE
    return sequence, bytes(mapping[start : start + length])


def _worker(
    memfd: int,
    request_eventfd: int,
    response_eventfd: int,
    iterations: int,
) -> None:
    mapping = mmap.mmap(memfd, _MAPPING_SIZE, access=mmap.ACCESS_WRITE)
    try:
        for _ in range(iterations):
            os.eventfd_read(request_eventfd)
            sequence, payload = _read_slot(mapping, 0)
            _write_slot(mapping, _SLOT_SIZE, sequence, payload)
            os.eventfd_write(response_eventfd, 1)
    finally:
        mapping.close()


def _benchmark_shared_memory(
    iterations: int,
    payload_bytes: int,
    pause_seconds: float,
) -> dict[str, object]:
    if not hasattr(os, "memfd_create") or not hasattr(os, "eventfd"):
        raise RuntimeError("benchmark requires Linux memfd/eventfd support")

    memfd = os.memfd_create("faster13-shadow", flags=os.MFD_CLOEXEC)
    request_eventfd = os.eventfd(0, os.EFD_CLOEXEC)
    response_eventfd = os.eventfd(0, os.EFD_CLOEXEC)
    try:
        os.ftruncate(memfd, _MAPPING_SIZE)
        mapping = mmap.mmap(memfd, _MAPPING_SIZE, access=mmap.ACCESS_WRITE)
        context = mp.get_context("fork")
        process = context.Process(
            target=_worker,
            args=(memfd, request_eventfd, response_eventfd, iterations),
            daemon=True,
        )
        process.start()

        def roundtrip(sequence: int) -> None:
            outgoing = _payload(sequence, payload_bytes)
            _write_slot(mapping, 0, sequence, outgoing)
            os.eventfd_write(request_eventfd, 1)
            ready, _, _ = select.select([response_eventfd], [], [], 5.0)
            if not ready:
                raise RuntimeError("benchmark shared-memory response timed out")
            os.eventfd_read(response_eventfd)
            returned_sequence, incoming = _read_slot(mapping, _SLOT_SIZE)
            if returned_sequence != sequence:
                raise RuntimeError("benchmark shared-memory sequence mismatch")
            if incoming != outgoing:
                raise RuntimeError("benchmark shared-memory payload mismatch")

        result = _measure(iterations, roundtrip, pause_seconds=pause_seconds)
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            raise RuntimeError("benchmark shared-memory worker did not stop")
        if process.exitcode != 0:
            raise RuntimeError("benchmark shared-memory worker failed")
        mapping.close()
        return result
    finally:
        if "process" in locals() and process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if "mapping" in locals():
            mapping.close()
        os.close(response_eventfd)
        os.close(request_eventfd)
        os.close(memfd)


def _run(
    iterations: int,
    payload_bytes: int,
    *,
    pause_seconds: float,
    max_load_per_cpu: float,
) -> dict[str, object]:
    gate = _load_gate(max_load_per_cpu)
    result = _benchmark_shared_memory(iterations, payload_bytes, pause_seconds)
    return {
        "schema_version": "faster13/shm-eventfd-shadow/v1",
        "iterations": iterations,
        "payload_bytes_requested": payload_bytes,
        "shadow_mode": {
            "real_work_units": False,
            "single_producer": True,
            "single_consumer": True,
            "pause_ms": round(pause_seconds * 1000, 3),
            "load_gate": gate,
        },
        "shared_memory_eventfd": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shadow benchmark for same-Linux-host shared memory plus eventfd. "
            "Uses only anonymous memfd/eventfd resources."
        )
    )
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--payload-bytes", type=int, default=256)
    parser.add_argument("--pause-ms", type=float, default=2.0)
    parser.add_argument("--max-load-per-cpu", type=float, default=0.75)
    args = parser.parse_args()

    if not 1 <= args.iterations <= 10_000:
        parser.error("--iterations must be between 1 and 10000")
    if not 0 <= args.payload_bytes <= _MAX_PAYLOAD_BYTES:
        parser.error("--payload-bytes is outside the supported range")
    if not 0 <= args.pause_ms <= 1000:
        parser.error("--pause-ms must be between 0 and 1000")
    if not 0.1 <= args.max_load_per_cpu <= 2.0:
        parser.error("--max-load-per-cpu must be between 0.1 and 2.0")

    print(
        json.dumps(
            _run(
                args.iterations,
                args.payload_bytes,
                pause_seconds=args.pause_ms / 1000,
                max_load_per_cpu=args.max_load_per_cpu,
            ),
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
