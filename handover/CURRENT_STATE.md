## 2026-10-09 — Faster-13 eventfd shadow + Windows host contract

#460 (shadow-only shared-memory/eventfd benchmark) exact-head attribution `37974721744` and full validation `37974721750` GREEN; squash merged `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`. Added 5s response deadline and guaranteed worker cleanup on failure with positive and negative tests. Not a production transport or OCR throughput improvement.

#490 (host-platform capability contract) exact-head attribution `37975249864` and validation `37975249793` GREEN; squash merged `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. Platform family `supported` is not Windows backend readiness: explicit `serviceAdapterImplemented` false for Windows, true for Linux implementation, false unsupported. Runtime Windows SCM not installed or qualified.

#619 implements a narrow further fail-closed guard on default service-manager backend selection for non-Linux. Latest head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution `37975695602` GREEN, full validation `37975695551` IN_PROGRESS. No merge until exact-head green. Linux normal/injected test backends remain unchanged. Subsequent Windows SCM implementation requires separate least-privilege, isolated Windows CI and deployment approval. #489 remains broader owner.

#590 external tunnel return-path identity remains OPEN; #599 source freshness guard already closed. No live host/tunnel changes.

## 2026-10-09 — Final landing: #456 fully GREEN and MERGED

Supersedes earlier #456 WAITING_CI: PR #456 exact head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262` SUCCESS (Ruff/pytest, release artifact, clean demo), squash merge `fc034b094c633b51889e2a13cc86727e2b1941fe`. Together with exact-green merges #465 `365a7a1f32f82e01da75004b800ed2948516fa9e`, #467 `4bba36e877d96246c93eb8064d6bf0d4af72de05` and #613 `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`, all four code PRs are integrated; no live server, CI selector, tunnel, credential or production transport mutation. New next-safe CI-aware action in following session: reconcile existing stacked PR #460 against merged #456 and newest main (do NOT duplicate PR), inspect CI and rebase only using exact branch name. #458 is a temporary hosted benchmark lab and explicitly DO NOT MERGE. #590 external connector response delivery still OPEN despite local JSON-RPC ID guard; remote health dispatcher/response-delivery snapshots remain unproven. #599 source-level auth freshness is closed. No OCR throughput claims from synthetic measurements.

## 2026-10-09 — Faster-13 shadow merges #467 and #465; #456 awaiting clean demo

Exact-head attribution and full validation SUCCESS: existing PR #467 Unix-envelope E2E head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, attribution `37962618491`, validation `37962618480`, squash merge `4bba36e877d96246c93eb8064d6bf0d4af72de05`; existing PR #465 compact-envelope head `9d1344beaef929acc9bac236a6c8d692dd48b988`, attribution `37962706609`, validation `37962706712`, squash merge `365a7a1f32f82e01da75004b800ed2948516fa9e`. #456 same-Linux-host Unix IPC head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262`: Ruff/pytest and built artifact SUCCESS, clean demo IN_PROGRESS at last check, state `WAITING_CI`. #460 is STACKED on #456 and must not merge first. #458 hosted synthetic lab DO NOT MERGE. These are measurements only: no actual OCR speedup, live worker load, runtime transport change, service or tunnel mutation. Prior #467 GraphQL diagnostic retracted: incorrect branch name caused failure; exact branch solved it. #590 external connector still OPEN despite #613 local bridge reply-ID hardening.

## 2026-10-09 — Local MCP reply-ID guard merged; three Faster shadow PRs in validation

PR #613 exact head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97` passed attribution `37962077429` and full validation `37962077446`, merged `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`; internal JSON/SSE replies without exact numeric JSON-RPC id are rejected. Externally intermittent connector/route issue #590 remains OPEN. Issue #599 source freshness was already merged via #609 and closed on reconciliation. Official upstream tunnel-client diagnostics define loopback-only dispatcher and response-delivery counters, documented in triage.

Existing shadow-only Faster PRs (no deployment) restacked to main, original PRs preserved: #467 head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, CI `37962618480`; #465 head `9d1344beaef929acc9bac236a6c8d692dd48b988`, CI `37962706712`; #456 head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, CI `37962833262`. Attribution green for all; Ruff/pytest green for all, full demo pending at last check. `WAITING_CI`, no merge claim. #460 remains stacked behind #456; #458 temporary benchmark lab is DO NOT MERGE. No live service, worker, CI selector, tunnel, credentials or customer data touched.

## 2026-10-09 — Faster-13 synthetic benchmark integrated

PR #514 exact head `1f329ff57e1ef5b8262f813b4a72100aa410820a` passed attribution `37957744577` and full validation `37957744262`, then squash merged `46f9a8b86dc00586cfa24a2368e146f234345d2f`. Includes existing bounded shadow benchmark and seven CLI input rejection tests. No real OCR acceleration claim, local runtime/deploy or workload change. #383 broader Faster-13 remains open. The earlier WAITING_CI note below is superseded. Connector response tracing PR #608 and sanitized playbook PR #607 also merged; #590 external return-path still unqualified.

## 2026-10-09 — MCP connector response identity and Faster-13 benchmark

**Completed:** PR #607 sanitized operator playbook fully green merged `6dc5160c93815b223214302ffb50cebbb304e49d`. PR #608 existing HTTP middleware trace/request-ID negative and concurrent tests fully green merged `e0250205ee33cd39f5ffc501ff8fa86861679d30`. Tests prove local response identity, not external tunnel return path. User/operator observed enabled/active tunnel, readiness 200, zero service restarts; boot drill pending. #590 remains open for live first failing response edge, #540 generation fencing open, #333 reboot readiness open; no live reconfiguration.

**Active:** Existing Faster-13 #514 was cleanly restacked in-place onto current main, with seven fail-closed CLI argument tests. Latest head `1f329ff57e1ef5b8262f813b4a72100aa410820a`; exact-head attribution `37957744577` SUCCESS, Runner MCP validation `37957744262` Ruff/pytest and built artifact SUCCESS, clean demo IN_PROGRESS at last check; `WAITING_CI` overall. Earlier Ruff formatting failure `37957558080` repaired; no production benchmark was run. #383 remains open; no OCR throughput claim or production transport switch.

## 2026-10-08 — Diagnostic topology adoption in review

Tracking: #569.

A documentation-only diagnostic architecture is being added under `docs/diagnostics/` following the merged AIfordable cross-project standard. It maps 14 Runner-MCP components, their sources, state lineage, physical store classes, public tool/result lineage, tests and reusable failures. It does not change runtime behavior, MCP schemas, private configuration, services or the active Fleet/Bewind work.

Reusable failures already indexed include local-idle versus end-to-end-busy, source authorization independent of runtime health, healthy Fabric process versus missing peer capability, and stale client tool-catalogue state.

## 2026-10-08 — Bewind OCR source custody + scalable artifact cache merged; client refresh remains

Runner-MCP #541 / PR #542 merged as `9b0560d3b07bbd7cca548ce72d790ea5fe3f50bd`: workload-neutral private content-addressed worker artifact custody keyed by exact SHA-256 + size, with owner-only atomic storage, cache hit/miss semantics and fail-closed re-verification. No generic MCP/file-transfer/path/URL authority was added.

Runner-MCP #538 / PR #543 merged as `3af622efa95c694946814a7bc33b54e7870bff7f`: zero-argument canonical Bewind OCR source provisioner. It fetches only the fixed public eJustice sentinel `2026/02/03_1.pdf`, pins HTTPS authority, verifies exact SHA-256 `80a0fc4a561f26527aa7fb6dcc89209310f5af73a96e4e030f213faf76defa46` and size `2811759`, publishes it into content-addressed local custody, and writes a private file-backed source binding consumed by the existing staging tool. Exact cache hits avoid redownload. Normal/multi-host activation remains disabled.

Exact-head #538 validation was fully green before merge: attribution, compile, Ruff, 2323+ pytest suite, MCP Registry metadata, whitespace, built release artifact and clean demo.

Live self-update job `f1c924bb4680409caf2012da4970f6ce` completed to exact `3af622efa95c694946814a7bc33b54e7870bff7f`. Runtime status proves installed/source/active runtime revision aligned and no install recovery pending. One restart marker remains pending in the currently connected MCP process/session; the current ChatGPT tool catalog was loaded before the new zero-argument `bewind_ocr_qualification_source_provision` tool existed and does not expose it yet.

Scalability follow-up is Runner-Fabric #1249 (child of #986): content-addressed artifact publish/worker-cache replication with authorization manifests, one-publish/many-reference, backpressure, resumable replication, retention/leases and corruption refetch. #538 is the first consumer, not a Bewind-only transfer architecture.

Next exact action after connector/tool-catalog refresh:
1. confirm `bewind_ocr_qualification_source_provision`, `bewind_ocr_qualification_stage` and `bewind_ocr_qualification_run` are visible;
2. call source provision exactly once and require ready + canonical SHA/size + bindingReady=true + normalActivationEnabled=false;
3. call stage exactly once and require ready + same SHA/size + singleUse=true;
4. call run exactly once;
5. validate the bounded result through Bewind #101 and compare hashes/timing/CPU/load against the canonical route;
6. keep production/multi-host activation disabled until Runner-Fabric #1110 qualification is accepted.

## 2026-10-08 — Bewind OCR qualification staging + execution live; client schema refresh next

Runner-MCP #529 / PR #532 merged as `7f53f92a721dbc6ab9493030bb264e0bab50a277`: fixed zero-argument content-addressed staging for the canonical Bewind German OCR sentinel. Runner-MCP #528 / PR #533 merged as `b6a50eedad8b7448f73e3d13dc9c8be08c1a0668`: fixed zero-argument one-shot Bewind OCR qualification execution using the canonical `pre1997-ocrmypdf-sidecar-0.2.0` contract with exact `nld+fra+deu`, bounded hash/timing/load/failure evidence, final disposable-target destruction and staged-input cleanup. Both keep normal activation false and do not touch active Bewind v3.

Exact-head #528 validation is fully green: attribution, compile, Ruff, pytest, MCP Registry metadata, whitespace, built release artifact and clean demo. Initial CI had only five Ruff authoring diagnostics (three SIM102 cleanup conditions and two overly broad test exception catches); these were corrected on the same branch and are not treated as a reusable operational Failure Museum class.

Live Runner-MCP self-update job `5e8b7494552a436792f3f44ca236399d` completed successfully to exact `b6a50eedad8b7448f73e3d13dc9c8be08c1a0668`. Runtime status then proved installed/source/active runtime revisions all exactly aligned with no restart or install-recovery pending.

Immediately after update, the Fabric loopback bridge was unavailable. The fixed zero-argument `fabric_worker_qualification_policy_configure` restored the trusted Bewind worker policy (generation 1, policy valid, source target ready, normal activation false), after which bounded `fabric_agent_restart` returned restarted/pid_changed/healthy. Final live proof:
- Fabric bridge preflight: ready;
- Fabric source revision: `3bd24f96844341e418618ea44adcbd625cc7bb60`;
- worker: `aifordable-lab`;
- capability: `bewind-ocr-qualification-v1`;
- generation: 1;
- capabilityAllowed/policyValid/activationReady: true;
- normalActivationEnabled: false;
- Runner-MCP doctor: 0 failed checks.

Current blocker is client schema only: this already-open ChatGPT runner-mcp-control tool catalog was loaded before #528/#529 became live, so `bewind_ocr_qualification_stage` and `bewind_ocr_qualification_run` are not callable in this session. Do not use shell/Desktop Commander as a bypass.

Next exact action in a fresh first-party client/chat after connector tool refresh:
1. confirm both new zero-argument tools are visible;
2. call `bewind_ocr_qualification_stage` exactly once;
3. require ready state, canonical source id `2026/02/03_1.pdf`, content hash/size evidence, singleUse=true and normalActivationEnabled=false;
4. call `bewind_ocr_qualification_run` exactly once;
5. require `state=qualified`, exact `nld+fra+deu`, pipeline `pre1997-ocrmypdf-sidecar-0.2.0`, German sentinel verified, page/output hashes, cleanupReceipt.targetDestroyed=true, cleanupReceipt.stagedInputRemoved=true, normalActivationEnabled=false;
6. return bounded result to Runner-Fabric #1114/#1110 for canonical-route equivalence comparison before any multi-host/production activation.

## 2026-10-06 — Cross-project authority binding

Runner-MCP is bound to the AIfordable Infrastructure + Credential Authority. Do not maintain a separate full server/token map here. Resolve scoped current context before infrastructure mutation or credential repair; unknown/stale/conflicting context fails closed.

## 2026-10-06 — Mandatory topology preflight

Before connection or infrastructure troubleshooting, consult the canonical AIfordable infrastructure authority at `Blacksp1d3r/AIfordable/docs/INFRASTRUCTURE_AUTHORITY.md` and Runner Fabric's topology directory. Confirm the actual host, runtime and service identity before changing configuration. Unknown or conflicting topology fails closed. Historical correction: `github-runner` was the first Runner-MCP host; `aifordable-lab` was the first Runner-MCP + Runner Fabric combination.

## 2026-10-06 — #451 dedicated Bewind source credential in validation

Tracking: #451; unblocks Runner-Fabric #1112/#1110.

Runner-MCP #445 is merged via #452 as `1d4957ff0787e91378dc1a46215469623fc76947` and live on aifordable-lab with restart/recovery clear.

#451 adds one fixed private credential selector for the built-in `bewind` project. When `RUNNER_MCP_BEWIND_GITHUB_TOKEN` is present, only Bewind known-project preflight/source-preflight/prepare may use it. Other projects and mailbox remain on the existing global token. Missing dedicated credential explicitly preserves current global fallback; malformed dedicated credential fails closed. MCP callers still provide only project_id and no credential value is returned/audited.

Next: exact-head CI/merge/live update. Then the owner stores the already-created fine-grained Bewind read token in the dedicated private env binding; run bounded preflight -> prepare -> register to close Fabric #1112 without touching v3.

## 2026-10-06 — #445 fixed worker-qualification provisioner in validation

Tracking: #445; Fabric chain #1130 -> #1113 -> #1110. Active branch: `fabric/445-worker-qualification-provision-v2`.

Implemented:
- fixed MCP tool `fabric_worker_qualification_provision`;
- exact accepted capability `bewind-ocr-qualification-v1`;
- request fingerprint recomputed locally from worker/capability/generation/plan digest/expiry/Fabric revision;
- local private worker identity/capability/generation authority;
- active managed Runner-Fabric launcher must resolve inside the exact requested control-plane update slot;
- owner-only fixed qualification config is written under Runner-MCP private config and persisted into `runner-mcp.env`;
- the same in-memory private environment is shared with existing `fabric_disposable_target_qualify`, so provision -> qualify needs no runtime restart;
- sanitized result proves managed launcher + qualification state ready and keeps normal activation false;
- no OCR execution and no active Bewind v3 interaction.

Original PR #449 was restacked once because concurrent A6 work advanced main; v2 is based on current main `10df2c8b...`.

Next: exact-head CI/review/merge. Then update the live Runner-MCP runtime, configure only the host-owned private qualification template, execute Fabric #1130 bounded binding and continue #1113.

## 2026-10-06 — Known projects can materialize from trusted local source

Tracking: #401.

Runner-MCP can now consume an optional host-owned private known-project local-source map before falling back to GitHub. The MCP caller still supplies only project_id.

The local binding is schema-bound to:
- fixed catalog project identity;
- expected canonical repository identity;
- private owner-only local source directory;
- exact expected commit revision.

When present and valid, preparation clones locally with network disabled, checks out the exact revision, verifies a clean HEAD, normalizes the resulting origin to the canonical GitHub repository identity, atomically renames the temporary checkout into the existing trusted sibling destination and cleans partial state on failure.

Invalid or unsafe configured local authority fails closed rather than silently falling back to GitHub. Without a local binding, the prior GitHub preparation path is unchanged. The private binding is retained across config overwrite.

Live branch qualification included lint + unit PASS and a real bare local Git source materialization test.

## 2026-10-06 — Local Fabric update custody is self-staging

Tracking: #442, follows local-custody update source #404.

Runner-MCP now has a bounded exact-commit staging path for Runner Fabric control-plane update bundles. The caller supplies only the full commit revision. Runner-MCP owns the canonical Runner Fabric repository, fixed builder, private temporary checkout and existing local-bundles custody root.

The staging path:
- clones/fetches only the canonical Runner Fabric source using the existing private GitHub credential;
- verifies exact clean HEAD before build;
- invokes only scripts/build_control_plane_update_bundle.py;
- reuses FabricUpdateManager local bundle and bootstrap integrity validation;
- atomically publishes only a fully validated bundle to local custody;
- is idempotent for an already-valid exact bundle;
- cleans temporary source/credential state on failure;
- exposes no repository/path/token/argv authority to the caller.

This closes the gap between provider-neutral bundle creation and the existing fabric_local_update_readiness/fabric_local_update route.

## 2026-10-06 — F34 bounded mirror activation

Tracking: #431. Depends on Runner Fabric #1121 for one-time delegation of the fixed 8TB namespace.

Runner-MCP now has a zero-argument activation path that, after the fixed storage namespace is writable by the managed service identity:
- verifies the fixed inventory/mirror roots are private and writable;
- writes the canonical 11-repository desired-state snapshot into owner-only Runner-MCP private config;
- binds the existing GitHub credential into an owner-only Git configuration without exposing it in output/audit;
- persists the four F34 private runtime bindings atomically into runner-mcp.env;
- updates the same in-memory mirror environment used by readiness/preflight, so activate -> preflight works without an extra restart;
- never runs mirror reconcile/network work as part of activation.

Reconcile remains separately gated on repository-mirrors-preflight READY.

## 2026-10-06 — A6 now blocked by stale Fabric runtime plus private Runner-Fabric authorization

The ChatGPT runner-mcp-control schema now exposes both A6 qualification proxies. Runner-MCP #427/#428 also restored bounded recovery of the fixed qualification-only Fabric Agent MCP after genuine process loss; the live restart returned `state=restarted`, `pid_changed=true`, `healthy=true`.

A full Runner-MCP restart on `55fa3d1ba46d6d6bb41b2e43d3d94e97376cf309` ruled out cached downstream MCP session state. Fabric bridge calls still fail, including A6 prepare and older read-only Fabric operations.

Bounded source evidence for built-in `runner-fabric`:
- credential_configured=true;
- source_reachable=false;
- main_ref_available=false;
- reason_code=source-unreachable-or-unauthorized;
- runtime doctor still reports Runner-Fabric Actions read unavailable/unauthorized.

The managed Fabric slot is older than A6 (#1046/#1049). Local-custody readiness was checked for current Fabric main `7af6cbf887a214f70354726c99abe9d19712b32f`, A6 baseline `5b5e71ad9ed66a9f7cec35ddb48eb7535edf3d99`, prior managed-update baseline `a8cb6835d33269bfb96ea3d8e40bc505f91b107b`, and older live-qualified `a7492aeb2bc738a4de4d19d6e515d29b1482a1a0`; none is locally staged.

Do not create an untrusted bundle ingress, another updater, or a shell/Desktop Commander bypass. Immediate unblock is either least-privilege Runner-Fabric repository/Actions read for the existing private Runner-MCP credential or a separately trusted pre-staged local-custody bundle. After Fabric is updated to an A6-capable exact revision, resume only `prepare -> self_update -> fresh A3 probe -> finalize`.

## 2026-10-06 — Fleet A6 blocked only on client schema; access warning split to #417

Fresh reconciliation confirms the active runner-mcp-control catalog still lacks the two existing A6 qualification proxies. Live Runner-MCP remains operational on the previously qualified installed commit with no pending restart or install recovery. Do not rebuild the proxy or updater.

Runner-MCP #417 separately tracks the private Runner-Fabric source/Actions read warning. This is not A6 implementation work and must not weaken the fixed-repository, fixed-workflow, fail-closed update boundary.

## 2026-10-06 — customer update readiness counterpart planned

Tracking: #414; Runner Fabric #1063; AIfordable #401.

Runner-MCP is execution-only for the new customer-update safety lane. Planned first scope is read-only semantic readiness for disk capacity/margins, RAM/available memory/memory pressure/swap/OOM, CPU/thermal/storage/power/network/restart/build/schema/recovery and returning-node trust generation. No live customer mutation or fleet policy is activated.

## 2026-10-06 — A6 qualification proxy merged and live

Runner-MCP main/live: `e88e76badad428995c026cf5ac9988607fd52069`.

PR #411 added exactly two strict Runner-MCP -> Fabric A6 qualification proxies:
- `fabric_a6_update_qualification_prepare(candidate_commit)`
- `fabric_a6_update_qualification_finalize(correlation_id, job_id)`

Exact-head validation #1138 and attribution #655 were green before merge. Live self-update job `3d3339dcad1d44838eb99825286eca8a` completed successfully; runtime_status confirms exact installed commit, operational mode, no restart pending and no recovery pending.

The remaining blocker is ChatGPT connector schema refresh: this current session still exposes the older runner-mcp-control tool catalog and therefore cannot invoke the two newly added proxy tools even though the server runtime has them.

Do not add another proxy/updater. After tool schema refresh, execute the existing A6 prepare -> self_update -> finalize path and hand evidence back to Fabric #942.

## 2026-10-05 — Tunnel readiness proven through control-plane authentication; end-to-end gate remains

Canonical Runner-MCP main: 9a4f9d7a2916625617aa2ef144fc40679e549129.

Issue #333 remains open. Completed and green: #370 managed tunnel autostart, #371 managed process evidence, #372 fixed local MCP health evidence, and #373 fixed local control-plane successful-poll evidence.

Current bounded progression: COMPLETE config -> managed process active -> local MCP proven -> control-plane authenticated -> end_to_end_not_routable. Do not claim READY from config, process, local MCP health, or successful control-plane polling alone.

Upstream tunnel-client review confirms each process sends an opaque X-Tunnel-Client-Instance-Id, but the local runtime has no authoritative inventory of every other active instance using the same tunnel ID. Tunnel service uses a shared queue per tunnel; redundant clients are safe only for equivalent/stateless or session-aware shared backends. Runner-MCP targets localhost per host, so keep one active tunnel client per tunnel ID unless topology proves equivalent shared-backend behavior.

Remaining #333 gate: do not invent local uniqueness evidence or a second probe engine. Wait for Fabric A3/#939's existing qualification/synthetic-work-unit path to expose continuous durable end-to-end evidence. Consume only a bounded first-party result if/when available, and require topology/duplicate-runtime reconciliation before end_to_end_routable=true / READY.

No live autostart, tunnel restart, deployment, migration or runtime update was performed in these slices.
## 2026-10-05 — Tunnel readiness runtime boundary merged; managed autostart next

Canonical Runner-MCP main: `2a27fb0d8236e6c06f2fd0da3b04dfced558d471`.

Issue #333 remains open. Completed this session:
- #364 / `4aae2a21...`: maps secret-free tunnel restart-config evidence into the bounded readiness state machine;
- #366 / `69b958aa...`: complete private config no longer makes `doctor` claim PASS; without separate process evidence it stays WARN / `process_not_running`;
- #367 / `7e157688...`: local read-only `tunnel-status` exposes only restart_config/state/reason;
- #368 / `2a27fb0d...`: hidden fixed `tunnel-run` executes only installed `tunnel-client run` against Runner-MCP loopback, explicitly exports the existing private tunnel ID/runtime key, requests an ephemeral loopback health listener and writes the resolved health URL to the fixed private config path.
- #363 also merged in parallel as `7b2782f2...` for A3 bound traceparent propagation; the transient duplicate restack #365 was closed after reconciliation.

Security boundary:
- no generic process scan, shell, arbitrary executable, arbitrary endpoint/argv, credential output or paid dependency was added;
- tunnel-client profile management is not reimplemented; current upstream supports env-backed tunnel ID/runtime key, a fixed MCP server URL and private health URL-file evidence;
- no live runtime update, deployment, migration or tunnel restart was performed in this session.

Next safe #333 slice:
1. admit `tunnel` as one fixed optional Runner-MCP autostart component for systemd-user and managed-cron only when `inspect_tunnel_restart_config(...) == COMPLETE`;
2. invoke only the existing hidden `tunnel-run --port <bounded-port>` path;
3. expose managed active/inactive evidence through existing autostart status, then feed that bounded process evidence into tunnel readiness;
4. only after process evidence is proven, consume the fixed private tunnel health URL for local `readyz` evidence; control-plane authenticated and end-to-end routable remain separate later evidence;
5. keep duplicate-tunnel/fencing protection explicit before any READY/routable claim.

Runner-Fabric A3/#939 is active in parallel; do not duplicate its Fabric-side trace/result/ACK/failure-taxonomy work.

## 2026-10-05 — Fleet Update A2 Runner-MCP audit identity hardening merged

Canonical Runner-MCP main: `98bd8ca0de5ecdb2c16b70bbe3ff620b882e432c`.

A1 remains complete via #346 / `c37f60dc...`.

A2 progress:
- #348 / `c73298e6...` added component/version stamping and runtime-start to the existing durable audit log.
- #355 / `98bd8ca0...` replaced the partial shape with the full bounded BuildIdentity field set on every audit row: component_id, build_version, source_revision, artifact_digest, protocol_min/max and interface_schema_digest.
- Existing request_id/tool/project/actor/result/timestamp evidence remains intact; unproven provenance/protocol/interface fields remain explicit null.
- exact-head #355 validation: Runner MCP validation #1033 success; attribution #543 success; Ruff/pytest, release artifact and clean demo all green.

Do not claim #938 complete from Runner-MCP alone. Remaining cross-repo work belongs primarily in Fabric: request/connection stamping across first-party hops plus trustworthy installed provenance/protocol/interface evidence. Runner-MCP may need a later bounded slice to expose those facts, but must not invent checkout-derived provenance.

## 2026-10-05 — Fleet Update A2 Runner-MCP build identity merged

PR #348 merged as `c73298e601081bc85d7f850583356b9c1ee741b4`. Runner-MCP now reuses its existing durable audit log to stamp every record with `component_id=runner-mcp` and the installed package version, and emits a safe runtime-start event. No new logging service/dependency was introduced. Fabric #938 remains open because Agent Bus/Fabric and other first-party hops still need equivalent identity evidence with backward-compatible persisted schemas.

## 2026-10-05 — Fleet Update A1 characterization merged

PR #346 merged as `c37f60dc6001be5f269f88506a92934bc09bf7cb`. The integration regression reproduces the observed stale-client tool-catalog failure class: MCP protocol negotiation remains green while the cached peer lacks a newly available Fabric tool, so the failure layer is `interface_schema`, not transport/protocol. No production code or runtime authority changed. Track A may proceed to A2 only after post-merge validation remains green.

## 2026-10-05 — Fleet Update Track A added; A1 first

Runner-Fabric v2 review narrows Runner-MCP work to concrete control-path protection. #341 is the execution counterpart; Fabric #937–#943 define Track A. First implementation is the historical incompatibility reproduction only; no production mutation.

Code inspection confirms existing self-update already has baseline-wheel/install-time recovery but not an independent post-activation commit-confirmed supervisor. Reuse the installer; do not build another updater.

Zero-cost rule: no paid software dependencies before project revenue.

## 2026-10-04 — bounded Fabric operational snapshot proxy merged

PR #286 merged as `e6330820a2ee58a2ec5068830c2d9a1267f2297b` after Runner MCP validation and attribution were green. Runner MCP now allow-lists Fabric's zero-argument `operational_snapshot` and exposes `fabric_operational_snapshot`, validating exact schema, pending-count relationships, capacity/age bounds, read-only flags and private-detail restrictions. Runner MCP does not reconstruct relay/Fabric truth. Fabric #876 is merged as `98baf4e2532e591d534ba893a147773aa31f644f`; live usefulness still depends on Fabric providing an explicit canonical provider. Keep #269 open until provider wiring and live proof show upstream pending work while local test workers are idle.

## 2026-10-04 — operational snapshot proxy implementation in validation

Issue #269 is now implemented as a strict Runner-Fabric projection rather than a local reconstruction. PR #286 head `d43e472bb265a7314e59bb3109bcdddbab650e18` adds zero-argument `fabric_operational_snapshot`, allow-lists only Fabric's fixed `operational_snapshot` call, validates exact `runner.fabric/operational-snapshot/v1` fields/count relationships/capacity bounds/ages/read-only flags and reuses private-detail rejection. This preserves Fabric as orchestration truth. Commit attribution is green; Runner MCP validation is in progress. Dependency: Runner-Fabric #876 must first land the optional Agent-MCP source contract. Do not merge #286 before both sides are terminal green.

## 2026-10-04 — operational snapshot gap promoted to maintenance priority

Live operator evidence showed `queue_status` and `worker_status` at 0 queued / 0 claimed / 0 running with both test workers available while first-party client sessions still reported systems as busy. Restart state later converged clear, so local test-queue idleness is not sufficient end-to-end evidence. Issue #269 now tracks one bounded read-only `operational_snapshot`; Runner Fabric #867 owns the canonical cross-layer projection. Required attribution spans control relay, Agent Bus, Runner MCP, Fabric/Conductor/work-unit, worker capacity, durable result/outbox/replay and ACK state. Unknown/unobservable layers must remain unknown rather than false green. This is a correctness/operator need allowed under maintenance mode, not speculative feature growth.

## 2026-10-04 — alpha core complete; maintenance mode

Runner MCP is now in maintenance mode after completion of the technical alpha/MVP core and live recovery acceptance.

Current live evidence:
- runtime is operational with emergency stop inactive;
- self-update is ready, with no active update, restart marker or install-recovery transaction;
- #108 recovery qualification is complete: interrupted install state was detected, overlap failed closed, local emergency-stop-gated recovery restored the exact prior baseline, and a normal bounded self-update returned the runtime to exact main;
- first-party bounded Runner Fabric work-unit control is proven; Runner Fabric remains the orchestration/control-plane owner;
- canonical public release is v0.1.3 on PyPI, the official MCP Registry and GitHub Releases;
- Glama and AllMCPs discovery/ownership are established without introducing hosted runtime dependencies;
- #101 remains open only for a deliberately deferred technical launch post after `aifordable.com` is ready;
- #263 remains open only for third-party directory metadata corrections, including upstream MCP Find issue #26.

Maintenance policy:
- no speculative Runner MCP feature work;
- accept security fixes, correctness bugs, compatibility fixes and concrete operational needs;
- preserve the deny-by-default bounded authority model and local-only recovery boundaries;
- keep broad orchestration, scheduling, provider logic and higher-level automation in Runner Fabric;
- external discovery/marketing work is non-blocking and must not drive runtime/package changes.

## 2026-10-04 — local self-update recovery qualification harness live-ready

Canonical Runner MCP runtime/code checkpoint before the live recovery drill: `ba35f70eb9e3e489fc6936d2bc2f0fc425710c81`.

Completed:
- #110 is closed after first-party coarse Fabric run/get plus fail-closed cancel/operator-safety acceptance;
- issue #261 / PR #262 add a local-only `self-update-recovery-qualify <commit>` path for #108;
- the qualifier uses normal exact-main validation/staging/install, then deterministically interrupts after target wheel installation and before verification/finalization, preserving the existing recovery transaction and staged baseline;
- the qualification path is not exposed through MCP, mailbox or Agent Bus and adds no generic command/path/package/process authority;
- exact-head #262 validation, release artifact, clean demo and attribution are green;
- managed Runner MCP self-update to `ba35f70e...` completed and restart convergence is clear;
- Fabric runtime update remains idle; do not confuse Runner MCP #260 automatic-bundle acceptance with an active Fabric update.

Next:
1. use the next exact current-main documentation commit as the forward target for the live #108 drill;
2. locally run `self-update-recovery-qualify <exact-current-main>` under the qualified service-user runtime;
3. prove remote/normal self-update refuses overlap while recovery is pending;
4. locally activate the operator emergency stop and run `self-update-recovery` with its exact confirmation;
5. verify baseline restoration, clear recovery state and then perform a normal bounded self-update back to exact current main;
6. close #108 only after that live evidence is recorded.

## 2026-10-04 — exact-main self-update guard is live

Canonical Runner MCP live code checkpoint: `82e4b0f133bae3a709bb29a89a9be2d98122aef9`.

Completed:
- PR #258 / issue #257 now require normal self-update to target the exact fetched `origin/main` tip; a stale normal target fails closed instead of becoming an implicit downgrade;
- recovery keeps its dedicated older-baseline path and no generic ref/branch selector was introduced;
- the six affected recovery/install test doubles were adapted to the new main-tip sync path; exact-head and post-merge validation, release artifact, attribution and clean demo are green;
- live self-update to `82e4b0f1...` completed through Runner MCP itself; after controlled restart: `self_update_ready=true`, `restart_pending=false`, `pending_restart_count=0`, `install_recovery_pending=false`;
- issue #246 is closed after live proof that configured restart consumers converge without orphan optional markers;
- current already-open client session still exposes the older cached MCP tool catalog, so newly landed `fabric_update` / `fabric_host_inspect` schemas require a fresh first-party client session; do not bypass this with broad remote shell/Desktop Commander.

Next:
1. open a fresh first-party client session and verify the newly landed Runner MCP Fabric tools are visible;
2. re-reconcile Runner Fabric current `main` at that moment and choose only the exact current commit with a successful canonical `control-plane-update-bundle` artifact; do not reuse a formerly-current Fabric SHA merely because it was recorded in an older handoff;
3. perform the first bounded managed Fabric update through `fabric_update`, prove status and rollback readiness, then use `fabric_host_inspect` / coarse work-units for routine control;
4. keep #110 as the remaining first-party work-unit proof and #108 as the separate deliberate recovery/fault-injection proof.

## 2026-10-04 — managed Fabric update path landed and Runner MCP live runtime converged

Canonical Runner MCP main/live commit: `cb7804bf0dbd10e9e343520aefb7b5df0f45ccc4`.

Completed:
- PR #252 / issue #250 fixed stale optional self-update restart markers with explicit bounded reconciliation and fail-closed optional-component configuration;
- PR #255 / issue #253 bound server self-update restart to the actual local loopback serve host/port instead of inferring restart authority from the public/tunnel resource URL;
- live self-update to `cb7804bf...` completed through Runner MCP itself;
- server and configured GitHub-watcher restart markers both self-consumed; live status is `self_update_ready=true`, `restart_pending=false`, `pending_restart_count=0`, and no install recovery is pending;
- PR #256 / issue #251 added bounded managed Runner Fabric exact-commit update/status/rollback tools;
- Fabric updates accept only a full lowercase commit, require a successful canonical `control-plane-update-bundle` workflow from `main`, verify exact manifest/commit/file-set/SHA256 integrity before execution, strip GitHub authorization before artifact redirects, reject local/private redirect hosts, require an already-managed Fabric slot launcher, and invoke only fixed `BOOTSTRAP.py preflight|apply|rollback` actions;
- rollback is bound to the currently active managed commit only; no repository, URL, path, command, environment, package, artifact ID or executable authority is caller-supplied.

Next:
1. make sure the desired Runner Fabric `main` commit has a canonical control-plane update artifact without reintroducing a manual operator dependency;
2. start a fresh first-party client session so newly added MCP tool schemas reload;
3. use `fabric_update` for the first exact managed Fabric upgrade and prove bounded status/rollback readiness;
4. then use the already-landed `fabric_host_inspect`/work-unit route to continue retiring Desktop Commander from routine work.

## 2026-10-04 — bounded Runner Fabric host inspection bridge

Tracking: #247. Cross-repo dependency: Runner Fabric #760 / I5 #751.

Runner MCP now proxies one new fixed zero-argument Runner Fabric capability:
- `fabric_host_inspect()` -> loopback Fabric `host_inspect`;
- strict bridge allow-list now includes exactly `host_inspect` beside the existing work-unit tools;
- result must be `runner.fabric/host-inspection/v1` with `mutation_enabled=false`;
- top-level, host and browser shapes are validated fail-closed;
- nested output is size/node bounded and rejects keys that could expose paths, credentials, endpoints, argv, command or executable authority;
- the public plugin takes no arguments, so callers cannot select a path, command, executable, service, URL or environment;
- audit records only `fabric_host_inspect`, semantic `host:local` and outcome;
- Fabric work-unit behavior and authority are unchanged.

Next:
1. exact-head Runner MCP validation;
2. merge after Runner Fabric #760 is green/merged;
3. self-update the managed Runner MCP runtime;
4. update the managed Runner Fabric runtime;
5. prove `fabric_host_inspect` through the existing remote connector and use that proof instead of Desktop Commander for browser/runtime readiness.

## 2026-10-03 — First-party client path replaces routine broad remote control

Canonical code base before this slice: `1196630299387d2f254629941790ee9b9cd70dca`.

Current direction:
- the canonical `aifordable-runner` service-user Agent Bus restart/replay acceptance is complete;
- Runner Fabric #479 is closed; GitHub-denied bounded work-unit execution, durable replay/fencing and convergence evidence no longer block the Runner MCP bridge;
- Agent Bus is the primary runtime control path; GitHub mailbox/direct GitHub choreography are fallback/bootstrap paths;
- broad remote-host tooling such as Desktop Commander is break-glass only and must not be the normal development path;
- Runner MCP already exposes exactly three configured coarse Fabric tools: `fabric_run_work_unit`, `fabric_get_work_unit`, and `fabric_cancel_work_unit`; do not add another bridge or a generic remote shell.

Issue #240 / PR #241 add the missing first-party client packaging layer:
- local ChatGPT/Codex plugin packages reuse the existing Runner MCP MCP server;
- registered-app mode stores only a validated technical app identifier;
- HTTP/self-hosted mode stores only a validated MCP URL plus bearer-token environment-variable name, never the token value;
- generated packages are private by default and contain a bounded skill that directs agents to coarse Fabric work-units and treats broad host tooling as break-glass.

Remaining #110 acceptance is now narrow: prove one real first-party client invocation through
`client -> Runner MCP fabric_run_work_unit -> private Fabric MCP -> work-unit service`, then record bounded get/cancel/operator-safety evidence and the coarse-call reduction. No new execution authority is justified.

Next:
1. land #241 only after exact-head attribution and full Runner MCP validation are green;
2. connect/register the private Runner MCP MCP server in an eligible first-party ChatGPT/Codex environment without weakening local-first/private connectivity;
3. start a fresh client session so plugin tools reload, run one bounded Fabric work-unit, and reconcile #110;
4. resume #108 recovery proof on the now-qualified replacement host after the first-party control path is usable.

## 2026-10-03 — Canonical service-user Agent Bus restart/replay acceptance completed

The dedicated `aifordable-runner` runtime on `runner:aifordable-lab` has now completed the live bounded Agent Bus acceptance that remained open in #125.

Evidence:
- Runner Fabric was activated through its managed slot/update path at exact qualification revision `a7492aeb2bc738a4de4d19d6e515d29b1482a1a0`;
- q591 executed through the AIfordable SQL relay while GitHub fallback was unavailable;
- the successful terminal relay acknowledgement was deliberately dropped only by the qualification-only Fabric path after durable commit;
- Runner MCP convergence observed `state=pending pending_results=1`;
- the ordinary Agent Bus worker was restarted;
- after restart the durable result replayed before new claims and convergence returned `state=clear pending_results=0`;
- the relay still returned q591 as the same completed/ok/reported terminal result;
- reused q591 identity with changed content failed closed and did not alter the original terminal record;
- prior live evidence already covers relay restart durability, stale-generation fencing, read-only GitHub-denied status/doctor and primary/fallback state.

Do not repeat:
- the old watcher-marker activation proof;
- stale-generation fault injection;
- relay-restart proof;
- manual outbox/relay-store edits;
- credential reconstruction.

Runner MCP itself required no new runtime authority for this proof; the existing wrapper/private-env boundary and convergence surface were sufficient.

Next:
1. reconcile/close #125 from the accumulated acceptance evidence;
2. keep Agent Bus as primary runtime control and GitHub mailbox as fallback/bootstrap only;
3. proceed with managed persistent worker lifecycle and higher-level Fabric live overview/operations rather than adding generic remote-shell authority.

## 2026-10-03 — Self-update succeeded; watcher restart activation is the only immediate Runner MCP gate

Live replacement-host facts supplied from the completed bounded self-update:
- installed runtime-code commit is `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`;
- successful self-update job: `c6602347fe0646ffa9e20a0f638a2967`;
- runtime status is operational; emergency stop inactive; install recovery clear;
- doctor reports 0 failures / 0 warnings;
- Agent Bus convergence is `clear` with 0 pending results;
- `last_installed_commit` is the exact target and `install_recovery_pending=false`;
- only restart activation remains: `restart_pending=true`, `pending_restart_count=2`;
- exact remaining markers are `github-watcher=9dc9d2bf...` and `completion-watcher=9dc9d2bf...`; server marker is already clear.

Source-supported restart path was re-verified on current main:
- long-running GitHub watcher calls `run_restart_if_requested(config_dir, "github-watcher", ...)` after each cycle;
- long-running completion watcher calls the same bounded helper for `completion-watcher` after each notification cycle;
- the helper validates the marker, removes it, and re-execs the fixed Runner MCP component; if re-exec fails it restores the exact marker instead of silently consuming it;
- therefore do not manually delete restart marker files and do not repeat the completed self-update proof.

Immediate live sequence:
1. start/resume the dedicated service-user `github-watcher run` and `completion-watcher run` paths long enough for each to reach its normal restart check;
2. verify only that `restart_pending=false` and `pending_restart_count=0`;
3. proceed directly to Runner Fabric #590 isolated Agent Bus qualification with GitHub/source-control credentials absent and fixed GitHub HTTPS probes denied;
4. prove one real worker restart, durable result replay without duplicate execution, and convergence back to clear;
5. only then qualify the separate GitHub fallback identity/pool, independent drain/disable, and persistent activation.

Current external limitation of this coordination session: the replacement host is not reachable from the available remote-management device, so no live marker mutation/restart was attempted from an untrusted or guessed path.

## 2026-10-03 — Replacement-host Runner MCP live qualification checkpoint

Canonical runtime-code self-update target: `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` (reachable from `origin/main`; later documentation-only handover commits need not move this target).
Installed/source rollback baseline on `aifordable-lab`: `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`.

Live facts proven on the dedicated `aifordable-runner` service user:
- `runner-mcp 0.1.3`; doctor previously reported 0 failures / 0 warnings.
- Local MCP server starts cleanly on `127.0.0.1:8000`; `/healthz` returns `{"status":"ok"}`.
- Direct MCP bridge `runtime_status` succeeds and reports `self_update_ready=true`, no active update, no restart pending and no install recovery pending.
- Bounded local `lint` and `unit` profiles both pass through the MCP bridge.
- GitHub mailbox -> watcher -> local MCP bridge -> bounded test runner is proven end-to-end by request `lint-55f906d7faec4d15`, job `dc43ca86f38244588b09ced284b70e34`, terminal `passed`, exit code 0.
- Self-update request `self-update-b3864011660143cb` was accepted end-to-end and created job `48a3cb362da249f0925b5cee18fdfe86` for exact target `fa2bedc3d9e9f8181fe2c27043a6d75c3dfe81fe`.
- That self-update job reached the target checkout, passed target `lint`, then failed target `unit` collection with exit code 2. v0.1.3 automatically restored the source checkout to baseline afterward, so a baseline HEAD after failure did not mean sync had never occurred.
- Runtime packaging preflight is healthy: pip is available and `setuptools.build_meta` imports successfully.
- A manual no-install/no-sync wheel build of the baseline project succeeds. Therefore do not re-investigate missing pytest/ruff, mailbox transport, MCP endpoint/auth, baseline registration, pip availability or build backend availability unless new evidence contradicts these facts.
- The MCP server is not yet installed as persistent autostart; for qualification it must currently stay alive in a foreground terminal.

Resolved root cause and correction:
- target lint job `bf7e0872202a4b4d91d15e3f9762e4df` passed;
- target unit job `eb64112264214b5cb88291ac4a04e540` failed during collection because pytest imported the previously installed baseline package from `.venv/site-packages` instead of the newly checked-out `src/` tree;
- PR #233 fixed validation with `pythonpath = ["src"]` in pytest configuration so self-update tests the active checkout;
- #233 merged to `main` as `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` after commit-attribution, Runner MCP validation, Clean Ubuntu installer proof, Ruff/pytest, demo smoke and release-artifact validation were green;
- current live host source remains safely restored to baseline `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`; next runtime-code target is `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.

Do not regress:
- Agent Bus remains the intended primary runtime control path; GitHub mailbox is qualification/fallback, not long-term authority.
- Do not install persistent autostart until the bounded live qualification path is understood and green.
- Do not manually replace the installed package or move the source checkout to the target to bypass self-update safety.
- Keep rollback baseline `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d` intact until the failed self-update is diagnosed.

## 2026-10-02 — Agent Bus live proof + replacement-host reconciliation

Canonical Runner MCP main at this checkpoint:
`c2ef4a348a126867f07777b162d913efa3a97edd`.

Important correction to older handoff sections below:
- live `runtime_status` and `runtime_doctor` over the AIfordable Agent Bus have completed successfully;
- one real bounded Runner Fabric work-unit completed over Agent Bus on `runner:aifordable-lab`;
- the work-unit reached terminal execution before a real HTTP 413 blocked completion delivery; the result remained durable in the local outbox and replayed successfully after the scoped AIfordable/nginx 64 KiB relay-body fix without work-unit re-execution;
- relay restart durability and stale-generation fencing are already proven;
- Runner Fabric repository tests prove a restarted worker/coordinator replays a pending terminal result after lost acknowledgement while executor call count remains exactly one, then converges the outbox to empty.

Runner MCP state now landed:
- #226 fixed runtime-smoke behavior for the service-user virtualenv symlink layout.
- #227 -> `70609a216e5b279a7a191a83f78eb0f876a15ae0`: deterministic dedicated service-user qualification guidance; do not weaken private home/config permissions or qualify an operator-account substitute.
- #229 -> `c2ef4a348a126867f07777b162d913efa3a97edd`: read-only `runner-mcp agent-bus convergence` status. It exposes only `not_initialized|clear|pending|invalid` plus pending-result count and performs no acknowledgement/deletion/mutation.
- Live service-user verification after the runtime-smoke fix reported doctor 0 failures / 0 warnings and autostart preflight ready.

Runner Fabric dependency now landed:
- Fabric #590 -> `98ea725a965ce4fbc94474df63738b2be296e3b0`: `agent-bus-qualify-isolated-work-unit`.
- The qualifier proves GitHub/source-control credential environment absent and fixed GitHub HTTPS probes blocked before using relay configuration, then submits only the synthetic qualification work-unit contract.
- It exposes no generic project/work-item/change-plan/provider/path/command authority and does not activate production Agent MCP.

Remaining #110/#125/#198-adjacent work is live-host specific:
1. regain local reachability to the `aifordable-lab` VM;
2. run `runner-mcp status`, `runner-mcp doctor`, `runner-mcp agent-bus status`, and `runner-mcp agent-bus convergence` in the dedicated service-user runtime;
3. require convergence to become `clear` before/after the next proof;
4. run Fabric #590's bounded work-unit while GitHub credentials are absent and GitHub network access is explicitly blocked;
5. perform one real Agent Bus worker-process restart/replay confirmation;
6. only after the Agent Bus primary path is green, register/qualify the separate GitHub runner fallback identity/pool and prove it can be disabled independently;
7. persistent activation remains gated until these proofs complete.

Do not regress:
- Agent Bus is primary runtime control; GitHub is fallback/CI/source integration only.
- Do not reconstruct a control credential on the runner.
- Do not inspect/delete private outbox files to manufacture convergence.
- Do not replace the qualification-only Agent MCP with production `agent-serve`.
- Do not add another Runner MCP bridge/recovery path for behavior already owned and proven by Runner Fabric.

Immediate resume:
1. use the AIfordable AF-22.6 live runbook/checkpoint;
2. resume at host reachability and service-user runtime checks;
3. use `runner-mcp agent-bus convergence` instead of manual private-state inspection;
4. complete the live isolated work-unit + worker restart proof;
5. only then proceed to fallback registration/drain/persistent activation.

## 2026-10-02 — Live update paths proven; remaining gates narrowed

- Current reviewed Runner MCP main checkpoint: `61da54c38b150ac1c04bd4b78da47833cf72260c`.
- Runner MCP was updated on the controlled host through the existing bounded mailbox `self_update` action to exact main `61da54c…`. The job completed successfully and the installed runtime now reports 0.1.3 with install recovery clear.
- Re-submitting the exact same commit completed as a safe no-op with `restart_required=false`; this closes that live acceptance item in #108.
- The new local `autostart preflight` is available and fails closed as `runtime_smoke_failed`. Persistent autostart/Agent-Bus activation remains blocked by #198; no force/repair/reinstall loop was used.
- The remaining destructive #108 activation/package-interruption recovery drill is deliberately deferred to a stable replacement host so product recovery evidence is not mixed with the known unstable hardware/runtime substrate.
- Runner Fabric was updated through its reviewed exact-wheel side-by-side slot path to exact Fabric main `a8cb6835d33269bfb96ea3d8e40bc505f91b107b`. Live apply, explicit rollback to the prior runtime and re-apply all succeeded while `runner-fabric doctor` remained foundation OK with mutation capabilities disabled.
- The live Fabric CLI now exposes `agent-serve-qualification`, and the existing private Runner MCP Agent Bus config was migrated with the fixed loopback Agent-MCP bridge binding without exposing/replacing the relay credential.
- Fabric #545/#549 are complete. The old “live Fabric runtime too old” blocker is gone.
- #110/#125/Fabric #479 are now blocked only on a legitimate authenticated AIfordable Control Center submission of the fixed synthetic `fabric_run_work_unit`, followed by one-shot replay/fencing proof. Do not write relay queue/storage directly and do not reconstruct a control credential on the runner.
- No additional prerequisite-safe Runner-MCP code lane is justified. Continue only with bounded operator/live proof, replacement-host qualification, or optional external discovery.

## 2026-10-02 — Live runner readiness narrowed to controlled runtime update

- Current reviewed Runner MCP main checkpoint before this coordination update: `2732308ee0d6e74ba7bc63f9df8ee287f2787eac`.
- The bounded live runner is reachable again; the previous remote-connector quota is no longer the blocker.
- Local Runner MCP status reports operational mode, emergency stop inactive and self-update install recovery clear; `doctor` reports no failures and no warnings.
- Agent Bus configuration is present, but the installed Runner MCP runtime still reports 0.1.2. The newer read-only `autostart preflight` command is therefore not yet available on that installed runtime; no autostart activation was attempted.
- The deployed Runner Fabric CLI does not yet expose merged `agent-serve-qualification` from Fabric #482/#483. Normal `agent-serve` remains RESERVED and was not started.
- Fabric's security foundation already includes terminal replay without re-execution (#403), identity rotation/revocation (#418), split-brain fencing (#420) and primary operation with fallback disabled (#445).
- The remaining #110/#125 live gate is therefore operational: update the live Runner MCP/Fabric runtimes through their existing bounded control paths, then run Fabric #479's synthetic GitHub-denied work-unit/replay/fencing drill.
- #108 likewise remains open because this chat does not expose the bounded self-update dispatch action. Do not substitute manual pip/curl/package/source mutation for that missing control-plane action.
- Secondary discovery work under #101 remains optional and external; PR #222 made this independence rule mandatory in bootstrap/docs.

## 2026-10-02 — Secondary-directory independence policy

- External MCP directories/marketplaces are explicitly optional discovery surfaces, not Runner MCP dependencies or launch gates.
- Canonical authority remains GitHub `Blacksp1d3r/runner-mcp`, PyPI `aifordable-runner-mcp` and MCP Registry `io.github.Blacksp1d3r/runner-mcp`.
- Glama hosting/gateway, Smithery-specific hosting/bundling, alternate package identities and provider-specific deployment modes must not be introduced merely to obtain a listing.
- If a directory changes requirements or cannot represent the self-hosted project unchanged, skip/drop that listing instead of redesigning Runner MCP.
- This rule is duplicated deliberately in `AGENTS.md` so every future AI/agent session receives it during mandatory bootstrap.

## 2026-10-02 — Task 69 self-update hardening integrated

- Current reviewed Runner MCP main checkpoint: `4b5351de6e03ab8938ebb799e2847e2195e8ee3a`.
- Issue #217 is COMPLETE via PR #219.
- Exact-head attribution #285 and validation #790 are green, including Ruff/pytest, built release artifact and clean five-minute demo.
- Autostart CLI tests no longer observe real systemd/cron state or the host's runtime-smoke result.
- Pre-install self-update failures now restore the clean source checkout to the starting/installed main commit before any install transaction becomes authoritative.
- A successful source rollback preserves the original bounded failure category; source rollback failure becomes `source_recovery_required`.
- If an install transaction was persisted or became unreadable, install-recovery remains authoritative and artifacts are preserved; post-install recovery behavior is unchanged.
- The remaining Runner MCP lanes are not safe autonomous code work: #108 is a private-host proof, #198 waits on replacement-host/CPU qualification, and #110/#125 depend on Fabric #479 plus live Agent-Bus proof. #101 is external/public discovery follow-up.
- Do not reactivate the unreliable i9 host or duplicate Fabric durability/live-proof work from Runner MCP.

## 2026-10-02 — Fabric live-cutover dependency reconciled

- Runner Fabric was reconciled against current main after the 0.1.3 release.
- The former #256/#264 checkpoint is obsolete: coarse work-unit service/MCP, reserved loopback runtime and durable journal substrate are integrated through Fabric #258/#266/#355/#357, with Agent-Bus work-unit bridging also present.
- Fabric issue #479 now owns the remaining live bounded work-unit qualification with GitHub credentials/network denied, including exactly-once replay/restart/fencing evidence.
- Current Fabric `AgentWorkUnitService` still keeps active request/result ownership in its in-memory `_records` map and does not consume `FilesystemWorkUnitJournal`; do not infer service-level restart durability merely because the journal substrate exists.
- Fabric #486 adds concrete source-write adapters but explicitly does not activate live work-unit execution.
- Runner MCP #110 has been updated to this checkpoint. Task 58 remains blocked on the private-host qualification plus the live Fabric proof; no duplicate Runner-MCP implementation is justified.

## 2026-10-02 — Runner MCP 0.1.3 published

- Task 68 is COMPLETE.
- Protected workflow run `36962568072` ran against exact main `0aa013c279128e22fbd53be32c35bced3ae26834`.
- Final version-metadata verification, full release check, wheel/sdist build and immutable workflow artifact all passed before publication.
- PyPI publication via OIDC passed and the workflow confirmed exact version `0.1.3` became visible before continuing.
- Official MCP Registry publication passed using the pinned publisher and GitHub OIDC.
- GitHub pre-release `v0.1.3` was created with wheel and sdist assets; the tag resolves exactly to `0aa013c279128e22fbd53be32c35bced3ae26834`, matching current main at release time.
- Do not rerun publication or move `v0.1.3`. Subsequent work starts from post-release hardening/live-proof lanes (#198, #108, #110/#125) or a new bounded task.

## 2026-10-01 — Runner MCP 0.1.3 release candidate integrated

- Current reviewed main checkpoint: `ee6ab95bec9be4d8d2f7b75854e1b2a17503da76`.
- Task 67 is COMPLETE via PR #208.
- Candidate version metadata is synchronized at `0.1.3` across `pyproject.toml`, `server.json`, `src/runner_mcp/__init__.py`, `glama.json` and the publish-workflow default.
- CHANGELOG now separates already-published 0.1.1/0.1.2 history from the current unreleased 0.1.3 delta.
- `docs/RELEASE_NOTES_0.1.3.md` records security-relevant changes, unchanged dependency contract, upgrade notes and known activation limits.
- Exact candidate head `6e5f7ddb28c8d9dfe1a1cabe5a7f1153a854c5f9`: attribution #265 green; Runner MCP validation #772 green; built release artifact green; Clean Ubuntu installer proof #5 green.
- The first clean-demo attempt hit an external `files.pythonhosted.org` pip read timeout. The failed job was rerun on the exact same candidate SHA and passed; no product-code workaround was introduced.
- No tag, PyPI upload, MCP Registry publication or GitHub release has been performed.
- Publication is a separate release action and must use the exact green main revision after a final release check.

## 2026-10-01 — Task 64 integrated; Fabric activation blocker narrowed

- Runner MCP current reviewed main checkpoint: `f666876ac3096fdd6663b368b2f1fe4ecbbed279`.
- Task 64 is COMPLETE via PR #202. The shared local autostart gate now requires emergency-stop/recovery/restart clear state, fresh fixed runtime smoke and `host_integrity_clear` before systemd or cron mutation.
- Direct systemd/cron installer entry points independently reject a missing/non-clear activation permit before touching unit files, systemctl or crontab.
- Exact-head PR #202 attribution #253 and validation #761 are green, including Ruff/pytest, built release artifact and clean five-minute demo.
- Stale overlapping PRs #199 and #201 are closed as superseded.
- Runner Fabric reconciliation: #357 durable journal, #355 loopback agent runtime and #383 Agent-Bus work-unit bridge are merged. However `AgentWorkUnitService` on current Fabric main still keeps work-unit ownership/result state only in its in-memory `_records` map and does not consume the durable `FilesystemWorkUnitJournal`.
- Therefore Runner MCP issue #110 remains blocked on upstream Fabric durable service/resume integration plus private-host qualification (#198); do not activate the coarse bridge yet.
- No new Runner-MCP code lane should duplicate Fabric durability work. Continue with public/documentation or live/operator work only when its prerequisites are available.

## 2026-09-30 — Tasks 50–52 reconciled

- Current reviewed main checkpoint: `0bade0af6ee574b09de42bb493f5ecffa41657d5`.
- Task 50 is COMPLETE via PR #149 / `469138077066b7b924ba867456ad44dc6372c85d`; issue #143 closed.
- Issue #151 is COMPLETE via PR #152 / `0bade0af6ee574b09de42bb493f5ecffa41657d5`; exact-head #669/#157 and post-merge #671/#159 are green; issue closed.
- Task 51 review is COMPLETE: keep service-journal output local-only. Generic redaction cannot prove arbitrary application/customer/personal data safe for remote disclosure. No remote log action is authorized.
- Task 52 review is COMPLETE: PR #150 provides a bounded Fabric bootstrap foundation, but #144 remains open because three explicit guards are still missing.
- Task 53 must add: self-update/restart/recovery exclusion; fixed installed-runtime preflight; different-installed-commit first-install conflict before subprocess.
- PR #153 refreshes unique PR #127 relay-core work; do not duplicate it. Task 54 owns integration/closure.
- PR #129 remains unique primary watcher work; Task 55 owns reconciliation after Task 54.

Immediate resume order:
1. integrate this review/coordination PR after exact-head CI;
2. implement Task 53 and close #144 only after exact-head + post-merge proof;
3. reconcile #153 and close #127 only after #153 is integrated;
4. then reconcile #129 against the new main;
5. keep remote service logs deferred.

## 2026-09-29 — Tasks 47 and 49 integrated; bounded queue refilled

- Runner MCP `main` checkpoint: `67954dea2117cce3a1819132f6d3c7480dd34c82`.
- Task 47 is COMPLETE via PR #145 / merge `67954dea2117cce3a1819132f6d3c7480dd34c82`.
  - local/private only: `runner-mcp service-log PROJECT ALIAS --lines N`;
  - per-service `allow_log_read: false` opt-in;
  - fixed no-symlink `journalctl`, fixed argv/env, 1–100 entries, <=10s, <=32 KiB retained stdout;
  - Task-41 redaction receives known local runtime secrets/private paths plus private unit/health URL;
  - disabled/unknown service fails before subprocess;
  - read remains available during emergency stop;
  - no MCP, bridge, mailbox or Agent-Bus log action exists.
  - exact-head validation #654 + attribution #140 and post-merge validation #655 + attribution #142 are green.
- Task 49 is COMPLETE via PR #124 / merge `da367081f88d6d2342cf938a9b67ec59d9d10de0`.
  - explicit additive async migration start/status exists;
  - `migration_async` approval is distinct from synchronous `migration`;
  - synchronous `apply_migrations` and deployment-triggered migrations remain unchanged;
  - exact-head validation #622 and post-merge validation #623 are green.
- Task 50 is the next small CODE lane: close the remaining issue #143 gap by preflighting installed-runtime `pip` + `setuptools.build_meta` before wheel-stage mutation.
- Task 51 is review-only: decide whether any remote service-journal disclosure is justified after Task 47; do not add remote log authority during the review.
- Task 52 is review-only: define the first-install Runner Fabric bootstrap safety boundary for issue #144 before any bootstrap mutation/tool is implemented.
- PR #127 and PR #129 remain open and contain unique Agent-Bus work. Do not duplicate or close them merely because #131/#132/#134 later merged; reconcile/rebase those PRs separately.
- Issue #130 remains open because its live activation proof is broader than the merged lifecycle code.
- Issue #143 remains open until Task 50 production preflight is integrated.
- Issue #144 remains open and high risk; Task 52 review comes first.

Immediate resume order:
1. integrate this coordination update after exact-head CI;
2. implement Task 50 as the next bounded CODE lane;
3. Task 51 and Task 52 can proceed as independent reviews if code work blocks;
4. do not duplicate PR #127/#129 Agent-Bus work;
5. keep remote service logs, generic package install, arbitrary VCS/package/shell authority and production mutation out of scope.

## 2026-09-28 — Task 44 integrated; Task 45 async migration boundary decided

- Runner MCP `main` checkpoint before this review branch: `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 is COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 evidence is fully green: exact-head validation #607 + attribution #91 and post-merge validation #609 + attribution #94; full pytest, Registry/whitespace, release artifact and clean demo are green.
- The durable migration substrate is additive only: private strict migration-job storage, queued/running/terminal state, restart -> interrupted without replay, canonical plan revalidation, bounded public status and read-only `MIGRATION_JOB` completion delivery. Existing synchronous `apply_migrations`, direct `migration_status`, bridge `APPLY_MIGRATIONS` and deployment-triggered migrations remain unchanged.
- Task 45 review is COMPLETE in `claude_feedback/TASK45_ASYNC_MIGRATION_INTEGRATION_REVIEW.md`.
- Task 45 decision: do not version or silently change synchronous `apply_migrations`. If async remote execution is integrated, add explicit `start_migration_job` + `migration_job_status` tools / bridge actions.
- Async execution must use a separate human approval operation `migration_async`, with a fixed async execution discriminator in the approval binding, so sync and async approvals are not interchangeable.
- Required start ordering: require configured runner -> recompute canonical migration state -> consume async approval -> durable queued persistence -> worker start. A consumed approval with no job is safer than durable execution intent without consumed approval.
- Bridge persistence/finalize ambiguity after a job starts must never replay/enqueue a second job. Immediate start result means durable acceptance/queueing, not migration completion.
- Task 49 is the bounded CODE follow-up. It must not add cancellation, automatic retry/resume, arbitrary SQL/executable/cwd, production mutation, automatic restore, generic async execution, job listing or change the current synchronous path.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- PR #120 package-version identity fix is separate from this review; it is being revalidated against the Task-44 main before merge.
- Issues #108/#110/#101 retain their existing external/upstream gates.

Immediate resume order:
1. integrate this Task-45 review after exact-head CI;
2. Task 49 may implement only the explicit additive async migration start/status contract;
3. Task 47 remains a separate safe local-only lane and may proceed independently;
4. preserve synchronous `apply_migrations` until/unless Task 49 is separately green and integrated;
5. do not infer completion from bridge/audit records; terminal migration completion comes only from durable migration-job metadata.

## 2026-09-28 — Tasks 48 and 43 complete; migration-job substrate next

- Runner MCP `main` is `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`.
- Task 48 is COMPLETE via PR #115 / merge `02475b4c5aa1f103b55f9e4ca6a71e0d09892c7c`: deploy/rollback now share one fixed private release-root `fcntl.flock` boundary in addition to the existing in-process thread lock. Exact-head and post-merge validation are green.
- Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`: local-only `retention prune-plan` / `retention prune-release` can remove exactly one freshly eligible staging orphan release per short-lived single-use plan after fresh current/metadata/policy revalidation under the shared release lock.
- Task 43 preserves the retained rollback/reference closure and migration boundaries, never deletes backups, never adds automatic pruning, and adds no MCP/mailbox/bridge deletion authority.
- Quarantine/transaction state is private and durable; post-quarantine failure is reported as manual-attention state rather than guessed success or replay.
- Exact-head Task 43 validation #592, attribution #76, build artifact and clean demo are green; post-merge validation #593 and attribution #77 are green.
- Task 44 durable migration-job substrate is now the preferred next independent CODE lane. Its scope remains additive: persisted migration jobs + read-only completion source only; existing synchronous MCP/bridge `apply_migrations` and deployment-triggered migrations remain unchanged.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- Issue #108 remains externally blocked by the authorized private-host connector quota. Issue #110 remains gated on upstream Fabric durable gateway/startup readiness. Issue #101 remains externally gated for actual secondary-directory submissions/claims.

Immediate resume order:
1. integrate this coordination-only status update after exact-head CI;
2. implement Task 44 from its Task 42 review with a separate private migration-jobs root and strict restart-no-replay semantics;
3. after Task 44 integration, perform Task 45 review before any remote async migration contract change;
4. Task 47 may proceed independently if Task 44 blocks;
5. keep backup pruning, automatic pruning, restore execution and all remote deletion authority deferred.

## 2026-09-27 — Task 46 reconciled; Task 48 release-lock prerequisite queued

- Live Runner MCP `main` before this coordination branch: `37c78fd0d2a0e2f620dc225f81e72843413ef3c3`; PR #113 discovery hardening is merged and post-merge validation #582 / attribution #66 are green.
- The previously unintegrated Task 46 review was reconciled against current `DeploymentManager`. Its core finding still holds: deploy/rollback use only per-process `threading.Lock` instances, so a future local CLI pruning process cannot safely share that mutation boundary.
- Task 46 is therefore COMPLETE as a review and its canonical deliverable is `claude_feedback/TASK46_CROSS_PROCESS_RELEASE_LOCK_REVIEW.md`.
- Task 48 is the separate prerequisite-safe CODE follow-up: add one private release-root `fcntl.flock` primitive and integrate it into deploy/rollback while preserving the existing thread lock and release -> database lock ordering.
- Task 43 local one-release pruning remains BLOCKED until Task 48 is integrated and proven. Do not implement pruning inside Task 48.
- Task 44 durable migration-job substrate and Task 47 local bounded service-journal reader remain independent prerequisite-safe CODE lanes.
- Issue #108 private-host recovery proof remains externally blocked by the authorized remote-management connector quota; do not bypass it with broader authority.
- Issue #110 Fabric bridge activation remains upstream-blocked. Latest checkpoint: Fabric #258 and #266 are merged/green; #256 and #264 remain open on failing/non-mergeable heads; #268 remains open.
- Issue #101 secondary discovery remains externally gated for actual directory submissions/claims; canonical discovery metadata is now hardened on main and the official MCP Registry publicly indexes v0.1.2.

Immediate resume order:
1. integrate this coordination-only Task 46 review after exact-head CI;
2. implement Task 48 as its own bounded code PR with multi-process/adversarial lock tests;
3. only after Task 48, reconsider Task 43 pruning;
4. Task 44 or Task 47 may proceed independently if Task 48 becomes blocked;
5. keep #108/#110/#101 external gates honest; do not convert preparation into claimed proof/publication.

## 2026-09-27 — Runner Fabric coarse bridge transport merged

- Runner MCP transport integration is merged on `main` as `3ebd39981c358c307fa66afa32ad2f5fc32731cf` via PR #111; issue #109 closed automatically as completed.
- Exact PR head `872798831403515bc6944b62efaac5992897b253` passed Runner MCP validation run #571 and commit-attribution run #54 with zero review threads.
- The PR validation checked GitHub's synthetic merge `cd60179b8d8f7c5d8895beef6164a7cb932937fe`, combining #111 with then-current `main` `776b5d0fd3499ca6ed6674806b2075167fc59f9e`; current-main compatibility was therefore validated before merge.
- Post-merge commit-attribution run #55 and Runner MCP validation run #572 are both terminal green on exact merged `main` `3ebd39981c358c307fa66afa32ad2f5fc32731cf`.
- The bridge remains optional and fail-closed: without private loopback Fabric configuration, no Fabric tools are registered and normal Runner MCP behavior is unchanged.
- When configured, the only Fabric-facing tools are `fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`; no generic GitHub, Git, shell, filesystem, provider or status-polling proxy was added.
- Additional hardening on #111 gives each calling thread an independent local MCP session and fails closed on mismatched expected revision, mismatched work-unit identity, or inconsistent status/result pairs.
- Runner Fabric remains the orchestration/control-plane owner. Runner MCP only authenticates, bounds, audits and transports the coarse request/result.
- Issue #110 remains the live activation/end-to-end follow-up. Do not duplicate the merged transport work from #109/#111.
- At this checkpoint Runner Fabric prerequisites are not ready for live activation: #258 and #266 still have failing Foundation CI, #266 is not mergeable, and #268 remains open. Reconcile upstream live state before acting.

Immediate resume order:
1. confirm post-merge Runner MCP validation #572 is terminal green;
2. keep #110 blocked until the required Runner Fabric work-unit service/MCP/startup lanes are green, integrated and privately deployable;
3. once upstream is ready, configure only the private loopback bridge and prove one bounded end-to-end coarse work-unit without exposing infrastructure details;
4. benchmark the coarse handoff against the former many-call GitHub workflow without weakening existing Runner MCP approval, operator-stop or fault-containment boundaries;
5. independent open lanes remain #108 (private-host self-update recovery proof) and #101 (external discovery/authenticated submissions); do not use either to bypass their human/private-environment gates.

## 2026-09-27 — AI fault-containment regression proof merged

- PR #106 merged to `main` as `affc2c054b3072f480822675718baefedc2db619` after exact-head Runner MCP validation and commit-attribution policy both passed, with zero review-thread blockers.
- Cross-boundary security tests now prove that client/AI intent cannot select an unlisted executor capability, mutate an already approved plan, reuse approval across action classes, self-assert production mutation authority or override the external operator emergency stop.
- Read-only work remains available during the operator stop, preserving the proportional-security rule instead of turning every safety state into a blanket development block.
- No new runtime authority was introduced; this slice locks existing executor, approval and operator-safety boundaries with regression coverage.
- Open follow-up #101 tracks secondary discovery; #108 now tracks the remaining private-host proof for recovery-capable self-update. Canonical v0.1.2 publication is already complete, and neither lane should duplicate completed release/runtime work.

## 2026-09-27 — AI fault containment roadmap rule prepared

- Runner MCP now documents AI/client requests as intent rather than execution authority.
- Security gates are proportional to blast radius: contained read/test work stays automatic,
  controlled staging/mutation paths use deterministic policy/freshness/fencing, and protected
  production/credential/destructive actions require independent authority.
- Prompt-injected content cannot create capabilities, weaken policy or satisfy approval.
- This documentation change adds no new runtime authority.

## 2026-09-27 — v0.1.2 canonical distribution published

- Human-approved Publish Runner MCP run #2 completed successfully from exact main `83175f439c60346f92b5759a90993c3b8f5352f8`.
- PyPI published `aifordable-runner-mcp==0.1.2` successfully and the workflow verified that exact version became publicly visible.
- Official MCP Registry validation, GitHub OIDC authentication and publication all succeeded for `io.github.Blacksp1d3r/runner-mcp` version `0.1.2`.
- GitHub pre-release `v0.1.2` was created with wheel and sdist assets; tag `v0.1.2` points exactly to `83175f439c60346f92b5759a90993c3b8f5352f8`.
- Repository description and discovery topics are already live; README/distribution follow-up is moving canonical PyPI/Registry links and one consistent directory-submission packet into the first-party docs.
- Secondary discovery: Glama, Smithery, mcp.so and optional AllMCPs are the next channels. The current GitHub App cannot write to the external `chatmcp/mcpso` submission thread, so that submission needs a user-authenticated browser/CLI path rather than an integration bypass.
- Do not republish or overwrite PyPI 0.1.1. It remains historical evidence of the first PyPI-only attempt; 0.1.2 is the canonical cross-registry release.

## 2026-09-26 — v0.1.1 AIfordable PyPI identity integrated

- PR #102 merged to `main` as `d948945034e07616d673945467e9b2e44748fa10` after exact-head validation and commit-attribution checks were green with zero review threads.
- Post-merge `main` validation and attribution were green on the merge commit.
- Python distribution identity is now `aifordable-runner-mcp`; product/primary CLI remain Runner MCP / `runner-mcp`; `aifordable-runner-mcp` is also exposed as a launcher alias for uvx/Registry compatibility.
- Pending PyPI Trusted Publisher is configured for `aifordable-runner-mcp`, `Blacksp1d3r/runner-mcp`, `publish.yml`, environment `pypi`; GitHub `pypi` is main-only with required human review and no stored PyPI token.
- The previous umbrella brand is retired from current project materials; AIfordable is the current umbrella identity.
- Remaining release action is human-controlled: dispatch `Publish Runner MCP` from `main` with version `0.1.1`, approve the `pypi` environment deployment, then verify PyPI -> MCP Registry -> GitHub pre-release in that fail-closed order.

## 2026-09-26 — v0.1.1 PyPI identity reconciled

- Active branch: `release/v0.1.1-aifordable-pypi`.
- PyPI rejected the new project name `runner-mcp` as too similar to an existing project; no package was published under that name.
- The pending Trusted Publisher is now configured for `aifordable-runner-mcp`, repository `Blacksp1d3r/runner-mcp`, workflow `publish.yml`, environment `pypi`.
- The GitHub `pypi` environment is restricted to `main` and requires the repository owner as reviewer; no long-lived PyPI API token is used.
- This branch changes only distribution/branding metadata: PyPI package `aifordable-runner-mcp`, CLI/product name remains `runner-mcp` / Runner MCP, official MCP Registry identity remains `io.github.blacksp1d3r/runner-mcp`.
- Public umbrella branding is being reconciled to AIfordable; the previous umbrella brand is retired from current project materials. Runtime/security authority remains unchanged.
- Publication remains blocked until this branch is exact-head green, reviewed, merged to `main`, and the human-triggered `Publish Runner MCP` workflow is approved/run for version `0.1.1`.

## 2026-09-26 — v0.1.1 distribution/discovery release prepared

- Active branch: `release/v0.1.1-discovery`.
- This slice changes packaging, discovery, release automation and public positioning only; it adds no new Runner MCP runtime authority.
- Package/version metadata is prepared for `runner-mcp` 0.1.1 and official MCP Registry identity `io.github.blacksp1d3r/runner-mcp`.
- `server.json`, distribution metadata regression tests, PyPI Trusted Publishing guidance and a human-triggered publish workflow are included.
- Publication order is fail-closed: exact release validation and artifact build -> PyPI OIDC publication -> PyPI visibility proof -> MCP Registry GitHub-OIDC publication -> GitHub pre-release.
- External publication is NOT complete yet. The first PyPI release still requires the one-time pending Trusted Publisher configuration plus matching protected GitHub `pypi` environment; then the publish workflow must be explicitly run from merged `main`.
- README/launch copy now lead with the concrete problem: useful AI development/staging operations without making a general-purpose remote shell the normal interface.
## 2026-09-24 — v0.1.0 alpha released and public docs reconciled

- GitHub pre-release `v0.1.0` is published from exact validated release commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; the published notes preserve the alpha limitations and validation provenance.
- Post-release docs PR #98 merged as `5647aa8839af90451189d2d943ce393edfacfe78`. Exact PR head `adc08c86628aed6256ba44271d0a55cd366ae3e8` passed run #514 / `36041142332`; merged-main run #515 / `36041352332` is fully green.
- README now links the current alpha, CHANGELOG records the dated 0.1.0 release, and launch-readiness no longer describes the first tag as pending.
- The immutable release reference remains the earlier exact green commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; post-release documentation is intentionally later on `main`.
- GitHub repository metadata still needs the prepared public wording: description `Security-first self-hosted MCP for controlled AI development and staging operations without a general-purpose remote shell.`; topics `mcp`, `model-context-protocol`, `self-hosted`, `ai-tools`, `developer-tools`, `devops`, `staging`, `security`, `python`, `automation`.
- Runner Fabric remains a separate private/proprietary project and is not part of the Runner-MCP MIT release.
- Remaining broader-launch gates: clean-host install verification from published `v0.1.0`, repository metadata, then optional ecosystem/registry submission and human-controlled community timing.

## 2026-09-24 — release-track reconciliation after Task 41 integration

- Runner Fabric remains a separate private repository/project. Runner-MCP stays the small, auditable execution product intended for release and must not absorb Runner Fabric orchestration scope.
- PR #97 `feat: add reusable bounded text redaction` merged as `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`.
- Exact PR head `91e0c1b1e737ad14a43b31750cfdfbf1bf582f24` passed validation run `36037258558` fully green: Ruff/pytest/whitespace, clean five-minute demo and built release artifact.
- Live reconciliation after the merge found no open Runner-MCP pull requests and no open Runner-MCP issues.
- This coordination update must itself receive exact-main green CI before any first alpha tag is considered.
- Task 10 private-host self-update/recovery proof remains unproven; release wording must keep that limitation explicit rather than implying live-host proof.
- The next release-track action after exact-main CI is a final alpha-candidate gate check. Tag/release, repository description/topics, registry submission and external posting remain explicit user-controlled actions.

## 2026-09-24 — Task 41 bounded redaction complete; Task 43 lock prerequisite found

- Task 41 implementation is COMPLETE on PR #97 pending final exact-head CI/integration.
- New shared bounded text-redaction primitive handles known secrets, known private paths and the existing bearer/password/token/GitHub-token patterns with explicit input/output byte limits and deterministic truncation.
- TestRunner now delegates its log scrubbing to the shared primitive; no journal reader or remote log authority was added.
- Direct implementation prep for Task 43 found a real safety prerequisite: `DeploymentManager._lock_for()` uses in-process `threading.Lock`, while Task 43 is a local CLI process and can therefore race deploy/rollback in the long-lived MCP process.
- Task 43 is blocked on Task 46 cross-process release-mutation lock review. Do not implement pruning until that boundary is resolved.
- Task 44 is now prerequisite-safe because Task 42 / PR #96 merged as `82ecef725d828b69e328f8f474553e01ef8548cb`.
- Task 47 is queued after Task 41 for a local/private service-journal reader with explicit per-service opt-in only; MCP/mailbox log exposure remains deferred.

## 2026-09-24 — Task 42 durable migration-job substrate review complete

- Task 42 review is COMPLETE on PR #96 pending integration.
- A dedicated persisted migration-job substrate is justified, but it must be additive first: the current MCP/bridge `apply_migrations` path remains synchronous until the substrate is independently proven.
- Future migration jobs must durably persist queued state before worker start, revalidate the exact approval-bound migration plan, call existing `DatabaseManager.apply_migrations()` at most once, and never replay queued/running work after restart.
- Restarted queued/running migration jobs become terminal `interrupted`; ambiguous success is reported for attention rather than guessed or retried.
- Deployment-triggered migrations remain synchronous inside deployment.
- Task 44 is queued for the private job substrate plus read-only completion scanner. Task 45 is separately blocked on Task 44 for any later remote asynchronous integration decision.
- Task 43 is prerequisite-safe after Task 40 / PR #95; Task 39 is already integrated on main via PR #94.

## 2026-09-24 — Task 39 adapter preset boundary refactor complete on PR #94

- Task 39 implementation is COMPLETE on PR #94 pending final exact-head CI/integration.
- Built-in pytest, Ruff and Alembic recipe materialization moved out of generic `config_manager.py` framework branches and behind typed adapter methods.
- Python adapter executable discovery remains project-local, rejects symlinked roots/virtualenvs/executables, requires executable access and verifies the resolved executable remains under the project root.
- The generic adapter has no built-in recipe authority. Unknown/ambiguous presets fail closed.
- The `custom` path remains explicit/local with the previous validation and no shell command string.
- Direct adapter/config-manager regression coverage and extension documentation were updated.
- No dynamic plugin loading, framework dependency, speculative adapter or new execution authority was added.
- Tasks 37 and 40 are already integrated on main; Task 43 remains blocked only on its explicit ownership/implementation claim, not on Task 40.

## 2026-09-24 — Task 40 retention pruning execute-boundary review complete

- Task 40 review is COMPLETE on `chatgpt/task40-retention-pruning-review` pending integration.
- Task 34 evidence is sufficient for one conservative next mutation only: local/manual pruning of exactly one old non-migration orphan release outside the entire retained rollback chain.
- The first executable slice must preserve current/direct rollback/reference closure and every migration-boundary release, acquire the deployment lock, recompute eligibility, bind a short-lived local plan, quarantine atomically, and use only symlink-safe fd-relative recursive deletion.
- Manual backups remain indefinite-retention/non-candidates. Backup pair pruning remains separately deferred because flat dump+metadata deletion needs its own durable crash-recovery transaction.
- Automatic/unattended pruning and all MCP/mailbox deletion authority remain deferred.
- Task 43 is queued but blocked until Task 40 is integrated.

## 2026-09-24 — Task 34 read-only retention preview implementation complete on PR #92

- Task 34 implementation is COMPLETE on PR #92 pending final exact-head CI/integration.
- New local CLI: `runner-mcp retention preview PROJECT`.
- Preview is advisory only and explicitly reports `deletion_authorized=false`; no release, backup or metadata deletion/rewrite path was added.
- Strict scanning fails closed on unsafe/symlink/broad-permission/malformed release or backup metadata, incomplete backup pairs and dump-size mismatch.
- Current release, direct rollback target, retained release references and migration-recovery references are protected; manual backups are never automatically eligible.
- Production/non-staging projects remain read-only; preview remains available while the emergency stop is active.
- Public output contains only bounded project/environment/ID/timestamp/kind/category state and does not expose filesystem paths, DSN, service units, health URLs, dump content or private configuration.
- Focused tests plus the full suite have passed during implementation; final exact-head PR CI remains authoritative before merge.
- Actual pruning/deletion remains deferred. A later execute-boundary review must separately resolve locking, crash-safe deletion, rollback-chain semantics and typed confirmation.
- PR #91 already merged as `11b9a4d4e508ac93cd436037563c09d08cfa43ab`, completing Tasks 33, 35 and 38.
- Task 37 restore-execution boundary review is proceeding independently on PR #93; Task 39 is now prerequisite-safe after Task 38 integration.

## 2026-09-24 — Tasks 32 and 36 alpha-readiness work landed

- Task 32 COMPLETE: PR #89 merged as `e629515f9c7e7a5d44506dfb82a48343870f94da`.
- Task 32 exact PR head `99c72037eff4ed54cf7e92f7a08b278b48af4e45` passed CI run 35967246877 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Audit conclusion: package/build/demo mechanics are suitable for an alpha candidate, but six public-documentation drift items had to be reconciled before any tag.
- Task 36 COMPLETE: PR #90 merged as `8c971016e4fc3cd821dc52d28334567c20835ff4`.
- Task 36 exact PR head `1b3567b5de1f5a4ac5a67db16c609db2edac25dd` passed CI run 35967550375 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- CHANGELOG now treats 0.1.0 as an unreleased alpha candidate; restore/security wording, mailbox launch copy, README rendering, public-data hygiene wording and connectivity limitation are reconciled.
- Live GitHub still has no `v0.1.0` tag or GitHub release. Repository description/topics, tag/release, registry submission and external posts remain explicit user-controlled actions.
- Task 10 private-host live self-update/recovery proof remains externally BLOCKED and must not be overclaimed in release wording.
- Current bounded queue: Tasks 33–35. No release/publication action was performed.

## 2026-09-24 — Task 31 local read-only restore preflight landed

- Task 31 COMPLETE: PR #88 merged as `e54a0684bdc9da3a32d062e0e0e45261c1616020`.
- Exact PR head `fc08b60c6feed85824b6097bf1479e7e41a29844` passed CI run 35966414093 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Local CLI now supports `runner-mcp database restore-plan PROJECT BACKUP_ID` for a read-only PostgreSQL backup preflight.
- The preflight validates strict backup identity/shape, private regular-file modes, size, symlink-free storage and fixed trusted `pg_restore --list` parseability without reading the configured DSN or connecting to a database.
- The archive is opened once with no-follow semantics, streamed through SHA-256 privately, passed to `pg_restore` over stdin so the private dump path is not placed in argv, and revalidated/hash-checked after parse to detect content/permission races.
- Production projects report ineligible. Emergency stop does not block the read-only preflight.
- Database restore execution, pre-restore backup, restore approval authority, WAL/PITR, production recovery and MCP/bridge/mailbox restore exposure remain deferred.
- Current bounded queue: Tasks 32–34. Task 10 remains externally BLOCKED.

## 2026-09-24 — Task 30 retention-pruning boundary review landed

- Task 30 COMPLETE: PR #87 merged as `99d081cd242642bfa8346031a22079b7397869bc`.
- Exact PR head `0a6e09fe4e4cd403c6ee6c4cc66461694b019a2a` passed CI run 35958661041 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- Review conclusion: existing age/count predicates are policy inputs, not destructive authorization. Manual backups have no automatic-deletion policy; current/rollback/reference/migration-recovery relationships require additional protection.
- Automatic deletion remains deferred. Task 34 is queued as the smallest safe follow-up: local read-only retention preview only.
- Current bounded queue: Tasks 31–34. Task 10 remains externally BLOCKED.
- No backup/release deletion, metadata rewrite, retention change, approval expansion or mailbox deletion authority was performed.

## 2026-09-24 — Task 29 privacy-safe connectivity guidance landed

- Task 29 COMPLETE: PR #86 merged as `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
- Exact PR head `7d4c264fbfac6881badbdf8f9bc69ea7a7ab12e8` passed CI run 35958283065 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- `runner-mcp guide` now reports only a generic connectivity category and bounded next steps. Configured external hostnames/resource URLs/auth issuers/tokens/private paths are not printed.
- Public setup is now documented consistently as external HTTPS identity only; it does not bind publicly or configure TLS, DNS, firewall, proxy or tunnel state.
- Current Secure MCP Tunnel guidance is linked to canonical OpenAI documentation; Runner MCP remains loopback-first and vendor provisioning stays external.
- Current bounded queue: Tasks 30–32. Task 10 remains externally BLOCKED.
- No network exposure, TLS/DNS/firewall, tunnel, tag, release or publication action was performed.

## 2026-09-24 — Task 28 deployment/rollback completion delivery landed

- Task 28 COMPLETE: PR #85 merged as `131e168e02b7d5781441bbc8256e65de434e6166`.
- Exact PR head `87f1d0c8295b059b4504e2971c5ef89ed9dc8422` passed CI run 35951310986 fully green: Ruff, whitespace, 1235 pytest tests, built release artifact and clean demo.
- Completion delivery now scans configured deployment/rollback job metadata read-only and never instantiates `DeploymentJobRunner`.
- Strict validation requires exact lowercase 32-hex job identity, explicit deploy/rollback operation, safe project, known state, private regular metadata and timezone-aware terminal timestamp; malformed/duplicate/non-finite/oversized/unsafe metadata fails closed.
- Deploy and rollback events use source-scoped deterministic IDs and the existing bootstrap cutoff, local delivery ledger and remote marker idempotency.
- Notification bodies omit `Test profile: None` for non-test events and expose only validated project, allow-listed operation, state and event ID. Deployment result/error/commit/release/path metadata is not copied.
- Migration completion remains blocked pending a separately reviewed durable migration-job substrate.
- Current bounded queue: Tasks 29–31. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment, rollback, migration or external mutation was performed by this task.

## 2026-09-24 — Task 27 database restore/recovery review landed

- Task 27 COMPLETE: PR #84 merged as `f1e92bb2997ad8b9d26e978892319289e1b7e4f1`.
- Exact PR head `a90667259b7dea7d6dcddf1ead26fc982d4fb893` passed CI run 35949363983 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review preserves the hard separation between code rollback, one-backup logical restore and WAL/PITR. Automatic/remote restore remains unavailable; production restore remains outside Runner MCP mutation authority.
- Task 31 queued as the smallest safe follow-up: local read-only restore preflight/plan only, with strict backup identity/privacy and fixed pg_restore parseability checks; no database mutation or MCP/mailbox restore action.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 28–31.
- No tag, release, publication, deployment, migration, restore, deletion or external database action was performed.

## 2026-09-24 — Task 26 bounded service-journal review landed

- Task 26 COMPLETE: PR #83 merged as `b08a0b10afcce754440c37025230773da72c6c05`.
- Exact PR head `faa5126548021c9294e3a395c6b71344505e545d` passed CI run 35949004101 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review conclusion: remote/MCP service-journal access stays deferred. Current alias/process boundaries are strong, but arbitrary application journal content needs an explicit per-service log-read opt-in and a reusable bounded text-redaction prerequisite before any local reader is justified.
- Task 30 was added from the roadmap's explicit deferred retention-pruning work to keep the public queue dependency-safe.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 27–30.
- No tag, release, publication, deployment, migration, restore, log exposure or deletion was performed.

## 2026-09-24 — Task 25 private connectivity/TLS onboarding review landed

- Task 25 COMPLETE: PR #82 merged as `f2c1d6a135133033ab1e0059f9a92cfec3021d88`.
- Exact PR head `38b3143d53d49c58af896adfe96b943e34c2ee5a` passed CI run 35948648167 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review confirms Runner MCP already preserves the required runtime safety boundary: setup does not mutate network exposure, serve/autostart remain loopback-first, non-loopback bind requires explicit override, and non-loopback HTTP is rejected/flagged.
- Demonstrated onboarding drift: `security/CONNECTIVITY.md` still describes Secure MCP Tunnel as a future connection, while current official OpenAI guidance and Runner MCP's own README/Quickstart describe it as available for supported products.
- Task 29 queued for documentation + privacy-safe guide reconciliation only; it must not configure TLS, DNS, firewall, reverse proxy or tunnel state.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 26–29.
- No tag, release, publication, deployment, migration, restore or network mutation was performed.

## 2026-09-24 — Task 24 completion-delivery expansion review landed

- Task 24 COMPLETE: PR #81 merged as `d9f7d40f952ab39478d4a0286d317f160d6b46ce`.
- Exact PR head `22d5e9a7c7e5ab854b81d84b7b9997202837caf4` passed CI run 35915217076 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review finding: persisted deployment and rollback jobs are safe candidates for one bounded read-only completion-delivery integration; migration completion is blocked because no dedicated persisted migration-job substrate exists.
- Task 28 queued from this evidence for deployment/rollback completion delivery only.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 25–28.
- No tag, release, publication, deployment, migration or database action was performed.

## 2026-09-23 — Task 23 completion watcher diagnostics landed

- Task 23 COMPLETE: PR #80 merged as `873f905c64cdfbfc0ec6ac4b5091c04877b84d59`.
- Exact PR head `595bb6466e7eca50b4b21a9dbc8695a59b248c11` passed CI run 35914643900 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- `CompletionNotifierRuntime.run_forever()` now emits only enum-rendered lifecycle, healthy/degraded cycle and bounded restart-failure diagnostics through an optional sink.
- Delivery/replay/idempotency behavior remains unchanged; tests inject repository/path/token/event/URL/exception literals and prove they cannot enter diagnostics.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 24, 25 and 26.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 22 cron supervisor diagnostics landed

- Task 22 COMPLETE: PR #79 merged as `1bfeb9e7e8991058fb82a31b6d93b94f77c5ba72`.
- Exact PR head `65e15a9654e131073d8e90dc90cfa5e0536b9781` passed CI run 35903803377 fully green: Ruff, whitespace, 1208 pytest tests, built release artifact and clean demo.
- `run_cron_component()` now emits only enum-rendered `cron_supervisor` diagnostics for lock-held, exec handoff and bounded start/restart failure states through an optional sink.
- Diagnostics contain no selected component, argv, executable/config path, environment value or raw exception text; adversarial tests inject sensitive literals and prove they cannot escape.
- Cron ownership, locking, command construction and execution authority were not changed.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 23, 24 and 25.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 21 managed autostart secure I/O landed

- Task 21 COMPLETE: PR #78 merged as `22e14fff99a4f02a30f2edf9abffd98a8b1792ea`.
- Exact PR head `01ee0c0bfeaeae8f3a07a47f4162d4f9560304ab` passed CI run 35903107229 fully green: Ruff, whitespace, 1207 pytest tests, built release artifact and clean demo.
- `autostart._write_managed_unit` now uses the shared private atomic-replace primitive while preserving the existing managed-marker ownership refusal.
- Regressions prove unmanaged unit content is preserved, successful writes end at 0600, fsync/replace failures keep the previous managed unit and emit only bounded errors, and a symlink swap cannot alter its referent.
- Cron, job metadata, ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from explicit roadmap items: Tasks 22 and 23 remain CODE lanes; Tasks 24 and 25 are bounded CHAT REVIEW lanes for completion-delivery expansion and private connectivity/TLS onboarding.
- Task 10 remains externally BLOCKED on a usable private-host proof path. No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 20 bridge adversarial matrix landed

- Task 20 COMPLETE: PR #77 merged as `4bfd71d85cb5228ba328ee17fc60414c84c43e0a`.
- Exact PR head `666a399803db41bae4deae73fc4f205de5e97854` passed CI run 35895116909 fully green: Ruff, whitespace, 1203 pytest tests, built release artifact and clean demo.
- Test-only hardening: one minimal valid fixture now exists for every BridgeAction, every syntactically valid non-owned optional field is rejected per action, action case/hyphen/prefix variants fail closed, duplicate request_id and request-side NaN/Infinity fail closed, and uppercase self-update commit remains rejected.
- Every adversarial rejection is exercised through BridgeProcessor with fail-if-reached replay/result boundaries and an executor invocation counter, proving invalid requests do not reach execution.
- No production protocol, action enum, alias, normalization, identifier regex, replay state, executor mapping or capability changed.
- Current UNCLAIMED bounded public queue: Tasks 21, 22 and 23. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 18 private atomic-replace hardening landed

- Task 18 COMPLETE: PR #76 merged as `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
- Exact PR head `97fcde693d6264171920c386d10e9e63403a9a9a` passed CI run 35894315537 fully green: Ruff, whitespace, 794 pytest tests, built release artifact and clean demo.
- Added one internal `secure_io.atomic_replace_private` overwrite primitive using a random same-directory temp, exact 0600 descriptor mode, file fsync before atomic replace, symlink refusal, ordinary-failure cleanup and bounded errors.
- `config_manager` and `approval_manager` now use the primitive while retaining their existing higher-level locks and serialization/state ordering.
- Completion notifier config/bootstrap private JSON state now uses the primitive while retaining size/schema checks and parent-creation behavior.
- Autostart, cron, high-churn job metadata, in-place ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from existing review evidence: Tasks 20, 21, 22 and 23 are UNCLAIMED; Task 10 remains externally BLOCKED on a private-host proof path.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Tasks 16/17 landed and session reconciled

- Canonical main checkpoint after PR #74: `3d7792ee088a10ca44126415394e74c8e3c29ce3`.
- Task 16 COMPLETE: adversarial protocol review merged via PR #72; no runtime capability-expansion defect demonstrated; bounded follow-up Task 20 queued for exhaustive fail-closed regression coverage.
- Task 17 COMPLETE: append-only audit writer hardening merged via PR #73. Exact final head `60466a72b1c8492eac54e4963b9d7ef4bb572977` passed CI run 35891213181 fully green.
- PR #74 merged the queue/agent handoff evidence for Tasks 16/17.
- Task 10 remains externally BLOCKED pending a usable private-host proof path.
- Next safe implementation work is Task 18 or Task 20 after live ownership reconciliation.
- No release/tag/publication was authorized or performed.

## 2026-09-23 — v0.1.0 public release docs prepared

- PR #57 merged: the changelog now has a dated v0.1.0 release-candidate section and Unreleased is reopened.
- `docs/RELEASE_NOTES_0.1.0.md` now covers the completed self-update hardening, bounded runtime visibility and the no-dependency bootstrap boundary.
- The release notes explicitly state that the newest private-host self-update recovery matrix has not yet been freshly re-proven.
- No tag, GitHub release or external publication has been created.
- After this handoff-only update lands, the resulting exact `main` commit must pass public CI and a final privacy review before it can be considered a tag candidate.
- The remaining non-public evidence item is the private-host live self-update proof; if it is not completed before release, the limitation must remain explicit.

## 2026-09-23 — Tasks 2–9 queue complete

Current public repository state:
- PR #53 merged as `0c46bbefb8fcad6ae5c7f87450e638c40492a41a`: Task 6 documentation/CLI contract audit complete; `runtime_doctor` is documented and the stale evergreen pre-tag test count is gone.
- PR #54 merged as `69e604935bfe0fef0dd61b48dfdde76fed8f46ba`: Task 7 dependency compatibility/bootstrap design complete; `docs/SELF_UPDATE_COMPATIBILITY.md` is the canonical boundary.
- PR #55 merged as `358f8f6345a7ff6f094eb6c8e4d7db4b9943aed7`: Task 9 release-candidate hygiene dry run complete.
- Tasks 2–9 are complete; no open Runner-MCP PR existed when this checkpoint was reconciled.
- No tag, release or external artifact has been created.

Next safe release-preparation work:
- finalize the v0.1.0 changelog and release-notes draft;
- validate the exact candidate commit and repeat public-repository privacy review before any tag;
- keep dependency/build/interpreter contract changes on the normal dependency-resolving bootstrap path;
- reconcile the remaining private-host self-update live proof, or explicitly retain that limitation in release notes.

Private runtime state:
- this batch did not re-probe the private host;
- older watcher recovery-attention observations remain historical/last-known, not current health evidence;
- never reset watcher replay/cursor/transaction state as a shortcut.

## 2026-09-22 — Task 8 checkpoint

- PR #52 merged as `d6821ddb0773b586b6a106b66b2e18154c90cc7a`.
- local release validation now has one fail-fast wrapper: `bash scripts/release-check.sh`;
- the wrapper covers compile, Ruff, pytest, branch/local whitespace, built-artifact smoke and clean-demo smoke while explicitly leaving GitHub CI authoritative;
- the clean demo no longer creates or deletes the repository's developer `.venv`; its project virtualenv lives under the temporary demo root;
- Task 6 audit has one demonstrated documentation drift ready for the next slice: `runtime_doctor` exists in the bridge protocol/executor/server but is omitted from README and the public bridge supported-action list;
- private watcher/recovery state was not re-probed in this batch.

## 2026-09-22 — current reconciliation checkpoint

Current public GitHub state:
- `main` includes PR #46 installer/operator robustness, PR #47 secure-I/O inventory, PR #48 self-update durability fsync hardening, PR #49 safe diagnostics contract, PR #50 CLI removal-confirmation deduplication and PR #51 reconciled self-update recovery visibility.
- PR #51 merged as `011fcbfec4e0b75a93820ca1c4c487111da6b495` after current-main CI passed Ruff, 773 pytest tests, whitespace validation, clean demo and built release artifact.
- stale PR #45 was closed unmerged after its functionality was rebuilt on current main in #51.
- there are no open Runner-MCP pull requests at this checkpoint.
- self-update transaction and installed-state markers now flush/fsync the file before replace and fsync the parent directory after replace.
- local `status` exposes install recovery only as `clear`, `REQUIRED` or `INVALID`; `doctor` warns/fails on pending/invalid recovery without exposing transaction details.
- watcher/notifier/supervisor diagnostics now have a category-only safe contract; production logging integration remains a separate later slice.
- ordinary REMOVE-style CLI confirmations share one narrow helper; emergency-stop, approval, watcher-recovery and self-update-recovery confirmations remain separate.

Agent-capacity policy:
- analysis/design-heavy Claude work is marked `CHAT REVIEW` and should be done in normal Claude chat rather than Claude Code;
- ChatGPT is the default implementer for CODE work unless explicitly reassigned;
- a Claude rate limit never blocks the critical path.

Private runtime state was not re-probed during this GitHub-only reconciliation. The prior handoff's degraded watcher/recovery-attention observation therefore remains historical/last-known, not a newly verified current fact.

## Controlled multi-project concurrency — 2026-09-21

Bounded fair multi-project concurrency is merged and validated. Runner MCP now separates mailbox acceptance from durable test execution, maintains fair logical per-project queues, returns immediate job IDs, exposes safe queue/worker/job state, and keeps same-project overlap opt-in only. High-risk mailbox actions remain excluded.

The authenticated MCP request limit was also raised from 60 to a still-bounded 600 requests per minute so concurrent mailbox workers and normal status polling do not hit a transport bottleneck before worker or queue capacity. Test-worker, project-lock and queue limits remain independent safety controls.

## Shared watcher migration proof — 2026-09-21

A private deployment has been migrated from the pilot poller to the shared `runner-mcp github-watcher run` runtime. The watcher was explicitly bootstrapped at the current request head, so historical mailbox entries were not replayed. After fresh requests and a package restart, the private cursor matched the request head, the replay ledger contained only completed records, and the heartbeat reported healthy with zero recovery attention.

Live protocol-v1 checks completed for `project_status`, `project_capabilities`, `list_test_profiles`, `queue_status` and `worker_status`. A real predefined test request was accepted asynchronously and later reached a terminal passed state through `job_status`. During that proof, the MCP SDK's multi-item encoding for list-returning tools exposed a compatibility gap; the loopback executor was hardened to accept bounded object-only multi-item list results while scalar tools remain fail-closed.

The legacy private poller is disabled in that deployment. Completion-notification transport remains an independent capacity concern and is not part of mailbox execution authority.

# Current state

Date: 2026-09-21

## Status

Runner MCP Phases 0 through 9 and Phase 3.9 launch-readiness are merged to main. Phase 3.7 formalizes the GitHub mailbox transport; Phase 3.8 adds bounded results and replay protection. Phases 3.8.1 through 3.8.7 add completion events, restart safety, the transport-neutral processor, hardened GitHub transport, incremental watcher coordination, the loopback MCP executor and private-config watcher runtime. Phase 3.8.8 adds bounded fair multi-project concurrency. The shared watcher runtime has now also been proven in a private deployment with explicit bootstrap, restart-safe cursor/replay recovery, bounded concurrent request handling, strict result publication and asynchronous test-job follow-up. GitHub remains the source-code surface, while Runner MCP remains the local execution and safety boundary.

Phase 0:
- repository structure defined;
- public infrastructure-data ban documented;
- security baseline drafted;
- threat model drafted;
- example project configuration added;
- public example safety tests added;
- manual privacy scan clean.

Phase 1 foundation:
- MCP server skeleton added;
- bearer-token verification hook added;
- health endpoint added;
- project registry added;
- `list_projects` added;
- `project_status` added;
- append-oriented audit logging added;
- per-request IDs added;
- bounded in-memory rate limiting added;
- health endpoint exempted from operator rate limiting;
- unauthenticated MCP requests verified to fail closed;
- project roots/repositories/services validated before use;
- DNS-rebinding protection bound to the private runtime MCP resource URL;
- authenticated MCP handshake and tool discovery verified end-to-end.

Phase 2 safe file access:
- `read_project_file` added with bounded line pagination;
- `list_project_files` added with bounded non-recursive listing;
- `file_metadata` added without exposing configured root paths;
- absolute paths, traversal, backslashes and symlinks rejected;
- secret paths such as environment files, keys and database artifacts blocked;
- binary/private-key content blocked;
- known literal secret values redacted;
- file-size, line-count and directory-entry limits enforced;
- MCP-level allowed/denied file reads and audit behavior tested end-to-end.

Phase 2.5 operator safety:
- external operator-stop file policy added;
- future operator actions fail closed until stop mechanism is configured;
- future operator actions remain read-only until retention values are explicitly confirmed;
- `safety_status` exposes safety state without returning private paths;
- code-release cleanup requires both count and age thresholds;
- default proposal is 20 releases and 90 days;
- PITR and pre-migration backup retention are separate controls;
- one approved code rollback may move back exactly one release;
- database restore always requires explicit approval;
- automatic production database restore is prohibited;
- operator-safety rules documented for later test/deploy/migration phases.

Phase 3 controlled test execution:
- private predefined test-profile schema added;
- MCP clients select only project and profile name, never a command string;
- executables must be absolute and are launched with `shell=False`;
- unsafe working-directory traversal and process-control environment variables are blocked;
- asynchronous jobs expose safe status, cancellation and paged scrubbed logs;
- per-project and global concurrency are bounded;
- test timeout and log-size limits are enforced;
- external operator stop terminates running test process groups;
- unfinished jobs are marked interrupted after Runner MCP restart;
- job metadata/logs use restrictive permissions;
- environment secrets, project paths and absolute command paths are scrubbed from logs;
- MCP lifecycle from `run_tests` through `test_status` and `get_test_log` is tested end-to-end;
- test-code trust boundary is documented; untrusted public-fork code remains excluded until stronger isolation exists.

Phase 3.5 onboarding:
- installable `runner-mcp` console command added;
- non-root `install.sh` added;
- interactive setup supports safe local mode and explicit public mode;
- generated private config uses restrictive filesystem permissions;
- inherited shell variables do not override setup-managed private runtime config;
- setup overwrite preserves the existing bearer credential unless `--rotate-token` is explicit;
- `status`, `doctor`, `emergency-stop` and `serve` commands added;
- project add/list/remove commands added without manual YAML editing;
- test-profile add/list/remove commands added;
- pytest and Ruff presets auto-detect project virtual environments;
- custom executable and project paths reject symlink components;
- project config updates are lock-protected and atomic;
- user-first README and QUICKSTART added.


Phase 3.7 GitHub mailbox bridge protocol:
- public infrastructure-neutral architecture and usage guidance added;
- versioned JSON requests are size-bounded and reject duplicate keys;
- request fields are strict and unknown fields fail closed;
- only list_projects, safety_status, project_status, project_capabilities, list_test_profiles and run_tests are allow-listed;
- no shell, executable, filesystem path, environment, service or arbitrary MCP tool may be supplied through the protocol;
- migration, deployment, rollback and restore remain outside the mailbox bridge and keep their existing approval boundaries;
- reusable public protocol logic is separated from private watcher credentials and infrastructure configuration.


Phase 3.8 bridge result envelope and replay protection:
- strict protocol-v1 result envelopes added for completed and failed operations;
- result payload size, nesting, collection count and string length are bounded;
- unknown result fields and duplicate JSON keys fail closed;
- sensitive result keys and absolute locations/URLs are conservatively redacted;
- failed results use bounded safe error codes instead of arbitrary raw process or exception output;
- canonical SHA-256 request fingerprints added;
- local replay ledger stores only request ID, fingerprint, allow-listed action and first-seen timestamp;
- duplicate identical requests are detected and must not execute again;
- reusing an existing request ID with changed content fails closed;
- corrupt, oversized, capacity-exhausted and symlinked replay-ledger states fail closed;
- replay ledger files are restricted to the service account;
- an initial umbrella project identity and a free public-launch-readiness plan were added without changing Runner MCP's product identity or security boundaries;
- public CI validates pull requests and main on a fresh standard GitHub-hosted runner with read-only repository permissions, pinned official actions and no private secrets; standard runners are free for this public repository.


Phase 3.9 public launch readiness:
- README now leads with a concise problem statement, architecture and safety boundary;
- the umbrella identity remains secondary; Runner MCP retains its own product/package identity;
- five-minute local evaluation demo added alongside the full Quickstart;
- root security-reporting policy added;
- public changelog and release checklist added;
- factual launch copy prepared without publishing external posts;
- privacy-safe bug and feature request forms added;
- pull-request template reinforces security invariants and public-repository hygiene;
- package metadata expanded for future public distribution;
- launch-readiness gate explicitly tracks what is complete and what still needs clean-environment/release verification;
- no marketing telemetry or paid runtime dependency added.

Service auto-start packaging — 2026-09-21:
- fixed local CLI management for the Runner MCP server, shared GitHub watcher and completion watcher;
- systemd user services remain preferred when a usable user bus exists;
- a managed cron backend is available for headless accounts without a usable user bus;
- the cron backend uses a marked private-user crontab block and per-component file locks; it executes only fixed Runner MCP argv and never accepts a shell command;
- unmanaged pre-existing Runner MCP cron entries make installation fail closed to prevent duplicate supervisors;
- the server remains loopback-only and no generic service/unit/cron command can be supplied by a remote client;
- optional watcher supervision requires private configuration plus explicit bootstrap state before installation;
- generated autostart state contains no credentials; foreign systemd units and unrelated cron entries are preserved;
- safe status reports only backend plus component installed/enabled/active state.

Test runtime hardening — 2026-09-21:
- local PostgreSQL validation exposed that the existing per-job `TMPDIR` could make Unix-domain socket paths exceed the platform limit when the private jobs root is long;
- Runner MCP now allocates a short, unique 0700 temporary directory below the fixed system temp root for each test job;
- the short temp path is included in private-path log scrubbing and removed after the job terminates;
- this is project-neutral and does not add environment passthrough or project-specific command authority.

Phase 3.8.1 task-completion feedback:
- strict terminal completion events added for succeeded, failed and cancelled outcomes;
- deterministic event IDs provide notification deduplication without exposing private source identifiers;
- completion source and operation are fail-closed bound;
- test completion requires a safe predefined profile identifier;
- attention state is derived from the terminal result;
- event parsing rejects unknown fields, duplicate keys, non-standard JSON constants and oversized payloads;
- completion payloads exclude paths, hosts, URLs, credentials, environment values, service names and raw logs;
- execution replay protection remains separate from notification deduplication;
- notification transport failure may be retried but must never rerun the completed task;
- public completion contract is transport-neutral; private destinations remain private configuration;
- built-in completion delivery now observes persisted terminal test jobs, uses deterministic event markers plus a private delivery ledger, and has a live exactly-once private proof; it no longer depends on repository-specific self-hosted Actions capacity.

Fail-closed mailbox recovery — 2026-09-21:
- exact claimed/completed requests missing a durable result can be locally resolved to terminal `RECOVERY_REQUIRED` without invoking the executor;
- a strictly valid unclaimed request can be locally abandoned to terminal `OPERATOR_ABORTED` without execution;
- a malformed historical request can be quarantined only when every sibling request in the current backlog already has a matching durable result and the request head remains unchanged;
- the raw recovery fetch is bounded and fixed-path; normal watcher processing remains strict protocol-v1 parsing;
- a live malformed legacy `sync_project` request was quarantined after 40 sibling requests were verified durable/completed, restoring heartbeat to healthy with zero replay;
- no replay-ledger reset, cursor reset command, request deletion or blind task retry exists in these recovery paths.

Phase 3.8.2 watcher resilience and restart recovery:
- replay entries now carry an explicit claimed/completed lifecycle;
- legacy replay entries without state are treated conservatively as claimed;
- completion is recorded only after a safe result is durable;
- restart classification distinguishes process, result-exists, ambiguous-claim and result-missing states;
- ambiguous or missing-result work is never automatically re-executed;
- public heartbeat exposes only healthy/backlog/degraded plus bounded counts and oldest-pending age;
- request IDs and infrastructure metadata are excluded from heartbeat output;
- stale thresholds and observation counts are bounded;
- duplicate pending observations fail closed;
- transient transport retries are bounded and limited to timeout/rate-limit/unavailable failures;
- authorization and invalid-response failures are not automatically retried;
- watcher resilience and task-completion notification remain separate concerns.

Phase 3.8.3 transport-neutral bridge processor:
- request parsing and replay claim are enforced before execution;
- completed duplicate requests never execute again;
- claimed duplicates become an ambiguous recovery state;
- executor interface exposes only the six mailbox-allow-listed actions;
- run_tests is represented as an explicit run_tests_to_completion(project, suite) operation;
- executor exceptions are converted to generic safe failure envelopes;
- unsafe executor output fails closed as UNSAFE_RESULT;
- only scrubbed/bounded serialized results reach the transport sink;
- durable result persistence precedes replay lifecycle completion;
- persistence/finalization failures require recovery and never authorize action replay;
- GitHub credentials, branches, endpoints and supervisor configuration remain outside the public processor.

Phase 3.8.4 hardened GitHub mailbox transport:
- fixed GitHub API host; no caller-supplied endpoint;
- safe repository/ref/token shape validation;
- fixed request/result/heartbeat mailbox locations;
- bounded API response and mailbox entry counts;
- strict GitHub JSON rejects duplicate keys and non-standard constants;
- wrapped base64 is accepted only after validation;
- request payload ID must match its filename;
- results are create-once and idempotent only for identical existing content;
- conflicting result content fails closed;
- all result read/write transport failures enter the BridgeProcessor persistence-recovery boundary;
- heartbeat publication is bounded and validated;
- HTTP/network failures are safely classified without raw response leakage;
- transport uses the Python standard library and adds no paid runtime dependency.

Phase 3.8.5 incremental watcher coordinator:
- bounded transient GitHub retries only for timeout/rate-limit/unavailable failures;
- fast-forward request discovery from a private local cursor;
- no historical replay on first start; bootstrap is explicit;
- cursor file is 0600, lock-protected and refuses symlinks;
- cursor advancement uses an expected previous SHA to detect concurrent watchers;
- existing durable results are reconciled without action execution;
- claimed or completed requests missing results never execute again automatically;
- persistence/finalization recovery leaves the cursor behind for safe reconciliation;
- malformed request changes fail closed and block cursor advancement;
- heartbeat publication stays independent of completed task execution;
- heartbeat delivery failure cannot cause an action replay;
- non-request commits advance the cursor without creating fake work.

Phase 3.8.6 loopback MCP bridge executor:
- local MCP endpoint is restricted to loopback HTTP(S) and the exact /mcp path;
- URL credentials, query strings and fragments are rejected;
- bearer token, MCP session ID and test job ID values are bounded/validated;
- MCP response bytes and JSON/SSE parsing are fail-closed;
- raw transport/server/tool errors are not exposed through bridge results;
- public executor exposes only the six mailbox bridge operations;
- generic MCP dispatch remains private and internally allow-listed;
- run_tests uses internal test_status polling only until terminal state;
- test logs are never fetched by the bridge executor;
- terminal run_tests output contains only project, suite and status;
- polling and total wait durations are bounded.

Phase 3.8.7 private-config watcher runtime and CLI:
- private GitHub repository/refs/token are stored only in the 0600 runtime environment;
- mailbox configure/status/remove use existing atomic private-config locking;
- status output never returns repository, refs or token;
- token entry uses a hidden prompt and there is no token CLI argument;
- setup overwrite preserves DB and mailbox secrets, including during bearer-token rotation;
- private replay/cursor files are derived inside the private config directory;
- explicit watcher bootstrap skips historical requests;
- one-cycle watcher output is limited to safe state/counts;
- continuous watcher polling and heartbeat cadence are separately bounded;
- heartbeat is slower than request polling by default and is refreshed on state transitions;
- heartbeat failure remains independent from completed action execution.

Phase 3.8.9 bounded operational bridge:
- the mailbox action enum now reaches existing configured service, backup, migration, deployment and rollback capabilities through explicit methods only;
- test-log retrieval is bounded to 100 lines per request and remains subject to test-runner redaction plus bridge-result scrubbing;
- service mutations accept only configured service aliases and preserve per-alias opt-in plus emergency-stop enforcement;
- backup creation uses only configured database state; no DSN/path/command input is accepted from the mailbox;
- migration/deploy/rollback plans can be requested and inspected remotely, but approval granting remains local/human-controlled;
- apply/deploy/rollback execution requires a valid pre-approved opaque approval ID and cannot bypass action/project/binding/expiry checks;
- deployment/rollback status accepts only validated opaque job IDs;
- restore/PITR, production mutations, arbitrary shell/argv/path/env/unit/tool input remain unavailable.

Phase 4 staging service management:
- private service aliases map to systemd-user units;
- service aliases default to read-only;
- start, stop and restart permissions are independently opt-in;
- MCP list/status output never exposes private unit names or health URLs;
- optional HTTP health checks return only safe health state;
- operator emergency stop blocks mutating service actions while status stays available;
- systemctl invocation uses fixed argument arrays with `shell=False`;
- raw systemctl failure output is not returned to MCP;
- no sudo or generic system-service control;
- CLI service-config add/list/remove avoids manual YAML editing;
- MCP list/status/restart/emergency-stop flow is integration tested.

Phase 5 PostgreSQL backup and migrations:
- private DB connection strings use dedicated `RUNNER_MCP_DB_*` variables;
- CLI database connection input is hidden and never echoed;
- setup overwrite preserves existing DB secrets;
- backup root/project directories and dump/metadata files have restrictive permissions;
- pg_dump receives the DSN via child environment and not command-line arguments;
- MCP exposes backup metadata only, never dump contents or private paths;
- migration status/apply use predefined argv arrays and `shell=False`;
- migration output is bounded and scrubbed for DSN/private paths/secrets;
- apply always creates a pre-migration backup and rechecks operator stop afterwards;
- migration failure keeps the backup and never performs automatic restore;
- database restore, PITR/WAL orchestration and retention pruning remain intentionally unimplemented.

Phase 6 staging deployment:
- staging-only deployment config with private release storage;
- clean Git HEAD is the only deployment source;
- client cannot supply arbitrary Git ref or build shell;
- Git hooks/fsmonitor disabled during preflight/archive operations;
- required tests run before release creation and source cleanliness is rechecked;
- repository symlinks are rejected from release archives;
- optional database migrations use the Phase 5 pre-migration backup flow;
- current-release activation uses an atomic symlink replacement;
- service restart requires a configured health check;
- activation failure auto-rolls code back one release only when no DB migration ran;
- post-migration activation failure requires manual recovery and never auto-restores DB;
- deployment jobs are asynchronous, private, persisted, and marked interrupted after restart;
- MCP plan/start/status lifecycle is integration tested;
- deployment config is manageable by CLI without exposing release paths.

Phase 7 controlled rollback:
- release history exposes safe metadata, retention protection and rollback eligibility;
- retention protection uses both minimum count and minimum age;
- release metadata identity/commit/timestamp/environment/permissions are fail-closed validated;
- rollback target is always the direct previous release from trusted metadata;
- unknown MCP tool arguments are globally rejected;
- current releases that applied DB migrations block code rollback;
- rollback runs as a persisted async job sharing the per-project deploy/rollback exclusion;
- successful rollback restarts and health-checks the configured service;
- failed rollback health reactivates the original current release when the stop is not active;
- no database restore, arbitrary target, production rollback or automatic cascade.

Phase 8 adapter foundation:
- built-in allow-listed adapter registry with no dynamic imports from config;
- generic adapter never guesses commands or automatic presets;
- Python adapter inspects safe local markers/tooling without returning paths;
- project adapter IDs are validated fail-closed;
- CLI and MCP can list adapters and inspect safe project capabilities;
- `auto` resolves only to existing allow-listed test/migration presets;
- named private/company project adapters remain outside the public repository.


Phase 9 human approval gates:
- migration, deployment and rollback require short-lived human approvals;
- MCP can request/inspect plans but cannot approve them;
- approval is local CLI only with explicit confirmation phrase;
- approvals are action/project/plan-bound, short-lived and single-use;
- migration approval binds a clean Git HEAD;
- deployment and rollback jobs are pinned to their approved commit/release targets;
- production project mutations are blocked; staging remains the only mutable environment;
- AIfordable-owned Agent Bus is the required primary runtime control path;
- GitHub mailbox is bootstrap/fallback only and must be independently disable-able;
- Desktop Commander remains break-glass only;
- optional third-party client tunnels do not become control authority.

## Validation

Current validation is green:
- Python 3.12 compile: green;
- Ruff: green;
- pytest: green in current CI; exact test counts are recorded with dated validation/release evidence rather than treated as durable status here;
- merged request-capacity change passed public CI including whitespace checks;
- live private bridge validation passed both Runner MCP lint and unit profiles;
- git diff whitespace check: green;
- HTTP auth/rate-limit tests: green;
- authenticated MCP handshake/tool-discovery test: green;
- unexpected Host rejection test: green;
- traversal/symlink/secret/binary/size/pagination file tests: green;
- MCP file-read allow/deny integration test: green;
- operator-stop/retention/rollback guard tests: green;
- startup fail-closed retention-confirmation tests: green;
- MCP safety-status integration test: green;
- controlled test-runner timeout/cancel/stop/concurrency/log-redaction tests: green;
- MCP test-job lifecycle integration test: green;
- test-profile schema and startup fail-closed tests: green;
- dependency check: green;
- non-root installer integration test: green;
- installed console command version/help smoke test: green;
- project-aware guide smoke test: green;
- GitHub mailbox bridge protocol validation tests on merged Phase 3.7: green;
- live private mailbox probe for the configured runner-mcp test-profile listing: green;
- isolated Phase 3.8 result-envelope/replay logic checks: green;
- full Phase 3.8 branch CI on the free standard runner for this public repository: green;
- operator-wrapper installer tests: green;
- onboarding/project/test-profile CLI tests: green;
- service manager permission/emergency-stop/subprocess tests: green;
- MCP service alias/status/restart integration test: green;
- service-config CLI/config-manager tests: green;
- PostgreSQL backup/metadata/permissions/secret-isolation tests: green;
- migration timeout/failure/pre-backup/redaction tests: green;
- MCP database backup/migration/emergency-stop lifecycle test: green;
- database-config and hidden-prompt CLI tests: green;
- staging release/git cleanliness/symlink/test/migration/health rollback tests: green;
- deployment job persistence/interruption/error-sanitization tests: green;
- deployment-config storage/validation/CLI tests: green;
- MCP asynchronous deployment plan/start/status/emergency-stop test: green;
- release listing/metadata-tamper/migration-boundary rollback tests: green;
- rollback job persistence/blocking tests: green;
- MCP one-step rollback/list/plan/status and arbitrary-target rejection test: green;
- adapter registry/inspection/symlink-safety tests: green;
- adapter auto-preset/config validation tests: green;
- CLI and MCP adapter capability tests: green;
- approval expiry/replay/action/project/fingerprint/permission tests: green;
- clean-Git high-risk source binding tests: green;
- production mutation gate tests: green;
- local approval CLI explicit-confirmation test: green;
- MCP approval request/consume migration/deploy/rollback flows: green;
- git diff whitespace check: green;
- private-address/path scan: clean.

## Deliberately not implemented yet

- arbitrary shell;
- production actions;
- database restore;
- PostgreSQL WAL/PITR orchestration;
- automated backup-retention pruning;
- production deployment;
- production rollback;
- arbitrary/multi-step automatic rollback target selection;
- automatic database restore;
- automatic release pruning.

## Next steps

The shared watcher migration, restart/reconciliation proof, exactly-once completion-notification proof, clean-Linux five-minute demo validation and non-root systemd user autostart packaging are complete. Keep obsolete pilot execution paths disabled, continue guided private-connectivity/TLS onboarding, and prepare the first tagged alpha only from an exact green commit.

Before activating real project test/service/database/deployment profiles, create the private runtime configuration and verify Linux-account, service-health and PostgreSQL recovery boundaries on the actual host.

Do not add real environment values to this repository.


## Safe project sync and adapter test presets — 2026-09-21
- Added a narrow `sync_project(project, commit)` mailbox capability for staging validation. The request accepts only an allow-listed project code and a full 40-character commit ID.
- Source sync requires a clean worktree, blocks submodules, validates that `origin` is exactly the configured GitHub repository, fetches with Git hooks disabled and terminal prompting off, verifies the commit is reachable from `origin/*`, and checks out the exact commit detached.
- Source sync refuses to run while that project's tests are queued or active. No branch, remote, filesystem path, executable, command, service or environment variable can be supplied by the mailbox.
- Python projects now expose fixed safe adapter presets `pytest` and `ruff` when the required executable is detected in `.venv/bin` or `venv/bin`. Configured profiles still take precedence.
- Adapter presets use fixed argv/cwd/env/timeout definitions. `custom` is deliberately excluded from implicit mailbox availability.
- Added protocol, executor, source-control and test-runner regression coverage for commit pinning, extra-field rejection, busy-project rejection, safe preset discovery/execution and custom-preset denial.
- This change does not enable migration, deployment, rollback, arbitrary shell or arbitrary Git ref execution through the mailbox.

Runtime observability bridge — 2026-09-21:
- added fixed read-only `runtime_status` and `runtime_doctor` MCP/bridge actions;
- output is intentionally host-neutral: version, safe capacity/configuration booleans and bounded check summaries only;
- private paths, endpoints, hostnames, environment values, service units and raw process output remain excluded;
- this is the first self-operations step toward removing routine dependence on general-purpose remote desktop tooling.

Shared Playwright runtime — 2026-09-21:
- Runner MCP E2E jobs previously replaced HOME and therefore could not see a shared Playwright/Chromium cache unless it was passed through manually;
- test profiles can now declare `runtime: playwright`;
- the browser cache comes only from private `RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH`, is locally validated and is scrubbed from logs;
- missing or unsafe browser runtime fails closed; PastEntrance does not need a project-code workaround for this boundary.

Runner MCP self-update — 2026-09-21:
- added fixed `self_update(commit)` and `self_update_status(job_id)` operations for the configured canonical Runner MCP project;
- commits are lowercase full object IDs and must be reachable from `origin/main`; direct MCP calls and mailbox calls enforce the same lowercase boundary;
- lint and unit profiles gate installation, and the source commit is rechecked immediately before the fixed local install;
- server, GitHub watcher and completion watcher use component-specific restart/reexec paths; callers cannot choose executables, commands, services or paths;
- private job/state/restart metadata is permission-restricted and restart recovery marks unfinished update jobs interrupted rather than replaying them;
- the current read-only `runtime_status` and `runtime_doctor` behavior is preserved, with self-update readiness/state added to runtime status;
- the local MCP bridge allow-list now explicitly includes both observability actions as well as the two self-update actions, closing the gap where protocol support existed but local dispatch could still reject runtime observability;
- arbitrary package-manager arguments, repositories, refs, paths, environment values, process controls and general remote-shell behavior remain excluded.


Self-update hardening follow-up — 2026-09-22:
- review of PR #37 found and fixed three integration gaps before merge: local MCP dispatch had not allow-listed runtime observability, the direct self-update capability normalized uppercase commits instead of rejecting them, and `self_update_status` was present in the enum/mapping but missing from strict request validation;
- the self-update source is now guarded across post-sync verification, lint, unit and install, closing the window where another source sync could change the checkout between validation steps;
- the project source guard was made re-entrant so the self-update orchestration can hold it while existing test-start/install paths safely re-enter it;
- PR #37 merged as `8570f842ffad5282bb28a89a77bcbcba5dd01bcd` after clean five-minute demo, built-artifact validation, Ruff and 704 pytest tests all passed.

Self-update activation recovery — 2026-09-22:
- follow-up work makes restart intent durable across fixed-component re-exec failure rather than consuming the marker before an unsuccessful activation;
- restart markers now cover server, GitHub watcher and completion watcher, are create-once and are batch-prepared so partial marker creation is rolled back;
- a new self-update is refused while any fixed activation marker remains pending;
- runtime status exposes only a boolean pending state and bounded fixed-component count, not paths/process identifiers;
- server self-reexec retries are bounded; watcher/notifier re-exec failure restores the marker so managed systemd/cron supervision can retry after process restart;
- failures after package installation are distinguished as activation failures with restart required, while pre-install failures remain ordinary self-update failures;
- package-install rollback remains a separate future hardening item; this slice improves activation recovery without claiming atomic package rollback.

Activation recovery merged — 2026-09-22:
- PR #40 merged as `1d160afdb9c0b6e0d3ebb3a74b88644b84eb348e`;
- validation was fully green: Ruff, 708 pytest tests, clean five-minute demo and built-release artifact;
- fixed-component restart intent now survives a failed re-exec, pending activation blocks overlapping self-updates, and runtime status reports only a bounded pending state/count;
- issue #7 (mailbox liveness/stale-request recovery) was closed as completed because its heartbeat, retry and fail-closed recovery scope is already implemented and live-proven;
- next self-update hardening target is package-install rollback/staging; current activation recovery does not claim atomic recovery from a failed in-place pip installation.


## 2026-09-22 — external review triage and low-risk cleanup

Claude's read-only review branch `claude/roadmap-review-suggestions-xxbhfo` was evaluated against the newer main baseline rather than merged wholesale. The review branch was based on `319259c7...`, before the commit-pinned self-update and recoverable activation work, so its exact test counts and some roadmap observations were already stale.

Accepted low-risk findings in this slice:
- gate the demo-smoke and release-artifact CI jobs on the main validate job so obviously invalid commits do not spend extra runner time;
- expose the validation workflow status from README and clarify that the operator wrapper is unnecessary for same-account installs;
- define status authority explicitly: roadmap for architectural phase status, handover for chronology, CI/release records for exact validation results;
- reconcile stale roadmap "Next" items that still described watcher migration, coordinator integration, completion proof and self-operation work that is already implemented;
- add direct unit coverage for the append-only audit logger and its 0600 file-permission contract.

Deferred rather than applied blindly:
- a shared `secure_io` rewrite: worthwhile, but the existing atomic/private-write call sites have different lifecycle and failure semantics, so this needs an inventory plus dedicated regression tests rather than a mechanical replacement;
- a generic audited-tool decorator: potentially useful, but audit payloads and failure categories differ by tool family and should not be homogenized without a separate design/test slice;
- watcher `logging`: operationally useful, but must first define a scrubbed, category-only logging contract so diagnostics cannot become a new private-data leak;
- large `server.py`/`cli.py` splits and adapter plug-in discovery: maintenance work, not current safety or self-update blockers;
- a full roadmap status table: not added because it would duplicate per-phase status and create another drift surface. The source-of-truth rule and stale-status cleanup address the underlying problem with less duplication.

The next functional priority remains the staged/rollback-capable self-update package-install strategy, plus live bootstrap/proof on the private host when that host can be upgraded through an available safe path.


Review cleanup merged — 2026-09-22:
- PR #41 merged as `0e66368ca1377359019de1d594833377892db7aa`;
- validation: Ruff and whitespace checks green, pytest 711 passed with one known third-party warning, clean demo green, built release artifact green;
- Claude's review branch remains unmerged by design; only independently revalidated low-risk findings were adopted;
- next functional target remains staged/rollback-capable self-update installation plus live private-host bootstrap/proof.


Self-update package-install recovery hardening — 2026-09-22:
- PR #43 stages the validated target as a private wheel instead of installing directly from the checkout;
- when a known installed baseline exists, a private recovery wheel is built before source sync while the project source guard remains held across baseline staging, target sync, lint/unit validation, target staging and package mutation;
- a strict private 0600 install-transaction marker is persisted before the in-place pip operation; pending recovery is exposed only as a bounded boolean and blocks overlapping self-updates;
- target installation must also pass a fresh-process Runner MCP import verification;
- a caught target install/import failure rolls back only when both baseline-package reinstall/import verification and exact baseline source restoration succeed; otherwise the transaction remains fail-closed as `install_recovery_required`;
- same-commit self-update requests still verify reachability through `origin/main` and then avoid unnecessary reinstall/restart;
- clean CI exposed that offline `--no-build-isolation` wheel staging requires the setuptools build backend to remain available at runtime, so `setuptools>=75` is now an explicit runtime dependency; this dependency-set change reinforces that the first private-host bootstrap must use the normal dependency-resolving installation path;
- the current design deliberately does not claim atomic in-place pip mutation. A process interruption can leave an install transaction pending; the next hardening slice is a bounded local recovery command before live package-install fault injection.


Package-install recovery merged — 2026-09-22:
- PR #43 merged as `2b7dac9fb3c9e5168c07c7967333995b646957de`;
- final validation was fully green: Ruff, whitespace, 742 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- the source guard now remains held through installed-state persistence, restart-marker preparation and install-transaction finalization, closing a final post-install source-race window;
- the next hardening target is a bounded local operator recovery command for persisted install transactions; live package-interruption fault injection remains deferred until that local recovery path exists.


## 2026-09-22 — bounded local self-update install recovery

A local operator-only recovery path is being added for persisted rollback-capable self-update install transactions:
- `runner-mcp self-update-recovery` is local CLI only; it is not mapped into MCP or the GitHub mailbox;
- recovery requires the operator emergency stop to be active and exact confirmation `RECOVER SELF UPDATE`;
- only the private staged baseline wheel from the persisted transaction can be used;
- the installed package is reinstalled and import-verified, source is restored to the exact baseline commit reachable from `origin/main`, and installed-state metadata is reset to that same commit;
- the transaction is cleared only after all of those checks succeed; otherwise recovery remains pending and further self-update stays blocked;
- bootstrap/first-install transactions without a known baseline are deliberately not auto-recoverable;
- pending activation markers and install recovery are not allowed to overlap.


Local install recovery merged — 2026-09-22:
- PR #44 merged as `3ce122012d56ead3fbf75dfbf8fe770572f3ed47`;
- validation was fully green: Ruff, whitespace, 753 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- persisted rollback-capable self-update transactions can now be recovered only through local `runner-mcp self-update-recovery`, with the operator emergency stop active and exact confirmation;
- the recovery path restores the private staged baseline package, fresh-process import validity, exact baseline source commit and installed-state metadata before clearing the transaction;
- bootstrap/no-baseline transactions and overlapping activation recovery remain fail-closed;
- no install-recovery action was added to MCP or the GitHub mailbox;
- next: bootstrap this merged baseline on the private host and prove same-commit, forward-update and deliberately interrupted/recovered package-install paths through the safe operating model.

## Coordination checkpoint — 2026-09-22

Canonical coordination now uses `SESSION_HANDOFF.md`, `AGENT_EXCHANGE.md` and `RESUME_PROMPT.md`. GitHub live state wins over stale handoff text.

Immediate priority:
1. reconcile the four private watcher recovery-attention items without replay/reset shortcuts;
2. confirm the pending read-only runtime-status probe;
3. reconcile and, if still green/current, merge PR #45;
4. bootstrap/prove the newest recovery-capable self-update baseline on the private host.

Current blocker: watcher heartbeat is degraded by four recovery-attention items, so cursor advancement is intentionally withheld. Desktop Commander is unavailable; use GitHub plus the bounded Runner-MCP bridge.


## Agent Bus architecture correction — 2026-09-29

A GitHub primary-rate-limit incident proved that the mailbox cannot remain operationally primary.
The required target is now explicit: AIfordable-owned durable relay + outbound-only Runner Fabric
Agent Bus. GitHub remains source/CI during migration and later optional mirror/bootstrap/fallback.
Runner MCP #125/#130 and Runner Fabric #356 track the implementation and live cutover.
