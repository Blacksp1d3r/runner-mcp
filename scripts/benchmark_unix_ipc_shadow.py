from __future__ import annotations

import argparse
import json
import math
import os
import socket
import statistics
import struct
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

_MAX_FRAME_BYTES = 1_048_576
_HEADER = struct.Struct("!I")
_STOP = b'{"control":"stop"}'


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


def _recv_exact(sock: socket.socket, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("benchmark peer closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _send_stream_frame(sock: socket.socket, payload: bytes) -> None:
    if len(payload) > _MAX_FRAME_BYTES:
        raise ValueError("benchmark frame exceeds maximum")
    sock.sendall(_HEADER.pack(len(payload)) + payload)


def _recv_stream_frame(sock: socket.socket) -> bytes:
    header = _recv_exact(sock, _HEADER.size)
    (length,) = _HEADER.unpack(header)
    if length > _MAX_FRAME_BYTES:
        raise RuntimeError("benchmark frame exceeds maximum")
    return _recv_exact(sock, length)


def _stream_server(path: Path, ready: threading.Event) -> None:
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(path))
        server.listen(1)
        ready.set()
        connection, _ = server.accept()
        with connection:
            while True:
                payload = _recv_stream_frame(connection)
                if payload == _STOP:
                    return
                _send_stream_frame(connection, payload)
    finally:
        server.close()


def _seqpacket_server(path: Path, ready: threading.Event) -> None:
    server = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        server.bind(str(path))
        server.listen(1)
        ready.set()
        connection, _ = server.accept()
        with connection:
            while True:
                payload = connection.recv(_MAX_FRAME_BYTES + 1)
                if not payload:
                    return
                if len(payload) > _MAX_FRAME_BYTES:
                    raise RuntimeError("benchmark packet exceeds maximum")
                if payload == _STOP:
                    return
                connection.sendall(payload)
    finally:
        server.close()


def _benchmark_stream(
    iterations: int,
    payload_bytes: int,
    pause_seconds: float,
    socket_path: Path,
) -> dict[str, object]:
    ready = threading.Event()
    thread = threading.Thread(
        target=_stream_server,
        args=(socket_path, ready),
        daemon=True,
    )
    thread.start()
    if not ready.wait(timeout=5):
        raise RuntimeError("benchmark stream server did not start")

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(str(socket_path))

        def roundtrip(sequence: int) -> None:
            outgoing = _payload(sequence, payload_bytes)
            _send_stream_frame(client, outgoing)
            incoming = _recv_stream_frame(client)
            if incoming != outgoing:
                raise RuntimeError("benchmark stream payload mismatch")

        result = _measure(iterations, roundtrip, pause_seconds=pause_seconds)
        _send_stream_frame(client, _STOP)
    finally:
        client.close()
        thread.join(timeout=5)
    if thread.is_alive():
        raise RuntimeError("benchmark stream server did not stop")
    return result


def _benchmark_seqpacket(
    iterations: int,
    payload_bytes: int,
    pause_seconds: float,
    socket_path: Path,
) -> dict[str, object] | None:
    if not hasattr(socket, "SOCK_SEQPACKET"):
        return None
    ready = threading.Event()
    thread = threading.Thread(
        target=_seqpacket_server,
        args=(socket_path, ready),
        daemon=True,
    )
    thread.start()
    if not ready.wait(timeout=5):
        raise RuntimeError("benchmark seqpacket server did not start")

    client = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        client.connect(str(socket_path))

        def roundtrip(sequence: int) -> None:
            outgoing = _payload(sequence, payload_bytes)
            if len(outgoing) > _MAX_FRAME_BYTES:
                raise ValueError("benchmark packet exceeds maximum")
            client.sendall(outgoing)
            incoming = client.recv(_MAX_FRAME_BYTES + 1)
            if incoming != outgoing:
                raise RuntimeError("benchmark seqpacket payload mismatch")

        result = _measure(iterations, roundtrip, pause_seconds=pause_seconds)
        client.sendall(_STOP)
    finally:
        client.close()
        thread.join(timeout=5)
    if thread.is_alive():
        raise RuntimeError("benchmark seqpacket server did not stop")
    return result


def _run(
    iterations: int,
    payload_bytes: int,
    *,
    pause_seconds: float,
    max_load_per_cpu: float,
) -> dict[str, object]:
    gate = _load_gate(max_load_per_cpu)
    json_baseline = _measure(
        iterations,
        lambda sequence: json.loads(_payload(sequence, payload_bytes)),
        pause_seconds=pause_seconds,
    )

    with tempfile.TemporaryDirectory(prefix="faster13-ipc-") as directory:
        root = Path(directory)
        stream = _benchmark_stream(
            iterations,
            payload_bytes,
            pause_seconds,
            root / "stream.sock",
        )
        seqpacket = _benchmark_seqpacket(
            iterations,
            payload_bytes,
            pause_seconds,
            root / "seqpacket.sock",
        )

    return {
        "schema_version": "faster13/unix-ipc-shadow/v1",
        "shadow_mode": {
            "single_client": True,
            "single_server_thread": True,
            "pause_ms": round(pause_seconds * 1000, 3),
            "load_gate": gate,
            "real_work_units": False,
        },
        "iterations": iterations,
        "payload_bytes_requested": payload_bytes,
        "baselines": {
            "json_roundtrip": json_baseline,
            "unix_stream": stream,
            "unix_seqpacket": seqpacket,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shadow benchmark for same-Linux-host Unix IPC. "
            "Uses only internally-created private temporary sockets."
        )
    )
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--payload-bytes", type=int, default=256)
    parser.add_argument("--pause-ms", type=float, default=2.0)
    parser.add_argument("--max-load-per-cpu", type=float, default=0.75)
    args = parser.parse_args()

    if not 1 <= args.iterations <= 10_000:
        parser.error("--iterations must be between 1 and 10000")
    if not 0 <= args.payload_bytes <= 900_000:
        parser.error("--payload-bytes must be between 0 and 900000")
    if not 0 <= args.pause_ms <= 1000:
        parser.error("--pause-ms must be between 0 and 1000")
    if not 0.1 <= args.max_load_per_cpu <= 2.0:
        parser.error("--max-load-per-cpu must be between 0.1 and 2.0")

    result = _run(
        args.iterations,
        args.payload_bytes,
        pause_seconds=args.pause_ms / 1000,
        max_load_per_cpu=args.max_load_per_cpu,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
