# #333 — opt-in bounded tunnel state in runtime_doctor

## Goal
Connect the existing pure tunnel evidence classifier to the actual Runner-MCP `runtime_doctor` read-only MCP tool when the operator declares this connector tunnel expected, using only independently collected safe booleans.

## Ownership and code
- `src/runner_mcp/tunnel_readiness.py`: `bounded_doctor_tunnel_check` maps typed evidence to fixed, redacted doctor result.
- `src/runner_mcp/server.py`: append-only, opt-in `tunnel_expected` and read-only `tunnel_readiness_provider` to both build_mcp/create_app; actual doctor `connector_tunnel_readiness` only when explicitly expected. No existing tool signature changed.
- `tests/test_tunnel_doctor_evidence.py`: negative unknown/partial/unauthenticated/process down, redaction and strict expected flag.
- Candidate source 0.1.24.

## Safety boundary
- Default `tunnel_expected=False` leaves legacy runtime_doctor payload/check count unaffected.
- `expected=True` without authorized collector emits warn evidence_unavailable; it never claims process running or remote authenticated.
- Only a complete sequential verified routable evidence record reports pass; inconsistent or unavailable evidence cannot be upgraded. Private error strings never exposed.
- This source does NOT inspect process tables, secrets, filenames, health endpoints or credentials, and does not manage/autostart/restart tunnel. Collection/wiring to a trustworthy private host fixture remains operator/Fabric-owned.
- Live connected Runner MCP 0.1.9 does not get the new behavior until independently qualified rollout.
- Rollbacktimer deferred until customer rollout.

## Acceptance
Exact-head Ruff/pytest/build/demo/Ubuntu/attribution green, source merge. Parent #333 remains open for real private tunnel collector, reboot-safe managed restart and original-client remote ACK. No hidden tunnel commands, keys or process changes.
