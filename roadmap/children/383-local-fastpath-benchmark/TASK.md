# FASTER-13 / #383 — local-only JSON/MCP framing baseline

## Scope
Capture a repeatable, fully synthetic baseline for JSON encoding and decoding of fixed tiny (128B), medium (4096B), large (65536B) JSON-RPC tool envelopes, p50/p95/p99 duration, bytes per call, calls/s, and fixed 500ms status-poll detection delay.

## Ownership
- Source: src/runner_mcp/fastpath_benchmark.py
- CLI: scripts/benchmark_mcp_fastpath.py
- Tests: tests/test_fastpath_benchmark.py
- Parent: #383; canonical cross-project Faster roadmap in AIfordable.

## Safety and truth
- No actual LocalMCPClient/HTTP round trip, network endpoint, tool invocation, server, credential, external billing, subprocess or host mutation occurs. This is serialization baseline only.
- Each measured host must record runtime CPU/load/version separately; results from a GitHub ephemeral CI runner must never be presented as local server wall times.
- Computed polling-delay values are deterministic scheduling models (not measured push-notification latency). No claim of faster path superiority until isolated reproducible end-to-end benchmarks.
- Do not replace canonical MCP or bypass bearer/session/fencing/replay semantics on future fast paths.

## Acceptance
- Fixed payload/repetition labels; stable schema; p50/p95/p99, bytes/call, throughput and deterministic polling examples.
- Unit tests for invalid inputs, percentile definitions and clear scope disclaimers.
- CLI callable from an installed runner-mcp environment with fixed repetitions 1..10000, emits machine-readable JSON.
- Exact PR HEAD Ruff/pytest/Ubuntu/demo/build/attribution green before source merge.

## Next child
Phase 1b: measure real authorized loopback read-only MCP RTT with separate trace/correlation ID, latency/CPU; isolated host qualification and loopback auth required. Then compare persistent sessions/pooling/push in phase 2 under same request authority. No production deployment approved.
