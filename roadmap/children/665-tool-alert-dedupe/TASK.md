# #665 source-only typed mismatch alert deduplication

## Goal
Provide a pure bounded deterministic summary of already-authenticated, typed tool mismatch observations, grouped by independently supplied opaque scope fingerprint, stable tool ID, and mismatch reason. Count repeated observations within a configurable cooldown rather than emit per-poll notifications.

## Code
- src/runner_mcp/tool_alert_dedupe.py
- tests/test_tool_alert_dedupe.py
- Candidate source version 0.1.23

## Contract and authority
- Maximum 1024 sorted observations. Scope fingerprint must be a lowercase 64-hex value, stable tool id lowercase bounded, reason a ToolIdentityReason enum; unsigned/nonmonotonic timestamps and malformed booleans are rejected.
- Cooldown 1..86400 seconds, synthetic timestamps passed by trusted caller; no clock reads, network, datastore, worker, webhook, email, or notifications.
- READY observations excluded, all other typed reasons summarized; no path/error strings, credentials, hostname or private user data allowed.
- Result is a *possible sanitized alert digest*, NOT proof of a real security incident, persistent dedupe, successful delivery, acknowledgement or authorization to alert customers. A malicious caller may forge timestamps, scope and reasons unless upstream attests them.
- No server dispatch integration, no Fabric inventory mutation.

## Acceptance
- Tests cover window boundary, scope-tool-reason separation, READY suppression, invalid event/scope/id, forged reason, nonmonotonic sequence and strict resource bounds.
- Exact-head GitHub CI lint/pytest/demo/build/Ubuntu/attribution must pass before source merge.
- Parent #665 remains open for authenticated serving build observations, customer inventory persistence, durable deduplication and operator-approved alert notification/ACK.
- Operator deferred rollback timer until customer deployment. Live server stays unchanged.
