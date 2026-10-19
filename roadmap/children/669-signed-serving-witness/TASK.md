# #669 — signed serving-witness consumer (source-only 0.1.43)

## Ownership and dependencies
Runner-MCP owns only a deterministic, read-only canonical signed-statement comparator. This child does NOT mint an observer identity, sign a host statement, introspect a live process, provision host credentials, alter an updater or grant an activation. Correct-host observer custody and authorization remain separately owned outside Runner-MCP (AIfordable #428); original-client ACK #590; Fabric A6 #942, A7 #943.

## Acceptance
- Require independently pinned Ed25519 public key hash, correct host digest, expected complete role set, nonce, source revision, wheel SHA256, generation digest, and trusted clock.
- Canonical signed JSON with exact schema, 5-minute max validity, unique process-role instance hashes, exact host/wheel/generation equality.
- Malformed, replayed challenge, stale, foreign host, wrong roles, duplicate role/process and invalid signatures remain `unverified`.
- Even a valid signed candidate has `active_build_provenance_verified=False`, source and artifact null. No runtime/Doctor green until independent observer and original-client proof.
- Tests, CI and gate evidence on exact head; no production or private signing key.
- Release sequencing: #743 v0.1.41 → #745 v0.1.42 → this candidate v0.1.43. Never merge ahead of dependent version reservations.

## Non-goals
Do not rewrite historical self-update state, add a competing updater, store keys, expose remote shell, inspect real host process, start Fleet updates or auto-merge a blocked stacked release.
