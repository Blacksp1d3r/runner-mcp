# #664 — legacy callable-signature regression guard (tests only)

## Purpose
Freeze an explicitly identified subset of currently registered legacy MCP tool callable signatures so changes to existing names, required arguments, defaults, annotations and tool registration fail CI before customers receive a newer universal build.

## Grounding
- Baseline: tests/fixtures/legacy_tool_callable_signatures_v0123.json
- Guard: tests/test_legacy_tool_signature_regression.py
- Captured from main 53a002df136d010ebe460643a37ddcf86af58c6e, source package 0.1.23.
- Only AST/source registration and signature snapshot. Does NOT claim released wheel v0.1.9 schema snapshots, JSON-RPC tool output equivalence or full historic customer compatibility.
- No production code modified and no version bump required (test-only PR).

## Acceptance
- Guard catches removed/unregistered tools, argument/default drift, return type annotation drift on explicit baseline subset.
- Malformed or duplicate fixture identifier denied by tests. No runtime invocation, live host, credentials or actual traffic.
- Exact source-head CI lint/pytest/release demo/Ubuntu/attribution green before merge.
- Parent #664 remains open for genuine released wheel snapshots and generated input/output JSON schema/backwards compatibility with v0.1.9 and other supported trains; commercial support decision remains operator-owned.
- Existing #665 identity/alert source slices are merged; do not duplicate or claim authenticated serving build.

## Safety
No tools/list or tools/call changes, no broken older client; rollback timer remains deferred to customer phase.
