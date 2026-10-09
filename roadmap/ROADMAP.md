## 2026-10-09 — Continuation: source drift duplicate closed, A6 doctor landed, F36 relay CI

- Existing #519 self-update source-baseline drift PR CLOSED WITHOUT MERGE: current main already has stronger installed/source alignment, active runtime revision, sanitized `runtime_doctor` source baseline and fail-closed pre-queue checks; security tests cover aligned/drift/unavailable and private error containment. Do not resurrect outdated large-file changes. Queue-to-activation TOCTOU acceptance remains a separate review.
- Existing #518 A6 `runtime_doctor` binding-state inspection was selectively restacked in-place on current main. Fixed Ruff imports and an onboarding/server circular-import hazard by deferring env-file loader import to invocation time. Exact head `8c9683a16dcbccece78a0d08a6722fa19dee5cf2`, attribution `37984556255` SUCCESS, full validation `37984556225` SUCCESS, squash merge `62c6832338370190e9b9dcee69478fa288031c61`. No A6 agent restart, private runtime query, self-update or campaign activation. Its state-root resolver was verified identical to existing restart resolver; layout qualification beyond that remains separate.
- Existing #412 F36 read-only continuity Agent Bus bridge was selectively restacked, retaining already existing MCP continuity-status tool and Fabric wrapper on main. Branch `f36-continuity-status-bridge`, current head `2c5e7c0233613ac8da76b4b734f2163efb8e1e2e`; exact-head attribution `37985552722` and validation `37985552667` IN_PROGRESS. Fixed complete adversarial action-matrix fixture and zero-argument `bridge_tool_call` mapping following pytest failures on previous heads. No merge until full exact-head green. No production connector/tunnel/Agent Bus mutation or new privilege.
- #590 intermittent external ChatGPT connector reply return/generation remains OPEN and unqualified. No live deployment, reboot, runner mutation or secret exposure.

## 2026-10-09 — Self-update source alignment and A6 dependency reconciliation

Existing PR #519 was CLOSED UNMERGED after explicit live-main proof that its requested source baseline protection is already implemented with stronger current `source_commit`, `source_baseline_aligned`, active runtime revision and `runtime_doctor` evidence. Main `SelfUpdateManager.start` rejects source drift and unavailability before queuing; current security tests cover aligned, drift, unavailable and nonleaking error outcomes. Prior #519 branch is stale; do not reopen or override current source. Queue-to-activation TOCTOU remains independently reviewable and not proven solved by queue-time checking alone.

Open PR #518 still adds a distinct, sanitized A6 binding diagnostic, NOT yet on main. Review identified possible unverified derivation of its state root from projects-config folder nesting; owner must prove it matches the same private canonical A6 root as restart on nondefault configurations or fail closed. No A6 prepare, agent restart or live update until exact proof. Reviewed on original PR, no duplicate branch created.

External #590 intermittent ChatGPT tunnel response route still OPEN. No live host, tunnel, credentials, CI runner, server service or customer workload touched.

## 2026-10-09 — Final autonomous checkpoint: #620/#526 merged, #511 superseded

- Exact-green PR #620 explicit ServiceBackend injection test: head `82a918902636376b2bc26b5a3f22475295d279b8`, attribution `37981372498` SUCCESS, Runner MCP validation `37981372754` SUCCESS, squash merged `4f7a7d8e16ac9fe23760800bed8a313c37eb8a4e`. Test-only. No Windows SCM adapter/service activation.
- Existing PR #526 bounded Fabric local-custody failures was selectively restacked on current main without losing unrelated changes; head `e44bd321c0551db68560ac99bc99e36368dc6e32`, attribution `37982010408` SUCCESS, validation `37982010409` SUCCESS, squash merged `cfd7101c9f370728d0aa0b5117d2ef0a40244700`. Known exact failure classes return bounded `blocked/reasonCode`, untrusted details are never emitted. No live Fabric staging/host/runtime mutation. #525 auto-closed and independently checked.
- PR #537 independent review noted `/proc/stat` busy CPU delta may be host-wide under Incus containers, so it cannot automatically be labelled OCR process CPU/page. Require verified VM/cgroup-process scope or treat CPU metric unknown; do not infer actual OCR speed gain. No OCR runtime change.
- PR #511 OLD disposable-target reason projection was investigated. Main already implements a STRICTER single-line prefix + allowlisted reason parser (`_bounded_failure_reason`) and returns structured `state=invalid` directly from the runner; main server generically blocks exceptions. Old #511 would reintroduce direct `str(exc)` MCP exposure and duplicate already merged functionality. Despite experimental branch-only hardening commits, PR #511 was CLOSED UNMERGED as SUPERSEDED after verified current-main comparison; do not resurrect/rebase or duplicate it. No main/deployed mutation from #511.
- External ChatGPT tunnel response-return issue #590 remains OPEN and unproven; current tunnel untouched. Next safe work: reconcile other stale PRs to main without overwriting stronger existing features; document first failing edge when qualified private response-delivery/dispatcher counters are available. No Desktop Commander, reboot, credentials, release or runner activation.

## 2026-10-09 — Latest continuation: #620 and #526 exact green MERGED

PR #620 test-only explicit service backend injection, exact head `82a918902636376b2bc26b5a3f22475295d279b8`: attribution `37981372498` SUCCESS, full validation `37981372754` SUCCESS, squash merge `4f7a7d8e16ac9fe23760800bed8a313c37eb8a4e`. Tests injected backend remains selected on Linux, Windows, unknown host families. No SCM implementation or live runtime mutation.

Existing Fabric custody PR #526 requalified in-place by selective source patch onto current main (four files, current content preserved), exact head `e44bd321c0551db68560ac99bc99e36368dc6e32`: attribution `37982010408` SUCCESS, full validation `37982010409` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `cfd7101c9f370728d0aa0b5117d2ef0a40244700`. Known allowlisted local-custody `FabricUpdateError` values return bounded `blocked/reasonCode`, unknown categories generic. This is a source-only diagnostic improvement; no live Fabric staging, server update or credentials changed. #525 may be auto-closed by merge; verify before manual state change.

Independent review on existing Bewind OCR PR #537 notes CPU time from `/proc/stat` may include host-wide load under Incus containers and must not be interpreted as OCR-only CPU/page without VM/cgroup qualification. No OCR job performed. External connector response path #590 remains unproven. No Desktop Commander, no production host/tunnel change.

## 2026-10-09 — #619 exact-head GREEN and MERGED (supersedes WAITING_CI)

New bounded source-only PR #619 (`fix/windows-service-backend-admission-20261009`) exact head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution run `37975695602` SUCCESS, full validation run `37975695551` SUCCESS (Ruff/pytest, built release artifact, clean demo), squash merge `bac86a97f1493ff943ef5f3d01228814e3ed61c0`. `ServiceManager._backend()` refuses default Linux SystemdUserBackend on Windows/unsupported host before instantiation; existing Linux and explicitly injected backends unchanged. Three regression cases passed. This does NOT implement Windows SCM, change actual Windows startup, grant remote authority, or activate any server. Broader #489 remains open for least-privilege SCM adapter and isolated Windows CI.

This session's other exact-green source merges: Faster shadow #460 `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`, first platform contract #490 `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. All are GitHub source changes only; no runtime/self-update/tunnel, CI enrollment, credentials, production/worker mutation. #590 remains OPEN, external response return route unqualified. Prior temporary WAITING_CI paragraphs below are superseded. Safe next independent work is review/reconcile existing owned open PRs (#526, #519, #518 etc.), not duplicate or merge without fresh head and ownership checks.

## 2026-10-09 — Faster-13 eventfd shadow + Windows host contract

#460 (shadow-only shared-memory/eventfd benchmark) exact-head attribution `37974721744` and full validation `37974721750` GREEN; squash merged `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`. Added 5s response deadline and guaranteed worker cleanup on failure with positive and negative tests. Not a production transport or OCR throughput improvement.

#490 (host-platform capability contract) exact-head attribution `37975249864` and validation `37975249793` GREEN; squash merged `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. Platform family `supported` is not Windows backend readiness: explicit `serviceAdapterImplemented` false for Windows, true for Linux implementation, false unsupported. Runtime Windows SCM not installed or qualified.

#619 implements a narrow further fail-closed guard on default service-manager backend selection for non-Linux. Latest head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution `37975695602` GREEN, full validation `37975695551` IN_PROGRESS. No merge until exact-head green. Linux normal/injected test backends remain unchanged. Subsequent Windows SCM implementation requires separate least-privilege, isolated Windows CI and deployment approval. #489 remains broader owner.

#590 external tunnel return-path identity remains OPEN; #599 source freshness guard already closed. No live host/tunnel changes.

## 2026-10-09 — Final landing: #456 fully GREEN and MERGED

Supersedes earlier #456 WAITING_CI: PR #456 exact head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262` SUCCESS (Ruff/pytest, release artifact, clean demo), squash merge `fc034b094c633b51889e2a13cc86727e2b1941fe`. Together with exact-green merges #465 `365a7a1f32f82e01da75004b800ed2948516fa9e`, #467 `4bba36e877d96246c93eb8064d6bf0d4af72de05` and #613 `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`, all four code PRs are integrated; no live server, CI selector, tunnel, credential or production transport mutation. New next-safe CI-aware action in following session: reconcile existing stacked PR #460 against merged #456 and newest main (do NOT duplicate PR), inspect CI and rebase only using exact branch name. #458 is a temporary hosted benchmark lab and explicitly DO NOT MERGE. #590 external connector response delivery still OPEN despite local JSON-RPC ID guard; remote health dispatcher/response-delivery snapshots remain unproven. #599 source-level auth freshness is closed. No OCR throughput claims from synthetic measurements.

## 2026-10-09 — Faster-13 staged synthetic PRs reconciled

Existing #514 baseline is merged. Three unique existing, bounded shadow-only follow-ups were restacked without duplicating PRs: #467 Unix envelope E2E (head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, validation `37962618480`), #465 compact envelope (head `9d1344beaef929acc9bac236a6c8d692dd48b988`, validation `37962706712`), and #456 Unix IPC (head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, validation `37962833262`, target base corrected to main after #514). At last review all three had Ruff/pytest green and demos still in progress; do not merge until respective exact-head full terminal success. #460 remains stacked behind #456; #458 is a temporary measurement lane explicitly DO NOT MERGE. A previous #467 branch-update blocker was caused by incorrectly guessed branch name; with exact GitHub PR head branch the ref update succeeded. No real OCR/production throughput claim, no routing or live host changes.

## 2026-10-09 — Local MCP JSON-RPC response identity guard landed

PR #613 head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97`: commit attribution `37962077429` SUCCESS and full validation `37962077446` SUCCESS, squash merged `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`. Internal `LocalMCPClient._post` now refuses replies with absent, mismatched, wrong-type JSON-RPC IDs; nine regression variants cover normal JSON and SSE. This does not prove external ChatGPT tunnel response delivery; issue #590 stays OPEN. #599 freshness source safeguard already merged via #609 and issue closed. Upstream `tunnel-client` local dispatcher/response-delivery component counters are documented as next safe first-failing-edge evidence, not a replacement for per-request identity proof.

## 2026-10-09 — #599 stale poll-authentication evidence reconciled

Issue #599 is **COMPLETE** on source: existing PR #609 exact head `04d0f493db9ba0ea00c4aa10e403e3823785e30b` passed validation `37957581774` and attribution `37958136637`, squash merged `ee29a791bb8dab96275ae3efc9987c6548a57bdd`. Current source rejects malformed, stale (>90s), or over-future (>5s) control-plane last_success; clock is injectable for deterministic tests, threshold grounded in documented 30s long-poll default. The issue was explicitly closed after source reconciliation. This does **not** prove the external connector route; #590 stays open. Independent internal LocalMCPClient JSON-RPC response-ID check is underway as draft PR #613, with no live tunnel changes. Do not recreate #599.

## 2026-10-09 — CI, tunnel and independent archive source gates landed

- Runner-MCP #584: #388 bounded local CLI **SOURCE COMPLETE** (`13a60429...`), #387 operator-dispatched cache-free qualifier **SOURCE COMPLETE** (`08bd1f96...`); live disposable guest, protected labels/network and no production secrets remain **BLOCKED**. Public hosted standard CI is free; no automatic replacement of current check selectors. Preserve exact required check names.
- Tunnel #599: conservative authenticated-poll freshness (`ee29a791...`) **MERGED / issue closed**, 30s documented default long-poll, 5s guardrail, 90s bounded age / 5s future skew; customized longer/backpressure not a tunnel-outage claim. External #590 remains **BLOCKED / UNLOCATED**, no production tunnel mutation.
- I5 independent protected release archive #586: zero-argument READ-ONLY semantic volume gate (`3077381b...`) **MERGED / issue closed**. No mirror-copy/restore performed; #585 parent still OPEN. Next hard dependencies AIfordable #537 and Runner-Fabric #1397 plus real operator volume/machine binding. #587 backup mutation and #588 restore qualification **BLOCKED** until those gates. Distinct filesystem `st_dev` is not physical disk identity or off-site DR.
- Other agents' Faster-13 / connector trace merges preserved; no requalification or duplicate branch.

## 2026-10-09 — Faster-13 local MCP baseline landed

Existing PR #514 was restacked (not duplicated) and exact-head green with validation `37957744262` and attribution `37957744577`, then squash merged `46f9a8b86dc00586cfa24a2368e146f234345d2f`. It adds shadow-only bounded local MCP communication benchmarking and fail-closed CLI argument tests. **Does not imply real Bewind OCR speedup**, and does not authorize a faster production transport or close broader Faster #383. Next performance steps require reproducible qualified workload segments and connection/session lifecycle evidence; no live workloads measured here.

## 2026-10-09 — Connector response lineage and tunnel authentication freshness

- #590: local HTTP response trace isolation COMPLETE via PR #608 / `e0250205ee33cd39f5ffc501ff8fa86861679d30`, with exact-head attribution #37956025846 SUCCESS and validation #37956026036 SUCCESS. This covers request-ID isolation, traceparent inheritance and malformed context; external tunnel return association remains **BLOCKED on first failing-edge evidence**, not confirmed healthy.
- #333: tunnel service enabled/active/readiness 200 observed by operator, but no coordinated post-reboot qualification. Preserve the running service.
- #540: stale runtime/tool catalog generation binding remains separately open; do not create a second generation mechanism under #590.
- #599: code inspection confirms control-plane `last_success` accepts any nonempty string regardless of timestamp validity or age. Next code child must derive actual poll cadence/clock source before enforcing an age bound, test invalid/stale/future/fresh and not confuse a past successful poll with current authentication. No active tunnel mutation.
- Sanitized operations playbook PR #607 merged `6dc5160c93815b223214302ffb50cebbb304e49d`; superseded #603 closed unmerged. Privacy: historical Git refs are not erased merely by closing PR.

## 2026-10-09 — Corrected CI runner priority, enrollment integrity

Tracking: #584; source hardening #604/#605 merged and exact-head green, after earlier #600/#601/#602. Documentation #589 merged and current. Runner-MCP PUBLIC standard hosted PR CI is free; migration to isolated self-hosted is **optional**, not a paid-minute emergency.

- CI-0 validated GitHub inventory, registration marker/path and filesystem writable-mode guards: source COMPLETE; no live executor claimed.
- CI-1 local bounded enrollment CLI #388 + independent elevated credential: PR_OPEN / not live. Do not merge or execute ahead of security review.
- CI-2 self-hosted qualification workflow #387: PR_OPEN, real disposable VM/cache/process isolation proof BLOCKED.
- CI-3 selector migration after CI-2 acceptance: NOT STARTED. Maintain required checks and hosted fallback.
- CI-4 monitor actual private Actions artifact/package storage in project-owning issues, not inferred from public hosted minutes: ONGOING cross-project.

## 2026-10-08 — DIAG component topology, data lineage and failure registry

Tracking: #569. Cross-project authority: Blacksp1d3r/AIfordable#485; canonical standard merged through AIfordable PR #486.

Runner-MCP is decomposed into 14 stable diagnostic components covering runtime/self-update, project/source, tests, mailbox/watchers, Fabric bridge, qualification/bootstrap, deploy/migrate/backup, safety/approval/retention, CI runners, service lifecycle, tunnel/connectivity, diagnostics/audit, artifact/mirror custody and the MCP server/client interface.

Each component owns ROADMAP/SOURCES/DATA_LINEAGE/FAILURES. Global maps cover physical store classes, public field/action lineage, implementation paths, test/evidence surfaces and reusable failures. Existing failure-record and safe-diagnostics contracts are reused rather than duplicated.

Troubleshooting rule: identify the public symptom/tool, walk upstream to the earliest divergent source/state/policy/interface edge, and only then repair. Process health, runtime health, peer capability, source authorization and client catalogue freshness remain independent states. Public docs never copy private infrastructure or credential details.

## 2026-10-06 — fixed Fabric worker-qualification provisioning executor in validation

Tracking: #445; orchestration owner: Blacksp1d3r/Runner-Fabric#1130/#1113/#1110.

Runner-MCP now has a bounded local provisioning slice for Fabric-authorized worker qualification. Fabric remains authoritative; Runner-MCP only verifies the request against host-owned private worker authority, exact generation/expiry/fingerprint and the exact managed Runner-Fabric runtime slot, then writes the existing disposable-target qualification config into one fixed owner-only local namespace.

The public MCP tool exposes only semantic worker/capability identity, generation, plan digest, expiry, exact Fabric revision and request fingerprint. No caller-selected shell, argv, path, host/IP, service, endpoint, Incus object, environment map or credential is accepted. Normal workload activation remains false.

After this lands and is live, Fabric #1130 may bind the fixed executor, then #1113 may run the real external-worker qualification. No Bewind OCR or v3 mutation is part of #445.

## Customer/on-prem update readiness counterpart

Tracking: #414. Orchestration/policy owner: Blacksp1d3r/Runner-Fabric#1063. Customer/product semantics: Blacksp1d3r/AIfordable#401.

Runner-MCP may later expose only bounded local primitives required by Fabric: read-only semantic disk/RAM/memory-pressure/swap/OOM/CPU/thermal/storage/power/network/restart/build/schema/recovery readiness; returning-node trust-generation state; exact release staging/activation/rollback only after separate authorization; and bounded failover/failback hooks only for fixed target adapters.

Runner-MCP does not choose customers, cohorts, rollout order, canaries, soak windows or failure cause. Missing/unsupported health remains explicit unknown. Insufficient RAM/storage or unsafe resource pressure blocks before mutation. No arbitrary path, shell, package manager, endpoint, service selector, raw hardware log or customer data is exposed.

## Fleet Update Track A — control-path protection

Canonical umbrella: Blacksp1d3r/Runner-Fabric#924. Reviewed design: Runner-Fabric `roadmap/FLEET_UPDATE_PLANE_BUILD_VS_BORROW.md` v2. Runner-MCP execution issue: #341. Fabric Track A: #937–#943.

Runner-MCP owns the concrete bounded execution and local safety pieces, not fleet orchestration. Near-term order:
1. reproduce the historical stale/incompatible peer failure in automated tests;
2. expose build identity and version-stamped logs;
3. propagate correlation context and support the synthetic end-to-end probe;
4. exchange/enforce protocol range plus interface/tool-schema compatibility;
5. implement CI evidence for N/N-1 first-party skew;
6. emit bounded journal evidence needed by Fabric;
7. reuse the existing staged baseline/self-update recovery machinery while adding support for a separate local commit-confirmed supervisor that can revert after activation without network/Fabric.

Important existing capability: install-time rollback already stages a baseline wheel and can restore it when installation/runtime verification fails. The missing mechanism is post-activation independent recovery: successful updates currently clear the install transaction/artifacts and restart is scheduled by Runner-MCP itself.

Economic constraint until AIfordable has revenue: **incremental software spend is EUR 0**. Use existing code and free/open-source dependencies only. No paid SaaS, commercial update manager, paid Fleet tier, Mender Enterprise or other paid runtime dependency. Hardware, connectivity and electricity are accepted owner costs; software cost remains time only until revenue supports a new explicit decision.

Status update — 2026-10-05:
- Step 1/A1 COMPLETE via #346 / `c37f60dc...`.
- Step 2/A2 ACTIVE. Initial component/version audit stamping #348 / `c73298e6...`; full aligned BuildIdentity fields on every existing audit row #355 / `98bd8ca0...`.
- A2 is not complete until installed provenance, protocol range/interface digest and cross-hop request reconstruction are proven.
- Next Runner-MCP contribution is to expose/propagate the provenance/protocol/interface facts needed by Fabric A2/A4 without broadening remote authority.

# Runner MCP roadmap

This public roadmap is intentionally infrastructure-neutral. Real deployment details belong only in private configuration.


Handoff policy: `roadmap/ROADMAP.md` is the canonical architectural roadmap; `roadmap/DEPENDENCIES.md` is the canonical cross-stream build/integration order when parallel work exists. GitHub live state wins if either document lags.

Status policy: this roadmap is the architectural source of truth for implemented and remaining phases. `handover/CURRENT_STATE.md` is chronological evidence of completed work, while GitHub CI and release records are authoritative for exact validation results such as test counts.

## Maintenance mode — alpha/MVP core complete

Runner MCP's technical alpha/MVP core is complete and the project is in maintenance mode.

Maintenance-mode rules:

- do not add speculative features merely to keep the roadmap moving;
- accept security fixes, correctness bugs, compatibility work and concrete operator needs;
- preserve the small deny-by-default transport/execution boundary rather than growing into a general remote-control platform;
- keep orchestration, scheduling, provider/API behavior, change planning, higher-level autonomy and fleet-scale control in Runner Fabric;
- deferred items in later phases are not launch blockers and should be revisited only when a real use case justifies them;
- discovery/marketing work is non-blocking and must not cause provider-specific runtime, package, auth or hosting changes.

The canonical public alpha release is v0.1.3. Live acceptance covers bounded first-party control, self-update/restart convergence and deliberate interrupted-install recovery. Remaining open issues are external/owner-controlled follow-up rather than core runtime blockers.

## Cross-cutting — end-to-end operational snapshot

Tracking: #269; cross-repo source of orchestration truth: Runner Fabric #867.

A concrete operator-correctness gap was observed on 2026-10-04: the local Runner MCP test queue could correctly report `0 queued / 0 claimed / 0 running` with all test workers available while the first-party client still reported that systems were busy. Therefore local test-queue idleness must never be presented as end-to-end idleness.

Runner MCP will expose one coarse, read-only, bounded `operational_snapshot` over the existing canonical control path:

`client -> control relay -> Agent Bus -> Runner MCP -> Runner Fabric -> worker/work-unit -> durable result -> acknowledgement`.

The snapshot must, where canonical evidence exists, distinguish queued, claimed/inflight, running, waiting-for-result, waiting-for-ack/replay and retrying work; expose oldest-pending and last-activity age; show bounded worker capacity/saturation and primary/fallback/degraded transport state; and return explicit `unknown` / `not_configured` instead of false green when a layer cannot be observed.

Runner MCP must not create a second queue, scheduler or orchestration state store. Runner Fabric remains the owner of orchestration truth; Runner MCP performs only bounded validation/projection. The tool exposes no payloads, prompts, file names, host paths, endpoints, credentials, raw logs, arbitrary queue browsing, shell, process or network authority.

Acceptance requires a synthetic and live-observable case where the local test queue is idle while upstream relay/Agent-Bus/Fabric work is pending to report the system as non-idle and attribute the correct layer; a truly idle path must converge to clear across all observable layers. One coarse snapshot call is preferred over many small status calls.

## Cross-cutting — AI fault containment with proportional security gates

Runner MCP assumes that an AI/client can misunderstand instructions, hallucinate, follow prompt
injection, call the wrong tool, or otherwise request an unsafe action. The model/client is never
the final authority.

The execution boundary must therefore preserve fast autonomous work where mistakes are contained
while applying stronger deterministic checks only as blast radius increases.

### Operating zones

- **Green / contained:** read-only inspection, safe file reads, predefined tests, bounded logs and
  other actions confined to declared project/runtime limits should remain automatic and must not
  require human approval merely because an AI requested them.
- **Controlled:** staging mutation, known managed service/release actions, migrations and equivalent
  bounded operations require deterministic policy, fresh-state validation, exact plan/target
  binding and replay/fencing protection. Human approval is required only where policy says so.
- **Protected:** production mutation, database restore/destructive recovery, credential/security
  policy changes, emergency-stop changes and equivalent high-blast-radius actions require
  independent operator authority and are not enabled merely by client or agent text.

### Security invariants

- AI/client text expresses intent only; deterministic Runner MCP code decides whether a predefined
  capability exists and is authorized.
- Forbidden capabilities must be absent, disabled or technically unreachable, not merely described
  to the model as "do not call this".
- Tools accept bounded semantic identifiers, not arbitrary shell, executable, host path, endpoint,
  environment, service/process or credential input.
- Mutations revalidate current state immediately before execution and remain bound to the exact
  approved plan/target/revision.
- Approval cannot be self-asserted by the requesting AI/client and must be independently derived.
- Repository/document/tool output is untrusted data and cannot grant capability, weaken policy or
  satisfy approval through prompt injection.
- The caller cannot modify the emergency-stop, approval, audit, authentication or policy boundary
  that governs the caller's own action.
- Executors receive the minimum OS/network/credential authority needed for the bounded operation.
- Mutations verify postconditions and preserve recovery/rollback semantics where applicable.
- **Security friction is proportional to blast radius:** safe read/edit/test loops should remain
  fast and automatic; expensive/human gates belong at trust boundaries, not on every development
  step.

This cross-cutting rule strengthens the existing deny-by-default design. It does not add any new
production, shell, credential or restore authority.

## Cross-cutting — optional Runner Fabric coarse work-unit transport

The transport foundation is implemented on `main` via PR #111. Runner MCP may expose exactly three
coarse Runner Fabric tools when private loopback configuration is present:
`fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`.

This integration preserves the product boundary:

- Runner MCP owns MCP authentication/transport, bounded request/response validation, rate limiting,
  existing operator/safety gates and bounded audit;
- Runner Fabric owns orchestration, work-unit policy/state, capability/fencing decisions, change
  plans, validation/repair, commit/push, provider/API-budget behavior, idempotency and recovery;
- the bridge is absent when unconfigured and may not introduce generic shell, Git, GitHub,
  filesystem, provider or arbitrary polling primitives;
- endpoint/token/provider/private-host details remain private and may not escape through tool
  output, audit detail or exceptions;
- transport sessions are isolated per calling thread and response identity/revision/state
  relationships fail closed.

Live activation and end-to-end proof are complete. Issue #110 is closed after a real first-party
client invocation traversed `client -> Runner MCP fabric_run_work_unit -> private Fabric MCP ->
trusted work-unit service`, followed by bounded get/cancel/operator-safety reconciliation. The
former upstream Runner Fabric durability/Agent-Bus qualification gate is also complete. The merged
transport layer must not be rebuilt.

Agent Bus remains the normal runtime-control path, direct GitHub choreography is fallback/bootstrap,
and broad remote-host tools are break-glass only. No plugin/client convenience may add generic shell,
Git/GitHub, filesystem, provider or credential authority.

## Phase 0 — repository and design

Establish repository structure, security baseline, threat model, configuration model, handover notes, dependency policy, and public-repository hygiene controls.

## Phase 1 — minimal MCP server

Implement Streamable HTTP, authentication, health endpoint, project registry, structured audit logging, request identification, basic rate limiting, `list_projects`, and `project_status`.

## Phase 2 — safe file access

Add allow-listed project file reads, metadata, pagination, path traversal protection, symlink escape protection, secret deny-lists, and file-size limits.

## Phase 2.5 — operator safety and rollback policy

Before enabling mutating tools:

- require an external operator emergency-stop mechanism;
- keep future operator actions read-only until retention policy is explicitly confirmed;
- retain code releases using both a minimum count and minimum age;
- retain pre-migration backups separately from code releases;
- treat database point-in-time recovery as a separate retention control;
- allow only one code rollback step per approved action;
- prohibit automatic production database restores;
- require explicit human approval before any database restore;
- require recovery/preflight metadata before migration, deploy, or rollback.

## Phase 3 — controlled test runner

Implemented design:

- predefined test profiles only;
- absolute executable paths and argument arrays with `shell=False`;
- project-relative working directories;
- bounded concurrency, timeout and log size;
- asynchronous jobs with status and paged logs;
- explicit cancellation;
- external operator-stop observation;
- process-group cleanup;
- scrubbed secrets and private paths in logs;
- persisted safe job metadata and interrupted-job recovery;
- restricted environment passthrough;
- short per-job private `TMPDIR` paths for local IPC/socket based test runtimes, with 0700 permissions and terminal cleanup;
- declarative `playwright` test runtime support that injects only a privately configured shared browser cache into the isolated job environment;
- no automatic execution of untrusted public-fork code without stronger sandboxing.

## Phase 3.5 — packaging and onboarding

Make the safe core usable without reading or editing source code:

- `runner-mcp setup` interactive private configuration;
- local/public setup modes with safe local defaults;
- explicit retention confirmation;
- `status`, `doctor` and emergency-stop commands;
- project add/list/remove commands;
- test-profile add/list/remove commands;
- pytest and Ruff profile presets;
- explicit token rotation only;
- non-root `install.sh`;
- user-first README and Quickstart;
- private config permission checks and atomic project-config updates.
- install/runtime preflight must verify the exact Python interpreter, venv support, pip usability/version, packaging backend availability, dependency compatibility and post-install import/bytecode integrity before enabling the installed command; known-bad or incompatible environments fail closed before service activation.
- clean-install validation must cover a minimal Ubuntu-like host where `python3-venv` may be absent and must exercise the real installed CLI after dependency resolution, including detection/recovery guidance for corrupted or incompatible `.pyc`/marshal state.

Service auto-start packaging is implemented with a preferred non-root systemd-user backend plus a managed cron fallback for headless accounts without a usable user bus. Both keep fixed components, explicit watcher bootstrap, duplicate-supervisor protection and foreign-state protection. Privacy-safe guided connectivity is implemented; external tunnel/TLS/reverse-proxy provisioning remains operator-managed. Task 33 reviewed optional graphical administration and keeps it deferred for the first alpha; any later first slice must be a separate loopback-only read-only dashboard over explicitly allow-listed safe summaries, with no new mutation authority.

## Phase 3.6 — community usability and extension path

Make the existing safe core easier to adopt, understand and extend without changing its trust boundaries:

- project-aware runner-mcp guide command with safe next-step suggestions;
- separate operator/service-account wrapper without secret duplication;
- dedicated user-to-developer extension guide;
- contribution rules that preserve deny-by-default behavior;
- configuration-first extension model;
- built-in adapter extension path before core changes;
- documentation must use placeholders and stay free of real infrastructure values;
- onboarding documents must stay synchronized with implemented features.

Still planned:

- optional graphical administration remains post-alpha/deferred after the Task 33 boundary review; revisit only on concrete operator need, starting read-only/local-only;
- framework adapters only when concrete reusable use cases justify them.

Privacy-safe private-tunnel/TLS/reverse-proxy guidance is implemented. Runner MCP deliberately does not provision external tunnel/TLS/DNS/firewall/proxy state itself.

## Phase 3.7 — GitHub mailbox bridge protocol

Formalize the proven GitHub to Runner MCP transport without turning it into a remote shell:

- public, infrastructure-neutral mailbox protocol documentation;
- strict versioned JSON request model;
- fixed allow-list for project inspection and predefined test execution;
- unknown fields, duplicate keys and oversized requests fail closed;
- no client-supplied shell, executable, path, environment, service or arbitrary MCP tool name;
- migration, deployment and rollback execution are available only through their existing approval IDs; restore remains outside the mailbox allow-list;
- watcher implementation stays private until deployment-specific parts are separated from reusable protocol logic.

Current status:

- the private watcher migration is complete through the shared runtime described in Phases 3.8.3–3.8.7;
- deployment-specific credentials and infrastructure details remain private.

## Phase 3.8 — bridge result envelope and replay protection

Harden the GitHub mailbox transport in both directions:

- strict, versioned result envelope;
- bounded result size, nesting, collection count and string length;
- fail-closed unknown fields and duplicate JSON keys;
- conservative redaction of credentials, environment metadata, paths, hosts, URLs, executables, commands and service-unit details;
- safe error codes instead of raw exception/process output;
- canonical SHA-256 request fingerprints;
- local replay ledger that stores no project/profile/path/credential/result content;
- duplicate request IDs never execute twice;
- request-ID reuse with changed content fails closed;
- corrupt, oversized, capacity-exhausted or symlinked replay ledgers fail closed;
- ledger file permissions restricted to the service account.

Current status:

- the shared validator, result envelope and replay lifecycle are integrated into the public watcher runtime and proven through the later 3.8.x phases.

## Phase 3.8.1 — task-completion feedback

Make asynchronous work observable to the operator without expanding execution authority.

Implemented public contract:

- strict terminal completion events: succeeded, failed or cancelled;
- deterministic event IDs derived from a private source identifier, giving transports a stable deduplication key without exposing the source identifier itself;
- fail-closed source/operation binding for test, migration, deployment and rollback job classes;
- test completion requires a predefined profile; unrelated job classes cannot attach one;
- project/profile/event identifiers use safe bounded shapes;
- attention state is derived from terminal status rather than trusted from a sender;
- duplicate JSON keys, unknown fields, non-standard JSON constants and oversized events fail closed;
- completion payloads contain no paths, hosts, URLs, credentials, service names, environment values or raw logs;
- notification delivery is explicitly separate from task execution: delivery retries may never rerun the operational action;
- mailbox permissions and action allow-lists are unchanged.

Implemented notification runtime and private proof:

- an optional private GitHub-issue notifier observes strict persisted terminal test, deployment/rollback and migration jobs without calling any execution path;
- notifier bootstrap deliberately skips historical completions;
- deterministic event IDs are used both in a private 0600 delivery ledger and as remote notification markers;
- existing remote markers are reconciled instead of posted again;
- notification failures remain retryable independently from task execution;
- one fresh predefined test job was proven end to end to produce exactly one user-facing notification, and a repeated notification cycle produced no duplicate;
- the built-in notifier no longer requires a repository-specific self-hosted Actions runner.

Next:

- keep heartbeat/stale-request recovery separate from notification delivery;
- map any future asynchronous Runner MCP job class to the same completion-delivery runtime only when its persisted terminal metadata can be consumed without widening execution authority.

## Phase 3.8.2 — watcher resilience and restart recovery

Make the private mailbox transport observable and restart-safe without widening the mailbox action allow-list.

Implemented public foundation:

- replay ledger lifecycle now distinguishes `claimed` from `completed`;
- legacy replay entries without a lifecycle state are treated conservatively as `claimed`;
- a request is marked completed only after its safe result is durable;
- restart recovery distinguishes processable, already-resulted, ambiguous-claim and missing-result states;
- ambiguous claimed work is never rerun automatically;
- a completed ledger entry with a missing transport result is never rerun automatically;
- sanitized heartbeat states are limited to `healthy`, `backlog` and `degraded`;
- heartbeat output exposes only bounded counts and oldest-pending age, never request contents or infrastructure metadata;
- stale/backlog thresholds are bounded;
- duplicate heartbeat observations fail closed;
- transient transport retry is bounded to timeout/rate-limit/unavailable failures;
- authorization and invalid-response failures are not automatically retried;
- transport retry policy never authorizes operational action replay;
- local operator recovery can resolve an already-claimed missing-result request by publishing a terminal safe `RECOVERY_REQUIRED` result without invoking the executor;
- the recovery command requires an existing exact replay record, refuses an existing durable result, preserves the cursor, and finalizes a claimed ledger entry only after the safe failure result is durable;
- a strictly valid request that has never been claimed can be explicitly abandoned by a local operator, producing an `OPERATOR_ABORTED` result without invoking the executor;
- a malformed historical request can be quarantined only when it is in the current backlog, has no result, every sibling request has a matching durable result, and the request head remains unchanged through final verification;
- malformed-request quarantine fetches only bounded bytes from the fixed mailbox path and does not weaken normal protocol parsing;
- no recovery path exposes a generic replay, ledger-reset or cursor-reset control;
- a normal watcher cycle performs subsequent reconciliation where applicable.

Operational proof covers migrated claim -> execute -> persist -> complete ordering, sanitized heartbeat publication, restart-safe reconciliation and one live malformed legacy-request quarantine with zero replay. Explicit operator recovery paths have regression coverage for persistence failure, protocol validity, exact confirmation and cursor/head races.

Next:

- keep notification delivery and heartbeat/stale recovery independent;
- extend operator recovery only when a new fail-closed state has a provable non-replay resolution; never add a generic replay/reset switch.

## Phase 3.8.3 — transport-neutral bridge processor

Move reusable watcher orchestration into the public package without publishing deployment-specific transport details.

Implemented foundation:

- strict request parsing happens before replay claim or execution;
- replay claim happens before any Runner MCP action;
- duplicate completed requests return without execution;
- duplicate claimed requests become an ambiguous recovery state and are not executed;
- executor interface contains only the six mailbox-allow-listed actions;
- no arbitrary MCP tool name, shell, executable, path, environment or service name is accepted by the processor;
- `run_tests` uses an explicit `run_tests_to_completion(project, suite)` executor method;
- executor exceptions become generic safe failure envelopes without raw exception text;
- unsupported/unsafe executor output becomes a bounded `UNSAFE_RESULT` failure;
- results are scrubbed/serialized before the transport-specific result sink sees them;
- durable result persistence happens before replay lifecycle completion;
- result-persistence failure leaves the request claimed and returns safe recovery material rather than rerunning the task;
- replay-finalization failure after durable persistence is reported as recovery-required rather than triggering execution again.

Still transport-specific/private:

- mailbox repository/branch selection;
- credentials;
- polling/webhook mechanics;
- result-file naming/location;
- notification destination;
- supervisor/service configuration.

Current status:

- the processor is integrated with the hardened GitHub transport and watcher coordinator in Phases 3.8.4–3.8.7; the private pilot migration and end-to-end proof are complete.

## Phase 3.8.4 — hardened GitHub mailbox transport

Provide a reusable GitHub transport without putting deployment-specific credentials or infrastructure details in the public repository.

Implemented foundation:

- fixed GitHub API host; callers cannot supply an arbitrary endpoint;
- repository and branch/ref identifiers are strictly validated;
- request, result and heartbeat locations are fixed below the mailbox root;
- GitHub credentials remain runtime-only and are never serialized into mailbox data;
- API responses are size-bounded;
- duplicate JSON keys and non-standard JSON constants from GitHub fail closed;
- wrapped GitHub base64 content is accepted only after strict validation;
- request payload identity must match its mailbox filename;
- result publication is create-once and idempotent only when existing content is identical;
- conflicting existing result content fails closed;
- result transport failures map into the BridgeProcessor persistence-recovery boundary;
- heartbeat create/update uses bounded validated public heartbeat JSON only;
- HTTP authorization, rate-limit, timeout, conflict and availability failures are classified without returning raw GitHub response content;
- no GitHub SDK or paid external service is required.

Current status:

- the generic coordinator and private-runtime integration are implemented in Phases 3.8.5–3.8.7;
- credentials, repository/ref selection and supervisor configuration remain private.

## Phase 3.8.5 — incremental watcher coordinator

Combine the public GitHub transport, bridge processor, replay lifecycle and heartbeat contract into a restart-safe watcher loop.

Implemented foundation:

- transient GitHub transport retries are bounded to 2 and 5 seconds after the original attempt;
- authorization and invalid-response failures are never automatically retried;
- request discovery uses a strict fast-forward compare from a private local cursor instead of rescanning historical mailbox contents;
- compare input is limited to validated 40-hex commit SHAs;
- request-file deletes, renames, nested paths, malformed IDs and oversized compare sets fail closed;
- first use is explicitly uninitialized and executes nothing;
- explicit bootstrap records the current request head and deliberately skips historical requests;
- local cursor uses restrictive permissions, file locking, symlink refusal and optimistic expected-SHA advancement;
- an existing durable result is reconciled into the replay ledger without executing the action;
- claimed requests without a result are never automatically rerun;
- completed requests with a missing result are never automatically rerun;
- persistence/finalization failures keep the cursor behind so the next cycle reconciles safely;
- malformed requests block cursor advancement instead of being silently skipped;
- heartbeat publication stays independent from operational task success;
- heartbeat delivery failure never rewinds an already-advanced cursor or reruns an action;
- non-request commits can advance the cursor without executing work.

Current status:

- the coordinator is combined with the loopback MCP executor and private runtime in Phases 3.8.6–3.8.7; restart/reconciliation proof is complete;
- completion delivery remains an independent idempotent subsystem.

## Phase 3.8.6 — loopback MCP bridge executor

Move the remaining pilot-specific MCP handshake and test polling into reusable public code without exposing a generic remote-control interface.

Implemented foundation:

- local MCP endpoint is restricted to HTTP(S) loopback hosts and the exact `/mcp` path;
- credentials in endpoint URLs, query strings and fragments are rejected;
- bearer token, session ID and test job ID shapes are bounded and validated;
- MCP response bytes are bounded;
- JSON and SSE payloads reject duplicate keys, non-standard constants, malformed UTF-8 and ambiguous multi-event responses;
- transport, JSON-RPC and tool failures become generic `BridgeExecutionAdapterError` values without raw server details;
- the public executor exposes exactly the six bridge operations;
- generic MCP tool dispatch stays private and internally allow-listed;
- internal `test_status` polling is used only to finish a previously allow-listed `run_tests` request;
- test logs are never fetched by the bridge executor;
- terminal test output is reduced to project, suite and status;
- polling interval and overall wait time are bounded.

Current status:

- private-config watcher migration and restart/reconciliation proof are complete in Phase 3.8.7;
- clean-environment demo validation and completion notification proof are also complete; remaining connectivity/onboarding work is tracked separately.

## Phase 3.8.7 — private-config watcher runtime and CLI

Wire the public GitHub transport, replay ledger, cursor, watcher and loopback MCP executor together without putting deployment-specific values into the repository.

Implemented foundation:

- GitHub repository, request ref, result ref and token live only in the private 0600 runtime environment;
- mailbox configuration is validated before atomic persistence;
- mailbox status reveals only configured/not-configured state;
- the GitHub token is entered through a hidden prompt and is not accepted as a CLI argument;
- mailbox removal deletes only the four mailbox environment values;
- setup overwrite preserves database and mailbox secrets even when rotating the Runner MCP bearer token;
- replay ledger and cursor files are derived inside the private configuration directory;
- `github-watcher bootstrap` explicitly starts at the current request head and skips historical requests;
- `github-watcher once` processes one bounded incremental cycle and prints only safe counts/state;
- `github-watcher run` provides continuous polling with bounded intervals;
- request polling and heartbeat publication have separate cadences;
- heartbeat defaults to a slower cadence and is also published on watcher-state transitions;
- heartbeat delivery remains independent from operational task execution.

Private deployment proof:

- the pilot poller has been replaced by the shared `runner-mcp github-watcher run` runtime in a private deployment;
- explicit bootstrap started at the current request head without historical replay;
- fresh protocol-v1 inspection requests, queue/worker observability and asynchronous test execution were proven end to end;
- restart/reconciliation preserved the cursor and replay ledger without duplicate execution;
- the legacy pilot poller is disabled in that deployment;
- completion-notification transport remains a separate capacity concern.

Current status:

- the independent exactly-once completion-notification proof and clean-environment demo validation are complete;
- remaining private-connectivity/TLS onboarding stays in the onboarding/launch phases.

## Phase 3.8.8 — controlled multi-project concurrency

Remove global serialization from routine bridge and test work without widening execution authority.

Implemented foundation:

- bounded mailbox request workers with a separate maximum in-flight batch;
- request acceptance separated from long-running test execution;
- persistent logical queues per project with fair round-robin scheduling;
- bounded global test-worker capacity and bounded global/per-project queue capacity;
- conservative defaults: two test workers globally and one active test per project;
- explicit per-project `max_parallel_tests` plus per-profile `parallel_safe` opt-in;
- queued, claimed and running lifecycle states before terminal test results;
- safe queue/worker/job observability and queued/running cancellation;
- malformed or recovery-required mailbox requests do not block independent work in the same batch, while cursor advancement remains fail-closed;
- GitHub result writes keep only a short serialized critical section;
- loopback MCP clients are thread-local so concurrent watcher workers do not share mutable MCP session state;
- existing shell, path, environment, service-name and arbitrary-tool injection boundaries remain unchanged;
- migration, deployment, rollback and restore remain outside the mailbox allow-list;
- authenticated MCP request capacity defaults to a bounded 600 requests/minute so status polling and mailbox concurrency do not become a new global bottleneck;
- request rate, test-worker capacity and queue capacity remain separate independently enforced controls.

Capacity can later grow by increasing bounded worker settings or adding execution capacity behind the same request/job protocol. Protocol clients do not need to change.

See `docs/CONCURRENCY.md` for defaults, scheduling, observability and Runner MCP versus GitHub Actions guidance.

## Phase 3.8.9 — bounded operational bridge

Extend the GitHub mailbox from inspection/tests into existing Runner MCP operational capabilities without introducing a generic remote shell or bypassing local safety controls.

Implemented foundation:

- bounded scrubbed test-log pages through `job_log`;
- configured service alias listing/status/start/stop/restart, never arbitrary systemd unit names;
- backup listing and on-demand configured PostgreSQL backups;
- read-only migration status, deployment plans, release lists and rollback plans;
- approval-plan request/status through opaque IDs;
- migration/deployment/rollback execution only with an already-approved short-lived approval ID;
- deployment and rollback job status through validated opaque job IDs;
- per-action strict argument schemas, bounded list/log ranges and fixed loopback MCP tool mapping;
- database restore, PITR, production actions, shell/argv/path/env injection and approval granting remain outside the mailbox authority.

This phase is specifically intended to remove routine dependence on general-purpose remote-control software. GitHub remains a transport; Runner MCP remains the local authorization and execution boundary.

Next:

- prove the expanded operational bridge live against one read-only operation and one low-risk configured mutation on the upgraded private runtime;
- preserve separate human approval for migration/deploy/rollback.

Runner MCP read-only observability and commit-pinned self-operations are implemented separately in Phases 3.8.10–3.8.11 rather than exposing package-manager or process-control primitives.

## Phase 3.8.9a — shared Playwright test runtime

Make browser-based E2E profiles work inside Runner MCP's isolated test environment without weakening HOME/TMPDIR isolation.

Implemented foundation:

- test profiles can declare a fixed runtime of `default` or `playwright`;
- the Playwright runtime receives only `PLAYWRIGHT_BROWSERS_PATH`, sourced from private Runner MCP configuration;
- the configured browser-cache path must be absolute, exist as a directory and not itself be a symlink;
- the browser-cache path is treated as a private path for log scrubbing;
- missing browser runtime fails closed before test execution;
- no arbitrary browser path can be supplied through the mailbox or test request.

This is intended for shared Chromium/Playwright installations on persistent self-hosted runners while preserving per-job HOME/TMPDIR isolation.

## Phase 3.8.10 — runtime observability bridge

Expose Runner MCP's own health/configuration state through fixed, read-only bridge actions so routine diagnosis no longer needs general-purpose remote access.

Implemented foundation:

- `runtime_status` returns package version, safety mode, emergency-stop state, bounded worker/queue capacities and whether test/database/deployment/approval subsystems are configured;
- `runtime_doctor` returns only bounded PASS/WARN/FAIL-style checks and generic details;
- no private paths, URLs, hostnames, credentials, service units, environment values or raw process output are returned;
- both actions are fixed no-argument protocol-v1 actions and map only to local MCP tools;
- result publication still uses the existing bridge scrubber, replay ledger and create-once result lifecycle.

Next:

- prove the runtime observability actions live after the private runtime is upgraded.

Mutating self-operations remain separate from read-only diagnosis and are implemented as commit-pinned operations in Phase 3.8.11.

## Phase 3.8.11 — commit-pinned Runner MCP self-update

Remove routine dependence on general-purpose remote-control software without introducing generic package or process control.

Implemented foundation:

- `self_update(commit)` accepts only one full lowercase 40-character commit ID for the configured canonical Runner MCP repository;
- the target commit must be reachable from `origin/main`, and source synchronization remains clean-worktree, exact-commit and staging/test gated;
- existing fixed `lint` and `unit` profiles must both pass before installation;
- validated update source is staged as a private wheel before installation; wheel building and installation use the active Python runtime with fixed offline/no-dependency pip arguments, no shell and no caller-supplied path/argv/environment;
- when a previously installed commit is known, its clean source is staged as a private recovery wheel before source synchronization, while the per-project source guard remains held across recovery staging, target sync, lint/unit validation, target staging and installation;
- a private 0600 install-transaction marker is durable before the in-place package mutation; runtime status exposes only a bounded `install_recovery_pending` boolean and overlapping self-updates fail closed while it exists;
- target package installation is verified in a fresh Python process before it is accepted;
- a caught target install/import failure automatically reinstalls and verifies the recovery wheel and restores the exact prior source commit when both package and source rollback can be proven; successful automatic recovery is reported as `install_rolled_back` without scheduling activation;
- a first/bootstrap install failure, process interruption during package mutation, failed rollback, or unfinalized transaction remains `install_recovery_required` and blocks further self-update instead of pretending the environment is intact;
- a persisted rollback-capable install transaction can be recovered only through the local `runner-mcp self-update-recovery` operator command; it requires the emergency stop to be active, reuses only the privately staged baseline wheel, restores the exact baseline commit from `origin/main`, re-verifies the installed runtime and clears the transaction only after package/source/state recovery is proven;
- the local recovery path refuses first/bootstrap transactions without a known baseline and refuses to overlap pending activation recovery; no recovery action is exposed through the mailbox or MCP tool surface;
- local `status` exposes only `clear`, `REQUIRED` or `INVALID` install-recovery state, while `doctor` warns on a valid pending transaction and fails on corrupt/unsafe transaction state without exposing commits or artifact paths;
- same-commit requests still verify the exact commit against `origin/main`, but then complete without package mutation or restart;
- the build backend required by the deliberate `--no-build-isolation` wheel path is an explicit runtime dependency rather than an implicit build-environment assumption;
- update jobs and installed-commit state are persisted privately with restrictive permissions;
- server, GitHub watcher and completion watcher activate new code through fixed component-specific self-reexec flows;
- activation creates fixed create-once restart markers for all three components; a failed component re-exec restores its marker instead of silently consuming the restart request;
- runtime status exposes only whether activation remains pending and the bounded number of fixed pending components; another self-update is blocked until those markers are cleared;
- server activation uses bounded retries, while watcher/notifier failures preserve their marker so existing systemd/cron supervision can safely retry on restart;
- `self_update_status(job_id)` exposes only bounded persisted state;
- read-only `runtime_status` keeps the broader observability fields and adds self-update readiness/state; `runtime_doctor` remains separate;
- the loopback bridge explicitly allow-lists `runtime_status`, `runtime_doctor`, `self_update` and `self_update_status`;
- protocol validation treats `self_update_status` as an exact job-id-only action, and direct/self-update entry points reject uppercase or abbreviated commit identifiers;
- arbitrary repository/ref selection, package-manager arguments, install paths, process commands, service identifiers and restart commands remain unavailable.

Next live-proof lane (tracked by #108):

- bootstrap the current recovery-capable baseline once on the private Runner MCP host through the normal dependency-resolving path;
- prove same-commit/no-op and one forward commit-pinned self-update through the bounded operating model;
- deliberately fail/retry one activation and fault-inject one package-install interruption only after the recovery-capable baseline is confirmed, proving that durable recovery state blocks overlap and can be cleared only by the existing bounded/local recovery path;
- keep dependency-set changes explicit because self-update intentionally never resolves or installs dependencies; a dependency-set change still requires an explicit compatible bootstrap path;
- do not describe in-place pip mutation as atomic: the transaction marker makes interruption detectable and fail-closed, while automatic rollback is claimed only for caught failures where both package and source restoration are verified;
- publish only scrubbed categorical evidence and public commit/workflow references; no private host identity, paths, services or credentials.

## Phase 3.9 — public launch readiness

Prepare Runner MCP for free, responsible discovery without changing its security boundaries.

Implemented launch-readiness foundation:

- Runner MCP remains the product identity under the AIfordable umbrella;
- README leads with the problem, safety boundary and architecture;
- Quickstart remains the full guided path while a separate five-minute local demo provides a shorter evaluation path;
- root security-reporting policy added;
- public changelog and release checklist added;
- reusable factual launch copy prepared for GitHub and developer communities;
- privacy-safe GitHub bug/feature forms and a security-focused pull-request template added;
- package metadata improved for future distribution;
- discovery metrics remain platform-level; no application marketing telemetry is added;
- no paid advertising, paid hosted CI or paid hosted infrastructure is a hidden dependency; standard free CI for this public repository is acceptable when it carries no private secrets.
- clean Ubuntu 24.04 / Python 3.12 CI now exercises the documented five-minute demo end to end, including installation, setup, doctor, predefined test-profile configuration, emergency stop and loopback health check;

Canonical publication completed:

- PyPI package `aifordable-runner-mcp==0.1.3` is published;
- official MCP Registry identity `io.github.Blacksp1d3r/runner-mcp` version `0.1.3` is published;
- GitHub pre-release `v0.1.3` is aligned with exact release commit `0aa013c279128e22fbd53be32c35bced3ae26834` and carries wheel + sdist assets;
- protected publish workflow run `36962568072` completed PyPI, official Registry and GitHub pre-release publication successfully;
- public GitHub description/topics and first-party canonical discovery links are live;
- mcp.so community submission is complete;
- secondary directories must reuse the canonical identity/install/auth metadata rather than inventing alternatives.

Remaining discovery work is intentionally non-blocking:

- Glama listing discovery, maintainer claim and metadata verification are complete; Glama hosting/release/Gateway remain intentionally unused;
- Smithery is deliberately skipped unless it exposes a repository-only path that preserves the canonical self-hosted architecture unchanged;
- AllMCPs listing ownership is verified through the free README path; no paid boost/featured placement is justified;
- stale third-party directory metadata is tracked separately in #263 and must not trigger package/runtime changes;
- one technical launch post remains deliberately deferred until `aifordable.com` is ready enough to serve as the public umbrella/landing page.

## Phase 4 — staging service management

Implemented core design:

- private service aliases mapped to systemd-user units;
- no arbitrary unit names supplied by MCP clients;
- safe alias listing without unit/health-URL disclosure;
- status and optional HTTP health checks;
- independent opt-in for start, stop and restart;
- all mutating actions pass the operator safety guard;
- emergency stop leaves status available but blocks service mutations;
- subprocess execution uses a fixed systemctl argument array with `shell=False`;
- no sudo or generic system-service control.

Task 41 provides the shared bounded text-redaction primitive. Task 47 is now integrated as a local/private `service-log` reader with explicit per-service `allow_log_read` opt-in, fixed bounded `journalctl` tailing and no MCP/mailbox/Agent-Bus log action. Any remote disclosure remains separately deferred to Task 51 review.

## Phase 5 — backups and migrations

Implemented core design:

- PostgreSQL-only database configuration with private `RUNNER_MCP_DB_*` credentials;
- DSN entered through hidden CLI prompt and kept out of project YAML;
- private backup root/project directories and 0600 dump/metadata files;
- `pg_dump` custom-format backups with DSN in child environment, never argv;
- safe backup metadata listing without dump paths or contents;
- predefined migration status/apply profiles with `shell=False`;
- bounded and scrubbed migration output;
- pre-migration backup required before migration apply;
- safety guard rechecked after backup and before migration;
- failed migration keeps the recovery point and never auto-restores;
- Task 44 adds the strict private durable migration-job substrate and `MIGRATION_JOB` completion source; Task 49 is now integrated as an additive `start_migration_job` / `migration_job_status` contract with distinct `migration_async` human approval while preserving synchronous `apply_migrations` and deployment-triggered migrations;
- local read-only restore preflight validates one private PostgreSQL archive without database connection or restore authority;
- local CLI retention preview strictly validates private release/backup state and reports protected or potentially eligible records without deleting or rewriting data;
- CLI database and migration configuration without manual YAML editing.

Not implemented yet:

- database restore execution remains deferred after Task 37: the current architecture does not prove a separately prepared empty recovery target, complete database-writer quiescence, application cutover, `pre_restore` retention semantics or semantic post-restore verification;
- WAL archiving/PITR orchestration and verification;
- automatic/unattended retention pruning;
- backup pruning remains deferred pending a separate crash-safe pair-deletion contract;
- local one-release pruning is implemented by Task 43 after Task 48 added the shared cross-process release lock: local CLI only, one freshly eligible non-migration orphan per short-lived plan, typed confirmation, durable quarantine transaction and fd-safe deletion; backups and automatic pruning remain deferred.

## Phase 6 — staging release engine

Implemented core design:

- staging-only deployment configuration;
- clean Git HEAD as the only deploy source;
- no client-supplied branch/ref/commit or arbitrary build shell;
- fixed Git argv with hooks/fsmonitor disabled;
- safe Git archive extraction with repository symlinks rejected;
- private release root, releases directory and runtime HOME;
- required test profiles before release creation;
- source HEAD/cleanliness rechecked after tests and before migrations;
- optional Phase 5 migration orchestration;
- atomic `current` symlink activation;
- configured service restart plus mandatory health check;
- one automatic code rollback after failed activation only when no migration was applied;
- no automatic rollback after database migration;
- persisted asynchronous deployment jobs and restart-interruption handling;
- MCP `plan_deploy`, `deploy_staging`, and `deployment_status`;
- CLI deployment configuration without manual YAML editing.

Still deferred:

- production deployment;
- framework-specific build/adapters;
- release pruning;
- manual historical rollback selection (Phase 7).

## Phase 7 — rollback engine

Implemented core design:

- safe release metadata listing with current/previous/commit/timestamp state;
- retention-protection reporting using both minimum count and minimum age;
- local advisory retention preview protects current/direct rollback/reference/migration-recovery relationships and never treats manual backups as automatically eligible;
- fail-closed release metadata validation and permission checks;
- direct previous release is the only rollback target;
- global strict MCP input validation rejects unknown arguments;
- rollback blocked when current release crossed a database migration boundary;
- asynchronous persisted rollback jobs;
- deploy and rollback jobs mutually exclude each other per project;
- atomic one-step release switch plus service restart and health verification;
- failed rollback health reactivates the original current release when safe;
- no database restore and no automatic multi-step cascade.

Still deferred:

- automatic release pruning remains deferred; Task 43 implements only one local/manual non-migration orphan release outside the retained rollback chain per confirmed plan;
- arbitrary historical target selection remains deferred after the Task 35 boundary review; older history is reached only through fresh direct-previous one-step approvals with health revalidation;
- production rollback;
- database restore/recovery workflow.

## Phase 8 — multi-project adapters

Implemented core design after Tasks 38–39:

- built-in `generic` and `python` adapters are deny-by-default and expose only bounded capability metadata;
- execution layers are project-generic after configuration is resolved;
- no dynamic adapter/plugin loading from project configuration is allowed;
- built-in non-custom test/migration presets are materialized through typed fixed adapter recipes rather than framework-specific branches in generic configuration code;
- Python-specific project-local executable discovery and fixed pytest/Ruff/Alembic argv construction live behind the Python adapter boundary;
- `custom` remains the explicit local-operator path with existing executable validation and no shell command string;
- unknown or ambiguous built-in presets fail closed.

New projects should normally require configuration/adapters rather than core changes. Additional framework adapters remain separate reviewed additions rather than dynamic plugins.

## Phase 9 — approval and risk gates

Implemented:

- short-lived persisted approval plans for migration, deploy and rollback;
- approval request/status available through MCP, but approval itself only through local CLI;
- explicit local confirmation phrase;
- approval bound to action, project and cryptographic plan fingerprint;
- single-use consumption and replay prevention;
- default ten-minute TTL with strict 60–1800 second bounds;
- deployment approval pinned to clean Git commit;
- migration approval requires and binds a clean Git HEAD;
- rollback approval pinned to current and direct previous release;
- runtime race checks reject changed deploy/rollback targets;
- mutating project actions restricted to `staging`;
- production remains read-only.

Connectivity decision:

- prefer OpenAI Secure MCP Tunnel for private ChatGPT/OpenAI connectivity where supported;
- keep Runner MCP private/loopback and use outbound HTTPS rather than opening inbound firewall ports;
- a hosted multi-user relay comparable to commercial remote MCP services is optional future infrastructure, not part of the MVP.

## Phase 10 — optional restricted command templates

Only if concrete use cases remain unmet, add tightly allow-listed executable templates under a sandboxed account. No free-form root shell.

## MVP completion

The MVP is complete when one pilot project can be inspected, tested, backed up, migrated, deployed to staging, health-checked, and rolled back without a general remote-shell dependency, while all actions remain auditable and secrets stay inaccessible.


## Cross-project Infrastructure Authority invariant

Runner-MCP consumes the canonical AIfordable Infrastructure + Credential Authority and does not own a separate fleet/server truth. Bounded operations must resolve scoped customer/site/host/runtime/service identity/credential binding and freshness before infrastructure mutation. Stable asset IDs are technical identity; env-var names and Linux usernames are implementation bindings, not host identity. Unknown, stale or conflicting context fails closed.

Authority: `Blacksp1d3r/AIfordable/docs/INFRASTRUCTURE_AUTHORITY.md`.
