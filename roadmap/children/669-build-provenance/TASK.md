# #669 — Active build provenance (fail-closed first stage)

## Ownership and dependencies
- Parent: Runner-MCP #669 (build/source provenance); cross-ref #590 and #341
- Release chain: PR #661 v0.1.4 -> PR #668 v0.1.5 -> PR #670 v0.1.6 -> this child v0.1.7
- Source scope: build_identity.py, server.py, unit regression tests, four version manifests, this child TASK/STATE
- Security rule: DO NOT alter or erase self-update-state.json; it is historical transaction/rollback state

## Confirmed defect
An attended pinned-wheel installation of v0.1.4 produced byte-for-byte parity across 100 package Python files, while the connected build_identity tool continued to report an older self-update commit. build_identity.installed_source_revision() used only the historical self-update-state.json commit as if it identified the currently serving installed wheel. Distribution metadata version() can also switch after an in-place wheel upgrade before the old server process has restarted.

## Bounded first fix
- Move historical transaction read into last_self_update_revision(), leaving its validation intact.
- Active installed_source_revision() fails closed to unknown until separately verified serving artifact provenance exists; never infer current source from historical self-update state.
- Bind live identity.build_version and runtime_status.version to the version imported into the serving process, not re-read post-upgrade distribution metadata; label installed_distribution_version explicitly separately.
- Expose categorical active_build_provenance_verified=false, active_artifact_revision=null, active_artifact_digest=null rather than presenting a fabricated identity.
- Add regressions for manual wheel-upgrade with old marker, malformed or linked historical state, and dist-info changes after process import.
- Bump all source/discovery version manifests uniquely to v0.1.7.

## Explicitly not complete in this child
This is **NOT full artifact attestation**. It deliberately reports UNKNOWN, rather than a false SHA or digest. Follow-up #669 phase 2 requires independently verifiable actual wheel digest and pinned source commit, a trusted installation receipt independent of self-update history, loaded-module/generation checks, installer/restore integration, original-client route + ACK, negative tamper tests. Do not claim digest verification, signed attestation or release activation from this patch.

## Acceptance
1. Exact HEAD Ruff, pytest, release artifact and clean Ubuntu installer CI pass; all source metadata versions aligned.
2. GitHub source has no historic-self-update-to-active provenance shortcut; manually installed wheel test reports null active source/digest.
3. Independent source/security review, guarded merge of upstream chain, A6/A7 rollback and original client ACK before production rollout. No current host mutation, network changes, or credential exposure.
4. Existing live v0.1.4 and attended cron tunnel PATH workaround remain undisturbed.

## Review and rollback
No automatic merge; no host update without independent A6/A7 gate. Revert source branch through protected PR if it fails tests, preserve last known-good 0.1.3 operator backup and v0.1.4 actual runtime until separately admitted. Incomplete artifact signature/report => WAIT.
