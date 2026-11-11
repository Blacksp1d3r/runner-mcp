# #669 — Offline versioned generation-layout child

## Goal
Check structural safety of a versioned release directory whose leaf encodes a pinned source commit and wheel SHA-256, WITHOUT claiming the directory is immutable or actively executing.

## Scope and ownership
- Source: src/runner_mcp/generation_layout_preflight.py
- Tests: tests/test_generation_layout_preflight.py
- Authority: umbrella issue #669; preceding offline manifest PR #690 merged source-only.
- Allowed: source change, synthetic tests, CI and public topology/roadmap.
- Forbidden: active process provenance promotion, private host access, installer/activation, production mutations or treating Unix mode as proof of immutability.

## Inputs and contract
- Explicit absolute generation directory named generation-<40 lowercase hex commit>-<64 lowercase hex wheel digest>, expected source and wheel digest.
- Fail closed on symlink ancestors, unsafe write permissions, wrong identity, relative/traversed name or missing directory.
- Results: offline_layout_match or unverified; active identity always false/null.

## Acceptance and limitations
- Ruff/pytest and independent CI at exact HEAD. Test wrong generation, linked root/ancestor, writable mode and path traversal.
- Directory naming and owner/mode do not prove actual module hashes, trusted origin, process identity or immutable filesystem. Those remain distinct future gates.
- A6/A7 original-client, release/rollback requirements remain outside this source child.

## Handover
See STATE.md, docs/diagnostics/topology/SYSTEM_TOPOLOGY.md and issue #669.
