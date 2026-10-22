## 2026-10-22 — #341 fixed Black Control Center issuer proxy SOURCE CANDIDATE (live ACK WAIT)

- Runner-MCP candidate v0.1.80 adds optional `control_center_black_submit/status/ack` tools for ONLY `runner:black`/`runtime_status`, using existing authenticated `FabricBridgeClient` and no direct relay, arbitrary endpoint, host, operation, shell or second updater. Strict typed validator binds returned request ID, fixed target, fingerprint, MFA original requester, version, terminal digest and explicit post-ACK readback; wrong target/replay/foreign identity fail closed.
- **Missing upstream capabilities:** Fabric Agent MCP does not yet publish these three bounded methods backed by its EXISTING `ControlRelayCommandClient`. Its client historically uses incompatible internal relay issuer route; AIfordable #585 PR #632 proposes adding digest/ACK to EXISTING MFA operator REST `/control-relay/commands`; Fabric must adapt real operator bearer/HTTP201/schemas. Fabric PR #1701 receipt-bound status is already MERGED and must be reused.
- Work is source-only pending exact-head CI; cannot send a real Black request with central serving v0.1.38. Physical original-client result/durable ACK remains WAIT, as does #669 correct-host provenance. Three Black services and six protected central roles remain untouched. Root cause RMCP-F-0072; child `roadmap/children/341-control-center-black-runtime/`. Do not close #341 or claim live until AIfordable, Fabric and one actual original-client MFA command -> Black result -> verified explicit ACK are independently qualified.

# Runner-MCP #669 / #341 / #747 — one-source-release and one-host-activation flow

Coordination authority: [Runner-Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924); canonical integration [single-flow contract](https://github.com/Blacksp1d3r/Runner-Fabric/blob/main/docs/coordination/CONTROL_PLANE_SINGLE_FLOW.md) (effective once Fabric coordination PR merges). This is a **Runner-MCP-owned** source and bounded-executor plan, NOT approval to install, reboot, restart, enroll agents, rewrite old state, or claim serving provenance from a source manifest.

## Observed facts and existing code — do not redo

- Main Runner-MCP commit `601afc953495fa0c2faa511d4601186ff269e034` **SOURCE MERGED** candidate 0.1.41: workspace PR #751 from issue #747 implements idempotent, path-safe, account-local `coding_workspace_preflight` and `coding_workspace_prepare`.
- #742 **SOURCE MERGED** 0.1.40: wheel/installed RECORD, signed offline candidate and fail-closed active provider checks; these do **not** attest loaded process. #669 draft PR #750 adds signed witness statement consistency only; it is not a trusted correct-host observer or deployed release.
- Central connected Runner-MCP 0.1.38, active source/wheel null, `self_update_ready=false`, Doctor `source_baseline_drift` and `active_revision_unavailable` (correct). Do not edit historical `self-update-state.json` to mask the two flags.
- AIfordable #585 PR #608 durable original-requester result fingerprint ACK **SOURCE MERGED**; Fabric #1602 strict future heartbeat **SOURCE MERGED**; Fabric A6 #942/A7 #943 physical subset trials already exercised. Live remote peer/ACK, A6 journal and A7 complete local Runner-MCP recovery acceptance remain separate.
- Source collision guard `scripts/check_release_reservation.py` is now **SOURCE MERGED** in 0.1.45 PR #753. The `Release reservation admission` job checked current main+1, competing READY PRs, exact synthetic HEAD and freshness before+after and PASSED on the actual ready PR. The older monotone `check_release_version.py` remains in use. This new check is not an atomic merge lock and is NOT independently proven REQUIRED by GitHub protection; CI success and branch-rule admission are separate.

## Source release manager — single accountable owner and atomic steps

1. Every shipping source PR is assigned to one issue/child and distinct owner; one designated Runner-MCP release steward owns **only** version ordering / PR dependency graph, not other workers' feature code.
2. Before allocating a version **and again immediately before ready/merge**, read canonical GitHub main HEAD/version, every active release PR with base/head/version (including stacked), and actual reserved next versions. A stale hardcoded number is not a reservation. One monotonic ledger maintained through GitHub and checked via CI/lease; use protected write/CAS semantics so two chats cannot reserve the same version silently.
3. For normal 0.1.patch releases, allocate the smallest unused next patch in strict merge order. A major/minor jump requires separate explicit, reviewable release intent; do not silently leap over in-flight patches. Ensure four metadata identities (`pyproject.toml`, `server.json` top/package, `glama.json`, `src/runner_mcp/__init__.py`) and changelog match.
4. On merge conflicts or main advancing, the **feature PR owner** rebases/reconciles on latest main while preserving ALL already merged changes; rerun exact-head release gate, all lint/pytest/artifact/demo/Ubuntu and attribution. Do not force-push others' PR heads or replace another owner's source. A green check from an older head/base does not qualify a new candidate.
5. Normal merges may proceed after exact-head enforced GitHub rules/CI. There is no artificial 12/24h wait, but **release collision**, security or protected main conflicts block that individual merge. Source merge != wheel-published != installed != live-verified.

### Current source sequence and remaining release enforcement (2026-10-19)

Merged `main` source v0.1.45: #743 → 0.1.42, #745 → 0.1.43, #750 → 0.1.44, #753 → 0.1.45 with final-head CI and real READY admission PASS. Former collision is no longer a blocker for this sequence. PRs #746/#748 remain OPEN against obsolete proposed v0.1.43/0.1.44 and must be handled by their respective owners on fresh actual main; do not silently retarget them. The 0.1.45 source has **NOT** been deployed on central live 0.1.38.

GitHub integration branch protection GET=403 and visible rulesets []; never infer the release-admission job is REQUIRED. An administrator must enforce latest-head/current-main release admission, serialize merges under the designated steward, and separately add qualified `merge_group` paths before a merge queue. Automatic candidate staging / guarded deployment and original-client Agent Bus ACK remain separate future work. Refer to #662 and `docs/operations/RELEASE_RESERVATION_GATE.md`.

## Worker/runtime acceptance: correct account, one target

- Runner-MCP owns only a bounded **local** operation: workspace tools must run under the actual approved Claude service account or inside the Qwen worker guest, with a separately configured preexisting permitted root. Central Runner-MCP cannot create directories remotely or cross an OS UID boundary by tool parameter.
- AIfordable #428 is the sole source for real asset/UID/service identity and scoped issuer credential; #585 owns authenticated existing relay, heartbeat, request/result and durable original requester ACK; #609 owns the end-to-end one-worker-at-a-time acceptance.
- Correct-host loaded wheel/RECORD/imported-process/source/protocol and all actual roles must be attested through separately trusted signer/issuer and fresh original-client return path (#669/#590). Offline signatures and source CI never imply `active_build_provenance_verified=true`.
- Fabric #924 owns the ONLY operator-attended per-target installation/rollout lease and A6/A7 recovery evidence; do not duplicate its updater/supervisor or the relay. Preserve already demonstrated October 18 guarded physical subset evidence.
- Reuse approved existing host/guest filesystems, no new mount or credential copy. One target at a time: exact host account and current runtime proof → Fabric admission+rollback → one guarded activation → original requester digest ACK → `coding_workspace_preflight` and one idempotent `prepare` under the worker-local UID, wrong-worker/readback negative checks → separate second target → guarded dispatch. All unknown statuses remain WAIT.

## Bounded automation follow-up: deterministic release reservation gate

**SOURCE IMPLEMENTED AND MERGED as #753 v0.1.45; remaining operational GitHub-policy/merge-group enforcement is NOT COMPLETE.** The implemented source is bounded, non-mutating and regression-tested. The original acceptance contract was:
1. PR synthetic merge compares current main version/HEAD to PR metadata; denies same version, downgrade, and unapproved non-consecutive patch for normal releases.
2. Fetches/validates all open release PRs and intentional stacked dependency graph with a scoped read-only GitHub credential; prevents TWO PRs with same reserved version from becoming merge-admissible without a clear deterministic winner/lease. Fail **closed or WAIT** when authority/API evidence unavailable; never infer uniqueness from empty/unavailable results.
3. Uses one collision/admission status on current head, guarded by actual GitHub branch protections; a check not made required cannot guarantee race prevention. Design the exact GitHub merge gate so an upstream merge invalidates/rechecks stale PR code.
4. Covers parallel PRs, stacked branches, same-version identical package metadata with different code, base drift, mid-run main advancing, API errors and manual minor/major exception. No false “CI passed” when the job did not run. Add tests, Failure Museum regression, version bump on that source PR and handover.
5. This child concerns **only source release coordination**, not a host update/credential/agent start.

## Shared proof states and handoff

Use `SOURCE_MERGED`, `STAGED`, `INSTALLED_UNVERIFIED`, `SERVING_VERIFIED`, `ACK_VERIFIED`, `ACTIVATION_ALLOWED` as different states, not synonyms. Evidence: issue owner, exact PR/base/head, source & wheel SHA, attested target asset/role/generation, trusted issuer/freshness, rollback A6/A7 receipt ref, original requester result fingerprint ACK, user/operator approval. Public GitHub only has redacted status. Maintain roadmap, topology and session handover with the **same** current GitHub truth; stale historical handovers are not current authority.
