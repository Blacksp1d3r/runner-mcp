# Runner-MCP #669 / #341 / #747 — one-source-release and one-host-activation flow

Coordination authority: [Runner-Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924); canonical integration [single-flow contract](https://github.com/Blacksp1d3r/Runner-Fabric/blob/main/docs/coordination/CONTROL_PLANE_SINGLE_FLOW.md) (effective once Fabric coordination PR merges). This is a **Runner-MCP-owned** source and bounded-executor plan, NOT approval to install, reboot, restart, enroll agents, rewrite old state, or claim serving provenance from a source manifest.

## Observed facts and existing code — do not redo

- Main Runner-MCP commit `601afc953495fa0c2faa511d4601186ff269e034` **SOURCE MERGED** candidate 0.1.41: workspace PR #751 from issue #747 implements idempotent, path-safe, account-local `coding_workspace_preflight` and `coding_workspace_prepare`.
- #742 **SOURCE MERGED** 0.1.40: wheel/installed RECORD, signed offline candidate and fail-closed active provider checks; these do **not** attest loaded process. #669 draft PR #750 adds signed witness statement consistency only; it is not a trusted correct-host observer or deployed release.
- Central connected Runner-MCP 0.1.38, active source/wheel null, `self_update_ready=false`, Doctor `source_baseline_drift` and `active_revision_unavailable` (correct). Do not edit historical `self-update-state.json` to mask the two flags.
- AIfordable #585 PR #608 durable original-requester result fingerprint ACK **SOURCE MERGED**; Fabric #1602 strict future heartbeat **SOURCE MERGED**; Fabric A6 #942/A7 #943 physical subset trials already exercised. Live remote peer/ACK, A6 journal and A7 complete local Runner-MCP recovery acceptance remain separate.
- Most important: the existing `scripts/check_release_version.py` enforces **greater than base** for shipping changes but does NOT check concurrent open PR version reservations or require the *next* patch for a normal patch release. It cannot itself prevent two independent agents from authoring the same next version. This is the precise source gap; do not misdiagnose GitHub CI scheduling as the cause.

## Source release manager — single accountable owner and atomic steps

1. Every shipping source PR is assigned to one issue/child and distinct owner; one designated Runner-MCP release steward owns **only** version ordering / PR dependency graph, not other workers' feature code.
2. Before allocating a version **and again immediately before ready/merge**, read canonical GitHub main HEAD/version, every active release PR with base/head/version (including stacked), and actual reserved next versions. A stale hardcoded number is not a reservation. One monotonic ledger maintained through GitHub and checked via CI/lease; use protected write/CAS semantics so two chats cannot reserve the same version silently.
3. For normal 0.1.patch releases, allocate the smallest unused next patch in strict merge order. A major/minor jump requires separate explicit, reviewable release intent; do not silently leap over in-flight patches. Ensure four metadata identities (`pyproject.toml`, `server.json` top/package, `glama.json`, `src/runner_mcp/__init__.py`) and changelog match.
4. On merge conflicts or main advancing, the **feature PR owner** rebases/reconciles on latest main while preserving ALL already merged changes; rerun exact-head release gate, all lint/pytest/artifact/demo/Ubuntu and attribution. Do not force-push others' PR heads or replace another owner's source. A green check from an older head/base does not qualify a new candidate.
5. Normal merges may proceed after exact-head enforced GitHub rules/CI. There is no artificial 12/24h wait, but **release collision**, security or protected main conflicts block that individual merge. Source merge != wheel-published != installed != live-verified.

### Currently known version collision (2026-10-19)

Main is now 0.1.41 via #751; existing **#743 also still 0.1.41** and cannot merge at that version, stacked **#745 is 0.1.42**, independently tested draft **#750 is 0.1.43**. Provisional order **only if no other main merge intervenes**: #743→0.1.42, #745→0.1.43, #750→0.1.44. The respective owners must reconcile; this documentation PR changes NONE of those heads. If other releases merge first, recompute the sequence from live main. A future deterministic CI/release reservation gate is REQUIRED but **not yet implemented**; track it as a separate bounded source child, because changing the current script itself is a shipping change requiring a unique version slot.

## Worker/runtime acceptance: correct account, one target

- Runner-MCP owns only a bounded **local** operation: workspace tools must run under the actual approved Claude service account or inside the Qwen worker guest, with a separately configured preexisting permitted root. Central Runner-MCP cannot create directories remotely or cross an OS UID boundary by tool parameter.
- AIfordable #428 is the sole source for real asset/UID/service identity and scoped issuer credential; #585 owns authenticated existing relay, heartbeat, request/result and durable original requester ACK; #609 owns the end-to-end one-worker-at-a-time acceptance.
- Correct-host loaded wheel/RECORD/imported-process/source/protocol and all actual roles must be attested through separately trusted signer/issuer and fresh original-client return path (#669/#590). Offline signatures and source CI never imply `active_build_provenance_verified=true`.
- Fabric #924 owns the ONLY operator-attended per-target installation/rollout lease and A6/A7 recovery evidence; do not duplicate its updater/supervisor or the relay. Preserve already demonstrated October 18 guarded physical subset evidence.
- Reuse approved existing host/guest filesystems, no new mount or credential copy. One target at a time: exact host account and current runtime proof → Fabric admission+rollback → one guarded activation → original requester digest ACK → `coding_workspace_preflight` and one idempotent `prepare` under the worker-local UID, wrong-worker/readback negative checks → separate second target → guarded dispatch. All unknown statuses remain WAIT.

## Bounded automation follow-up: deterministic release reservation gate

Create a single-purpose CI child on an **independent** issue/branch after a unique version is allocated; no changes to #743/#745/#750 feature code. Acceptance:
1. PR synthetic merge compares current main version/HEAD to PR metadata; denies same version, downgrade, and unapproved non-consecutive patch for normal releases.
2. Fetches/validates all open release PRs and intentional stacked dependency graph with a scoped read-only GitHub credential; prevents TWO PRs with same reserved version from becoming merge-admissible without a clear deterministic winner/lease. Fail **closed or WAIT** when authority/API evidence unavailable; never infer uniqueness from empty/unavailable results.
3. Uses one collision/admission status on current head, guarded by actual GitHub branch protections; a check not made required cannot guarantee race prevention. Design the exact GitHub merge gate so an upstream merge invalidates/rechecks stale PR code.
4. Covers parallel PRs, stacked branches, same-version identical package metadata with different code, base drift, mid-run main advancing, API errors and manual minor/major exception. No false “CI passed” when the job did not run. Add tests, Failure Museum regression, version bump on that source PR and handover.
5. This child concerns **only source release coordination**, not a host update/credential/agent start.

## Shared proof states and handoff

Use `SOURCE_MERGED`, `STAGED`, `INSTALLED_UNVERIFIED`, `SERVING_VERIFIED`, `ACK_VERIFIED`, `ACTIVATION_ALLOWED` as different states, not synonyms. Evidence: issue owner, exact PR/base/head, source & wheel SHA, attested target asset/role/generation, trusted issuer/freshness, rollback A6/A7 receipt ref, original requester result fingerprint ACK, user/operator approval. Public GitHub only has redacted status. Maintain roadmap, topology and session handover with the **same** current GitHub truth; stale historical handovers are not current authority.
