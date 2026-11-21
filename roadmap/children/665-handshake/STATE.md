# #665 — Optional authenticated client handshake: STATE

- State: UNCLAIMED / PLANNED (2026-10-12)
- Parent: #665; proposed ADR PR #666
- Branch: not allocated; this file is planning-only
- Implemented: NO
- Tested: NO
- Production changed: NO
- Blockers/dependencies: registry; attestation; #664; #590
- Next safe action: reconcile active workers and main/release version policy, claim bounded files, implement first negative synthetic tests, assign next unique release version when shipping code.
- Evidence/CI: planning file only; not a completed test or release.

## 2026-10-12 design checkpoint
- Source design contract created: `docs/architecture/665-HANDSHAKE-COMPATIBILITY.md` at commit `167b732658b14dd89a7fc845a5629216be89950c`.
- Status: DESIGN_SPECIFIED / NO HANDSHAKE CODE / NO LIVE NEGOTIATION.
- Compatibility decisions cover standard MCP clients, authenticated build/schema matches, stale sessions, unknown-effect transport failures and no privilege-enhancing fallback.
- Parent #661 is open (independent review pending), #663 and #667 remain draft. Do not consume a duplicate source version or alter existing clients until those dependencies are reconciled.
- Next: independent protocol review and isolated negative tests in a separately versioned source PR. Active service, fleet alerts and original-client ACK unqualified.
