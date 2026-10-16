# Fabric update readiness failure visibility

Parent: Runner-MCP #590 and Runner-Fabric Fleet #924.

The existing two read-only updater preflights can return generic connector errors when artifact metadata, local recovery or managed-launcher checks fail. Keep their successful response contracts unchanged, but return a bounded blocked status with a fixed allowlisted reason rather than leaking raw failure text or turning an unknown error into a positive signal. This change does not build, stage, install or approve a release.

Scope: existing `fabric_update.py` reason helper and existing `server.py` read-only wrappers; new negative tests, four version files aligned at source candidate 0.1.26. Other updaters, host control, permissions and transport unchanged.

Acceptance: exact-head lint, pytest, release build/demo, installer and attribution green before merge. Unknown errors are blocked and sanitized; `artifact_ready` is always false on failure. The installed Runner-MCP runtime remains separately unqualified; A6/A7, trusted host identity and original-client ACK are not replaced.
