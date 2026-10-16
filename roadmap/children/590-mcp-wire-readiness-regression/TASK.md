# Runner-MCP #590 — existing readiness diagnostics over actual MCP transport

## Why
Source-only fixes #706 (optional Fabric guest status) and #707 (Fabric update readiness) passed unit tests but did not independently demonstrate that an authenticated MCP client receives the sanitized read-only result. Client-visible errors were historically the observed symptom.

## Bounded scope
Tests-only: `tests/integration/test_fleet_readonly_failure_mcp_wire.py` exercises an isolated `create_app` with Starlette's TestClient, normal MCP initialize/initialized/tool call, fixed synthetic failure providers, and the existing server callbacks. No executable production code, tool catalogue, version metadata, token or host behavior changes.

## Acceptance
1. Both GitHub and local-custody update-readiness errors produce tool `isError=false`, a bounded `blocked` envelope, allowed reason codes and `artifact_ready=false` rather than a generic connector exception.
2. Arbitrary private failure strings never appear in the MCP response, and no mutating `start` or `start_local` methods are called.
3. Both success contracts remain unchanged.
4. Optional CI guest status errors return `unavailable`, nullable/unknown registration and runtime, and false mutation/execution flags; never enroll/start.
5. Exact-head lint/pytest, full validation, clean Ubuntu installer and attribution pass. Merge without changing shipping version 0.1.26 if all gates pass.

## Limits
This is a disposable local protocol test, NOT live host or wheel attestation, actual remote connection / same-original-client ACK, A6/A7 recovery proof, customer rollout or backup qualification. Runner-MCP #669 / Fabric #942 / #943 remain open.
