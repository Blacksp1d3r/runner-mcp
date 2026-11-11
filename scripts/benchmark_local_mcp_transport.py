from __future__ import annotations

import argparse
import http.client
import json
import math
import os
import statistics
import threading
import time
import urllib.parse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from runner_mcp.bridge_mcp_executor import LocalMCPClient, LocalMCPConfig

_SESSION_ID = "faster13-benchmark-session"
_TOKEN = "faster13-benchmark-token-0000000000000000"


class _BenchmarkServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], payload_bytes: int) -> None:
        super().__init__(server_address, _BenchmarkHandler)
        self.payload_bytes = payload_bytes


class _BenchmarkHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *args: object) -> None:
        del args

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            request = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error(400)
            return

        method = request.get("method")
        if method == "initialize":
            body = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "serverInfo": {"name": "faster13-benchmark", "version": "1"},
                },
            }
            self._write_json(200, body, include_session=True)
            return

        if method == "notifications/initialized":
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if method == "tools/call":
            server = self.server
            if not isinstance(server, _BenchmarkServer):
                self.send_error(500)
                return
            result_payload = {
                "status": "ok",
                "padding": "x" * max(0, server.payload_bytes),
            }
            result_text = json.dumps(
                result_payload,
                sort_keys=True,
                separators=(",", ":"),
            )
            body = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False,
                },
            }
            self._write_json(200, body, include_session=False)
            return

        self.send_error(404)

    def _write_json(
        self,
        status: int,
        payload: dict[str, object],
        *,
        include_session: bool,
    ) -> None:
        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if include_session:
            self.send_header("Mcp-Session-Id", _SESSION_ID)
        self.end_headers()
        self.wfile.write(raw)


class _PersistentMCPBenchmarkClient:
    """Benchmark-only MCP client using one persistent HTTP connection."""

    def __init__(self, endpoint: str) -> None:
        parsed = urllib.parse.urlsplit(endpoint)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
            raise ValueError("benchmark endpoint must be ephemeral loopback HTTP")
        if parsed.port is None:
            raise ValueError("benchmark endpoint requires an explicit port")
        self._path = parsed.path or "/mcp"
        self._connection = http.client.HTTPConnection(
            parsed.hostname,
            parsed.port,
            timeout=10,
        )
        self._session_id: str | None = None
        self._request_id = 1
        self._initialize()

    def close(self) -> None:
        self._connection.close()

    def _initialize(self) -> None:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "faster13-persistent-benchmark",
                        "version": "1",
                    },
                },
            }
        )
        if "error" in response:
            raise RuntimeError("benchmark MCP initialization failed")
        self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
            expect_body=False,
        )

    def call_runtime_status(self) -> object:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_id(),
                "method": "tools/call",
                "params": {
                    "name": "runtime_status",
                    "arguments": {},
                },
            }
        )
        result = response.get("result")
        if not isinstance(result, dict):
            raise TypeError("benchmark MCP tool result is invalid")
        content = result.get("content")
        if not isinstance(content, list) or len(content) != 1:
            raise TypeError("benchmark MCP tool content is invalid")
        item = content[0]
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise TypeError("benchmark MCP tool content is invalid")
        return json.loads(item["text"])

    def _allocate_id(self) -> int:
        request_id = self._request_id
        self._request_id += 1
        return request_id

    def _post(
        self,
        payload: dict[str, object],
        *,
        expect_body: bool = True,
    ) -> dict[str, object]:
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "faster13-persistent-benchmark",
        }
        if self._session_id is not None:
            headers["Mcp-Session-Id"] = self._session_id

        self._connection.request(
            "POST",
            self._path,
            body=raw,
            headers=headers,
        )
        response = self._connection.getresponse()
        body = response.read()
        if self._session_id is None:
            self._session_id = response.getheader("Mcp-Session-Id")
        if response.status not in {200, 202}:
            raise RuntimeError("benchmark MCP request failed")
        if not expect_body:
            return {}
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise TypeError("benchmark MCP response is invalid")
        return parsed


@contextmanager
def _fixture_server(payload_bytes: int) -> Iterator[str]:
    server = _BenchmarkServer(("127.0.0.1", 0), payload_bytes)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/mcp"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _percentile(samples: list[float], percentile: float) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[rank]


def _measure(
    iterations: int,
    operation: Callable[[], Any],
    *,
    pause_seconds: float,
) -> dict[str, object]:
    samples_ms: list[float] = []
    started = time.perf_counter()
    for _ in range(iterations):
        before = time.perf_counter_ns()
        operation()
        after = time.perf_counter_ns()
        samples_ms.append((after - before) / 1_000_000)
        if pause_seconds:
            time.sleep(pause_seconds)
    elapsed = time.perf_counter() - started
    return {
        "elapsed_seconds": round(elapsed, 6),
        "calls_per_second": round(iterations / elapsed, 2),
        "latency_ms": {
            "min": round(min(samples_ms), 4),
            "mean": round(statistics.fmean(samples_ms), 4),
            "p50": round(_percentile(samples_ms, 0.50), 4),
            "p95": round(_percentile(samples_ms, 0.95), 4),
            "p99": round(_percentile(samples_ms, 0.99), 4),
            "max": round(max(samples_ms), 4),
        },
    }


def _relative_latency(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, float]:
    baseline_latency = baseline["latency_ms"]
    candidate_latency = candidate["latency_ms"]
    if not isinstance(baseline_latency, dict) or not isinstance(candidate_latency, dict):
        raise TypeError("benchmark latency result is invalid")
    result: dict[str, float] = {}
    for key in ("mean", "p50", "p95", "p99"):
        baseline_value = float(baseline_latency[key])
        candidate_value = float(candidate_latency[key])
        if baseline_value <= 0:
            raise RuntimeError("benchmark baseline latency must be positive")
        result[f"{key}_speedup_x"] = round(baseline_value / candidate_value, 3)
        result[f"{key}_reduction_percent"] = round(
            (1 - (candidate_value / baseline_value)) * 100,
            2,
        )
    return result


def _load_gate(max_load_per_cpu: float) -> dict[str, object]:
    cpu_count = max(1, (os.cpu_count() or 1))
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


def _run(
    iterations: int,
    warmup: int,
    payload_bytes: int,
    *,
    pause_seconds: float,
    max_load_per_cpu: float,
) -> dict[str, object]:
    result_payload = {
        "status": "ok",
        "padding": "x" * max(0, payload_bytes),
    }
    encoded_result = json.dumps(
        result_payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    gate = _load_gate(max_load_per_cpu)
    direct = _measure(
        iterations,
        lambda: result_payload["status"],
        pause_seconds=pause_seconds,
    )
    json_roundtrip = _measure(
        iterations,
        lambda: json.loads(
            json.dumps(
                result_payload,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
        pause_seconds=pause_seconds,
    )

    with _fixture_server(payload_bytes) as endpoint:
        client = LocalMCPClient(
            LocalMCPConfig(
                endpoint=endpoint,
                bearer_token=_TOKEN,
                request_timeout_seconds=10,
            ),
            allowed_tools=frozenset({"runtime_status"}),
            client_name="faster13-benchmark",
        )

        for _ in range(warmup):
            client._call_tool("runtime_status", {})

        mcp_loopback = _measure(
            iterations,
            lambda: client._call_tool("runtime_status", {}),
            pause_seconds=pause_seconds,
        )

        persistent = _PersistentMCPBenchmarkClient(endpoint)
        try:
            for _ in range(warmup):
                persistent.call_runtime_status()
            mcp_persistent_http = _measure(
                iterations,
                persistent.call_runtime_status,
                pause_seconds=pause_seconds,
            )
        finally:
            persistent.close()

    return {
        "schema_version": "faster13/local-mcp-baseline/v2",
        "iterations": iterations,
        "warmup": warmup,
        "payload_bytes_requested": payload_bytes,
        "payload_bytes_encoded": len(encoded_result.encode("utf-8")),
        "shadow_mode": {
            "single_threaded": True,
            "pause_ms": round(pause_seconds * 1000, 3),
            "load_gate": gate,
        },
        "baselines": {
            "direct_python": direct,
            "json_roundtrip": json_roundtrip,
            "mcp_loopback_http_urllib": mcp_loopback,
            "mcp_loopback_http_persistent": mcp_persistent_http,
        },
        "comparisons": {
            "persistent_vs_urllib": _relative_latency(
                mcp_loopback,
                mcp_persistent_http,
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the existing loopback LocalMCPClient against a synthetic "
            "read-only MCP fixture. No external endpoint is accepted."
        )
    )
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--payload-bytes", type=int, default=256)
    parser.add_argument(
        "--pause-ms",
        type=float,
        default=2.0,
        help="Pause between measured operations; defaults to a low-impact shadow run.",
    )
    parser.add_argument(
        "--max-load-per-cpu",
        type=float,
        default=0.75,
        help="Refuse to start when 1-minute load divided by logical CPUs exceeds this value.",
    )
    args = parser.parse_args()

    if not 1 <= args.iterations <= 10_000:
        parser.error("--iterations must be between 1 and 10000")
    if not 0 <= args.warmup <= 10_000:
        parser.error("--warmup must be between 0 and 10000")
    if not 0 <= args.payload_bytes <= 1_000_000:
        parser.error("--payload-bytes must be between 0 and 1000000")
    if not 0 <= args.pause_ms <= 1000:
        parser.error("--pause-ms must be between 0 and 1000")
    if not 0.1 <= args.max_load_per_cpu <= 2.0:
        parser.error("--max-load-per-cpu must be between 0.1 and 2.0")

    print(
        json.dumps(
            _run(
                args.iterations,
                args.warmup,
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
