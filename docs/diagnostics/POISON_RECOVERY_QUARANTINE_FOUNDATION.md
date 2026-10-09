# Poison recovery quarantine — bounded ledger foundation (#531)

Status: **SOURCE ONLY / NOT ACTIVATED**. No production watcher, cursor advancement, GitHub mailbox action or MCP tool currently uses this module. The existing explicit malformed-request recovery mechanism remains unchanged.

## Motivation and failure sequence

When `GitHubMailboxWatcher.run_cycle` discovers an ambiguous claim or malformed request, its existing `RecoveryObservation` prevents the high-water cursor from advancing. Persistent failure can therefore revisit the same historical request every cycle, even while subsequent valid requests are processed. Advancing the cursor or silently dropping failed items would lose evidence; automatically retrying forever is also unacceptable.

## Foundation implemented by `recovery_quarantine.py`

- A bounded local file ledger keyed by validated request ID and an opaque 64-hex canonical failure fingerprint, with only allow-listed `RecoveryFailureKind` categories
- Three deterministic failures by default transition the record to `operator-required`; further identical failures are idempotent and never mutate a terminal record
- A conflicting fingerprint/category fails closed instead of overwriting evidence; a new unrelated request has independent retry state
- Strict schema/count/range validation on each read, exclusive advisory lock on mutations, owner-private directory and ledger, `O_NOFOLLOW` and fsync
- Explicit, exact-fingerprint operator rearm is a **data-layer guard**, not an authorization service; any future caller must independently prove operator rights/approval
- Records survive reopening the same file, corruption fails closed, and bounded capacity refusal does not evict historical evidence
- No raw exception, user request payload, secret, path or executable authority is stored in the public recovery reason category

## Not yet implemented; separate child before switching the watcher

1. Trusted mapping from fixed watcher failure classes and canonical, bounded request fingerprint to ledger records; never accept caller-defined unbounded category or override
2. An explicit, fail-closed strategy for cursor progression past terminal quarantined requests while preserving queryable provenance and reappearance prevention across restart
3. Replay/rearm authorization with audit, no generic shell, immutable history or signed operator receipts as required by production policy
4. Negative end-to-end tests for poison item + later good request, restart, changed head, duplicate poison identity and disk/full-write failure
5. Protected local source binding, capacity planning, scheduled retention and recovery from interrupted writes; no live activation without these

The ledger now uses a separate, stable, owner-private `.lock` inode and writes a new, private temp file, fsyncs it, atomically replaces the JSON and fsyncs the parent directory while holding that lock. Failures before replacement leave the prior complete JSON unchanged. Failures between replacement and directory sync may leave the old **or** new complete state and must be treated as unproven until reread; no partial JSON is ever intentionally published. Synthetic interrupted-replace/temp-fsync and concurrent writer tests check the invariants. This is a source-level proof, not a power-loss test on the real filesystem.

Still to qualify before watcher activation: operator rearm audit/provenance must preserve previous terminal evidence; a data-layer boolean is not authorization. Request fingerprints must be constructed from trusted canonical evidence, and cursor advancement must be atomic with terminal quarantine evidence (children #616/#617).

This PR provides a testable state foundation only. Its green CI must not be represented as an end-to-end watcher convergence fix or operational qualification.
