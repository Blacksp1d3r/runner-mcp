from __future__ import annotations

import argparse
import json
import math
import socket
import statistics
import struct
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path

FRAME = struct.Struct("!I")
HEADER = struct.Struct("!BBHQ16sI")
VERSION = 1
CLASS = 1
FLAGS = 1
CORR = bytes.fromhex("00112233445566778899aabbccddeeff")
MAX_PAYLOAD = 1_000_000
MAX_FRAME = MAX_PAYLOAD + 512
STOP = b"faster13-stop"


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def send_frame(sock: socket.socket, raw: bytes) -> None:
    if len(raw) > MAX_FRAME:
        raise ValueError("benchmark frame too large")
    sock.sendall(FRAME.pack(len(raw)) + raw)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    parts: list[bytes] = []
    while size:
        part = sock.recv(size)
        if not part:
            raise RuntimeError("benchmark peer closed")
        parts.append(part)
        size -= len(part)
    return b"".join(parts)


def recv_frame(sock: socket.socket) -> bytes:
    (size,) = FRAME.unpack(recv_exact(sock, FRAME.size))
    if size > MAX_FRAME:
        raise ValueError("benchmark frame too large")
    return recv_exact(sock, size)


def json_encode(sequence: int, payload: bytes) -> bytes:
    return json.dumps(
        {
            "version": VERSION,
            "class": CLASS,
            "flags": FLAGS,
            "sequence": sequence,
            "correlation": CORR.hex(),
            "payload": payload.decode("ascii"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def json_decode(raw: bytes) -> tuple[int, bytes]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("invalid JSON envelope")
    if (
        value.get("version") != VERSION
        or value.get("class") != CLASS
        or value.get("flags") != FLAGS
        or value.get("correlation") != CORR.hex()
    ):
        raise ValueError("JSON envelope identity mismatch")
    sequence = value.get("sequence")
    payload = value.get("payload")
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("invalid JSON sequence")
    if not isinstance(payload, str):
        raise TypeError("invalid JSON payload")
    return sequence, payload.encode()


def binary_encode(sequence: int, payload: bytes) -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("binary payload too large")
    return HEADER.pack(VERSION, CLASS, FLAGS, sequence, CORR, len(payload)) + payload


def binary_decode(raw: bytes) -> tuple[int, bytes]:
    if len(raw) < HEADER.size:
        raise ValueError("binary envelope truncated")
    version, message_class, flags, sequence, corr, size = HEADER.unpack_from(raw)
    if (version, message_class, flags, corr) != (VERSION, CLASS, FLAGS, CORR):
        raise ValueError("binary envelope identity mismatch")
    if size > MAX_PAYLOAD or len(raw) != HEADER.size + size:
        raise ValueError("binary envelope length mismatch")
    return sequence, raw[HEADER.size:]


def server(
    path: Path,
    ready: threading.Event,
    encode: Callable[[int, bytes], bytes],
    decode: Callable[[bytes], tuple[int, bytes]],
) -> None:
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(path))
        listener.listen(1)
        ready.set()
        conn, _ = listener.accept()
        with conn:
            while True:
                raw = recv_frame(conn)
                if raw == STOP:
                    return
                sequence, payload = decode(raw)
                send_frame(conn, encode(sequence, payload))
    finally:
        listener.close()


def mode(
    root: Path,
    name: str,
    iterations: int,
    payload: bytes,
    pause: float,
    encode: Callable[[int, bytes], bytes],
    decode: Callable[[bytes], tuple[int, bytes]],
) -> dict[str, object]:
    path = root / f"{name}.sock"
    ready = threading.Event()
    thread = threading.Thread(
        target=server,
        args=(path, ready, encode, decode),
        daemon=True,
    )
    thread.start()
    if not ready.wait(5):
        raise RuntimeError("benchmark server start timeout")

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    samples: list[float] = []
    cpu_before = time.process_time_ns()
    client.connect(str(path))
    try:
        for sequence in range(iterations):
            before = time.perf_counter_ns()
            send_frame(client, encode(sequence, payload))
            got_sequence, got_payload = decode(recv_frame(client))
            after = time.perf_counter_ns()
            if got_sequence != sequence or got_payload != payload:
                raise RuntimeError("benchmark roundtrip mismatch")
            samples.append((after - before) / 1000)
            if pause:
                time.sleep(pause)
        encoded_bytes = len(encode(42, payload))
        send_frame(client, STOP)
    finally:
        client.close()
        thread.join(5)
    if thread.is_alive():
        raise RuntimeError("benchmark server stop timeout")

    cpu_us = (time.process_time_ns() - cpu_before) / iterations / 1000
    return {
        "encoded_bytes": encoded_bytes,
        "process_cpu_us_per_roundtrip": round(cpu_us, 4),
        "latency_us": {
            "mean": round(statistics.fmean(samples), 4),
            "p50": round(percentile(samples, 0.50), 4),
            "p95": round(percentile(samples, 0.95), 4),
            "p99": round(percentile(samples, 0.99), 4),
            "max": round(max(samples), 4),
        },
    }


def compare(base: dict[str, object], candidate: dict[str, object]) -> dict[str, float]:
    base_latency = base["latency_us"]
    candidate_latency = candidate["latency_us"]
    if not isinstance(base_latency, dict) or not isinstance(candidate_latency, dict):
        raise TypeError("invalid benchmark latency result")
    result: dict[str, float] = {}
    for key in ("mean", "p50", "p95", "p99"):
        a = float(base_latency[key])
        b = float(candidate_latency[key])
        result[f"{key}_speedup_x"] = round(a / b, 3)
        result[f"{key}_reduction_percent"] = round((1 - b / a) * 100, 2)
    return result


def run(iterations: int, payload_bytes: int, pause: float) -> dict[str, object]:
    payload = b"x" * payload_bytes
    with tempfile.TemporaryDirectory(prefix="faster13-e2e-") as directory:
        root = Path(directory)
        json_result = mode(
            root, "json", iterations, payload, pause, json_encode, json_decode
        )
        binary_result = mode(
            root, "binary", iterations, payload, pause, binary_encode, binary_decode
        )
    return {
        "schema_version": "faster13/unix-envelope-e2e-shadow/v1",
        "payload_bytes_requested": payload_bytes,
        "iterations": iterations,
        "json_over_unix_stream": json_result,
        "binary_over_unix_stream": binary_result,
        "binary_vs_json": compare(json_result, binary_result),
        "shadow_mode": {"synthetic_only": True, "runtime_integration": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--payload-bytes", type=int, default=256)
    parser.add_argument("--pause-ms", type=float, default=1.0)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100_000:
        parser.error("invalid iterations")
    if not 0 <= args.payload_bytes <= MAX_PAYLOAD:
        parser.error("invalid payload size")
    if not 0 <= args.pause_ms <= 1000:
        parser.error("invalid pause")
    print(
        json.dumps(
            run(args.iterations, args.payload_bytes, args.pause_ms / 1000),
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
