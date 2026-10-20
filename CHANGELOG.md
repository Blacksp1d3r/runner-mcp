# Changelog

## 0.1.52 (source-only #669 active-generation update readiness fails closed)

- Prevent `runtime_status` from inheriting `self_update_ready=true` from a self-update transaction manager when the current loaded wheel/source and serving process remain unverified. Historical commit, git checkout, installed package version and manager readiness are not current-generation authority. Explicitly set update readiness to false alongside null active provenance; tests cover stale true/false/malformed manager data and hot-installed dist-info without process restart. Source only: this does not create any updater, trusted signer, A6/A7 journal or operational installation. (#669)


## 0.1.51 (source-only #669 canonical offline evidence paths)

- Reject relative, `..`-redirected or symlink-ancestor manifest/receipt/wheel/installed-package/generation paths before offline evidence-chain comparisons. Prevent a lexical `is_relative_to()` success from masking a redirected generation candidate; negative tests preserve fail-closed state and never claim active build identity. No host scanner or production install authority. (#669)


## 0.1.50 (source-only #669 installed RECORD negative admission)

- Limit extra pip-installed RECORD entries to the two declared Runner-MCP CLI scripts and standard pip metadata. Refuse arbitrary out-of-tree paths, duplicate console entries, malformed external digests and unbounded entries that were previously silently ignored by the offline source-vs-install comparison. Preserve legitimate pip extras and deliberately keep the resulting classification OFFLINE ONLY, never live attestation or update authority. (#669)


## 0.1.49 (source-only fixed A6 value integrity; not installed)

- In `runtime_doctor`, require exact fixed A6 configuration values, canonical already-qualified owner-private roots, plausible private bearer format and matching canonical Fabric revisions before returning `ready_11_of_11`. Eleven nonempty keys with a stale revision, wrong storage root/domain, loopback endpoint, probe target or secret format are no longer a green status. Synthetic regressions for each of eleven fixed keys, absent evidence directory, and correctly generated fixed values. This does NOT grant off-target A6 journal, independent A7 rollback, current loaded wheel/process proof or original-client ACK. (#509/#669)


## 0.1.48 (source-only A6 ancestor symlink hardening; not installed)

- Refuse symlinked *ancestors*, not only the final A6 private state/configuration directory, before canonical resolution. Also reject relative/parent-traversal lexical roots. A redirected grandparent must never cause an A6 journal/configuration read or the fixed 11-key private repair to be accepted. Add negative tests for state-root and config-parent aliases, traversal and no private writes; unchanged fixed binding authority. (#509/#669/Fabric #1617)
- The original connected central v0.1.38 remains unverified and unchanged. This source-only hardening does not prove off-target A6 storage, independent A7 rollback, a trusted currently loaded wheel or original requester ACK.


## 0.1.47 (source-only A6 diagnostic safety; not installed)

- Prevent `runtime_doctor` from reporting A6 unconfigured (0/11, absent journal/evidence roots) as PASS. Preserve safe non-mutating absence detail with WARN, classify malformed/private-root configurations fail-closed, and retain PASS for structurally complete private bindings only. Separate Fabric #942/#1617 off-target journal, A7 independent rollback and original requester ACK remain required for live update authority. This source correction does not modify private configuration, restart processes or install a wheel. (#509/#669)

## 0.1.45 (source-only candidate; release guard not yet branch-required)

- Implement fail-closed read-only GitHub current-main / PR-head / version admission for the unique next patch, with deterministic READY PR priority and twice-sampled contender inventory against races (#662). Reject wrong source/version, invalid API data and inherited proxy/redirect. Source CI alone cannot enforce merge atomicity: administrator-required check and fresh branch/serialized merges are separate gates. No live host release.

## 0.1.44 (source-only candidate; not deployed)

- Add independently pinned Ed25519 signed serving-witness input validator (#669), with exact host, source, wheel, generation, nonce, role instances, expiry and signature checks. Even a valid signed statement is OFFLINE and cannot establish current loaded host/process provenance or trigger update. No signing issuer, credential, live host observation or rollback authority.

## 0.1.43 (source candidate; not installed)

- Add bounded inert fixed GitHub Release asset-ID byte verifier (#739/#745), with no inherited proxy, exact size and independently supplied SHA256; allow strict direct 200 or narrowly authorized 302 with credentials stripped. Source-only security tests; never a full 33/33 signed importer, immutable storage, service activation, private host permission or Agent Bus ACK.

## 0.1.42 (source candidate; not deployed)

- Add operator-interactive pinned, standalone read-only GitHub Release metadata probe for first-host Fabric access (#739). Restricts repo/tag, disables proxies/redirects, bounds response, checks expected metadata and secret-safe category outputs. Offline security regressions. Neither release asset integrity, local custody, host activation nor original requester ACK is proven; no host action.

## 0.1.40 (source candidate; not published)

- Contain missing/invalid active-revision provider metadata errors as unknown rather than a runtime diagnostic tool error; preserve failed self-update activation and historical baseline guards (#669 / PR #742).
- Fail closed on malformed/unclean source checkout baseline evidence instead of accepting a coercible pseudo-commit or leaking a provider error (RMCP-F-0046, #669).
- Record explicit read-only, independently trusted serving-generation provenance acceptance design. This is not yet live wheel/host attestation or a manual-baseline reconciliation and grants no update/rollback authority.

## 0.1.39 (source candidate; not published)

- Add an optional **already configured project ID** to existing known-project preflight/prepare so mixed staging roots can select a safe destination without exposing filesystem paths. Keep no-anchor refusal and refuse second exact clone on another parent (#740). This does not register/deploy EnerCue, start Claude/Qwen, or relax Agent Bus admission.

## 0.1.38 (source candidate; not published)

- First-host Agent Bus read-only status identifies genuinely absent private base setup as `base_config_not_initialized` without making credentials, opening ports or weakening partial/unsafe config refusals (#735).

## 0.1.37 (source candidate; not published)

- Prevent direct operator-local recovery CLI inspect/finalize from creating Python import bytecode in a pinned source checkout; add ordinary-Python subprocess regressions without automatic stage recovery or service activation (#732).

## 0.1.36 (source candidate; not published)

- Mask complete variable-length GitHub App installation/access token families in bounded logs, including opaque URL-safe separators that the previous alphanumeric-only regex left partially visible. Regression tests cover `ghs_`, other GitHub token prefixes, truncated input and benign short strings. No real provider secrets or log data used; installed runtime unchanged (#730).

## 0.1.35 (source candidate; not published)

- Add a read-only, fixed-repository GitHub Releases asset attestation for Fabric offline bundles. Require exact tag/SHA and tag ref, 5-160 distinct bounded asset IDs/names/sha256 digests and mandatory source manifests. All queries are metadata-only; no URL follows, binary download, local archive writes, runner privileges, service upgrades or Claude dispatch. Existing Actions-artifact update route remains unchanged; an separately authorized custody importer must follow before any release install.

## 0.1.34 (source candidate; not published)

- Recover owner-held nested 0775/0664 pip/setuptools files only when protected by an independently checked owner-only 0700 private ancestor. Refuse shared parent/stage boundary, foreign ownership, symlinks and generated hardlinks; never chmod or reinstall an existing failed stage (#723).

## 0.1.33 (source candidate; not published)

- Automatically verify the actual fresh isolated Python 3.12 venv and pip >=23.2 before first-host stage prefix creation; missing Ubuntu Python venv packages produce a bounded denial without an unusable partial installation (#726).

## 0.1.32 (source candidate; not published)

- Add operator-local, fail-closed, manifest/host/source-bound recovery for intact previously blocked stages. Verify installed Python against immutable Git archive, wheel RECORD and CLI integrity, require explicit recovery-digest confirmation; no installer retry, activation, relay enrollment or ACK (#723).

## 0.1.31 (source candidate; not published)

- Isolate first-host staged installer builds in a pinned private Git-archive copy so setuptools-generated `build/` and `*.egg-info` never dirty the trusted source checkout. Preserve strict second source/host/manifest gate, no activation, and no retry of failed physical stages (Runner-MCP #721).


All notable user-visible changes to Runner MCP will be documented here.

Runner MCP is under active development. New changes remain under **Unreleased** until an exact validated commit is explicitly tagged and released.

## Unreleased

- Source candidate 0.1.30 (unreleased, never installed): rootless first-host bootstrap `diagnose --manifest` reads only the original failed stage's filesystem metadata, refuses unsafe path/host custody, emits allowlisted status without executing partial venv code or inferring pip functionality/host activation. Tracked under RMCP-F-0030 / #716 / #718; it cannot repair, retry, enroll or deploy Black.

- Source candidate 0.1.29 (not tagged, published or installed): local, unprivileged, operator-confirmed, SHA-pinned first-host staging bootstrap in scripts/managed_host_bootstrap.py. Uses existing install.sh; does not enroll a runner, start services, change disks or grant Fabric remote management. See docs/LOCAL_HOST_BOOTSTRAP.md and #713.

- Source package and MCP manifest versions advance to 0.1.4; this is a **pending candidate**, not a published release or deployment.
- Release guard prevents any source, tools, installer, scripts or workflow changes without a strictly higher version and matching metadata.

### Added

- local first-party ChatGPT/Codex plugin package rendering for the existing Runner MCP MCP
  boundary, including registered-app and HTTP/self-hosted modes without embedding bearer-token values.

### Security

- generated plugin packages are private by default, reject unsafe connection metadata and refuse to
  overwrite directories not created by Runner MCP.

## 0.1.3 — 2026-10-02

Published from exact commit `0aa013c279128e22fbd53be32c35bced3ae26834` through the protected release workflow after the full release check passed.

### Added

- proportional AI fault-containment regression coverage and deterministic security-gate boundaries;
- optional coarse Runner Fabric work-unit transport plus bounded first-install Fabric bootstrap guards;
- durable asynchronous migration-job storage with explicit async start/status integration;
- cross-process release-operation locking and bounded local one-release retention pruning;
- local-only bounded service-journal reads behind explicit per-service opt-in;
- AIfordable Agent Bus private configuration, managed worker lifecycle, outbound relay core and one-shot qualification;
- local host-runtime integrity decision model, fixed Linux diagnostic adapter and sanitized hardware/runtime fault evidence;
- fresh fixed autostart runtime smoke plus shared fail-closed activation gating for systemd and managed cron;
- local read-only `runner-mcp autostart preflight` using the same activation decision as installation.

### Changed

- clean Ubuntu install proof now exercises the current installer/runtime integrity path;
- installer/runtime probes classify bounded timeout/native-crash outcomes instead of leaking raw process details;
- self-update wheel staging now preflights offline packaging capability before per-job artifact mutation;
- self-update baseline/bootstrap and distribution identity handling were hardened while preserving the no-dependency compatibility contract;
- Agent Bus is the preferred future runtime-control direction while GitHub mailbox remains a bounded fallback path.

### Security

- autostart cannot persist/enable managed startup unless emergency-stop, recovery, restart-pending, fresh runtime-smoke and host-integrity gates all clear;
- direct systemd/cron installer entry points independently reject missing activation permits;
- host diagnostics remain local-only and expose bounded categories rather than raw journal records;
- Runner Fabric live activation remains gated until its durable service/resume chain is integrated and privately proven.

## 0.1.2 — 2026-09-26

Canonical cross-registry recovery release.

### Distribution and discovery

- corrected the official MCP Registry identity to the case-sensitive `io.github.Blacksp1d3r/runner-mcp`;
- published `aifordable-runner-mcp==0.1.2` to PyPI;
- published matching `0.1.2` metadata to the official MCP Registry;
- created GitHub pre-release `v0.1.2` from exact commit `83175f439c60346f92b5759a90993c3b8f5352f8`;
- aligned public PyPI / MCP Registry / GitHub discovery links.

## 0.1.1 — 2026-09-26

First public PyPI package upload under `aifordable-runner-mcp` while preserving Runner MCP as the product name and `runner-mcp` as the primary CLI.

## 0.1.0 — 2026-09-24

First public alpha release, published as GitHub pre-release `v0.1.0`.

### Added

- security-first self-hosted MCP server foundation;
- allow-listed project registry and safe project file access;
- external operator emergency stop and retention safety policy;
- predefined asynchronous test profiles with bounded scrubbed logs;
- allow-listed staging service controls;
- PostgreSQL backup and migration controls;
- staging-only deployment and one-step code rollback;
- built-in project adapter foundation;
- short-lived local human approval gates for higher-risk staging actions;
- GitHub mailbox bridge protocol with a strict allow-list;
- bounded bridge result envelopes and replay protection;
- strict terminal task-completion events with deterministic notification IDs;
- optional private GitHub-issue completion delivery with bootstrap history cutoff, local delivery deduplication and remote deterministic-marker reconciliation;
- watcher heartbeat, replay lifecycle and fail-closed restart-recovery primitives;
- explicit local missing-result recovery that can publish a terminal safe failure for an already-claimed request without replaying the operational action or resetting watcher state;
- local-only abandonment for strictly valid unclaimed requests and bounded malformed-request quarantine with request-head race protection;
- transport-neutral bridge processor with explicit allow-listed executor and durable-result ordering;
- fixed-host GitHub mailbox transport with strict JSON/base64 validation and create-once results;
- incremental GitHub mailbox watcher with explicit bootstrap and restart-safe cursor reconciliation;
- loopback-only MCP bridge executor with strict JSON/SSE parsing and bounded test polling;
- private-config GitHub watcher runtime and CLI with explicit bootstrap and separate polling/heartbeat cadence;
- secure standard-input token ingestion for mailbox configuration without putting credentials in command-line arguments;
- bounded fair multi-project scheduling with persistent project queues, immediate test job IDs, safe capacity observability and explicit parallel-safe opt-in;
- scale-aware bounded MCP request capacity sized for concurrent mailbox workers and status polling;
- interactive setup, doctor, guide and configuration-management CLI;
- managed non-root autostart for the fixed Runner MCP server and explicitly bootstrapped watcher components, using systemd user services when available and a lock-protected managed cron fallback on headless accounts;
- public CI for this public repository;
- initial umbrella project identity;
- five-minute local demo, release checklist and launch-readiness documentation;
- clean Ubuntu 24.04 / Python 3.12 CI coverage for the documented five-minute demo;
- short per-job private test temporary directories that avoid Unix-domain socket path exhaustion while preserving restrictive permissions and cleanup;
- bounded operational GitHub mailbox actions for scrubbed test logs, configured service control, backups, migration/deployment/rollback planning and approval-bound high-risk execution;
- canonical main-only Runner MCP self-update jobs with fixed lint/unit gates, local no-dependency installation and internal component self-reexec;
- recoverable self-update activation markers that block overlapping updates and preserve pending restart intent when a fixed component re-exec fails;
- private staged self-update wheels with durable install transactions, verified baseline rollback for caught package failures and fail-closed pending-recovery state for unproven interruption;
- bounded local self-update install recovery requiring the emergency stop and restoring only the persisted private baseline wheel/source commit, unavailable through MCP/mailbox control;
- bounded local `status`/`doctor` visibility for self-update install recovery without exposing commits or private artifact paths;
- a fail-fast local release-check wrapper covering compile, Ruff, pytest, whitespace, built-artifact and clean-demo validation while keeping GitHub CI authoritative;
- category-only safe diagnostics for managed cron and completion-watcher failures without leaking private paths or raw exception text;
- terminal deployment/rollback completion delivery with source-scoped idempotency and no task replay;
- privacy-safe connectivity categories and current private-tunnel/reverse-proxy guidance without changing bind, TLS, DNS, firewall, proxy or tunnel state;
- local read-only PostgreSQL restore preflight that validates one private archive without reading the configured DSN, connecting to the database or adding restore execution authority.
- local read-only retention preview that strictly validates private release/backup state and reports protected or potentially eligible records without deletion authority.

### Fixed

- the loopback mailbox executor now accepts the MCP SDK's bounded multi-item text encoding for list-returning tools such as project and test-profile listings, while still rejecting multi-item content for scalar tools;
- the clean demo keeps its temporary project virtual environment outside the repository so local validation cannot delete a developer's `.venv`.

### Security

- arbitrary shell input is not part of the normal MCP or mailbox interfaces;
- unknown MCP arguments fail closed;
- bridge requests/results reject duplicate keys and non-standard JSON constants;
- bridge results are bounded and conservatively scrubbed;
- duplicate mailbox request IDs cannot be silently re-executed;
- notification delivery is separated from task execution so a delivery retry cannot rerun the task;
- ambiguous or missing-result watcher recovery states do not automatically re-execute operational actions;
- malformed historical requests can be quarantined only after all sibling backlog requests are verified durable and the request head is unchanged;
- mailbox operational actions remain fixed-schema: no arbitrary shell, argv, path, environment, systemd unit, MCP tool, approval grant, restore or production mutation is accepted;
- self-update cannot select an arbitrary repository, branch, package-manager command, executable, install path or restart command;
- self-update restart markers are create-once, batch-prepared for the fixed components, and restored after a failed re-exec instead of silently losing activation intent;
- self-update package mutation is preceded by private wheel staging and a strict transaction marker; caught failures roll back only when both package and source restoration are verified, while interrupted/unproven recovery blocks further updates;
- result persistence/finalization failures do not authorize bridge action replay;
- GitHub mailbox transport failures are classified and kept inside the persistence/recovery boundary;
- watcher restarts reuse cursor/replay state and never treat process restart as permission to replay actions;
- bridge execution cannot target a non-loopback MCP endpoint and never fetches test logs;
- GitHub mailbox secrets stay in the private 0600 runtime environment and are preserved across setup overwrite;
- production mutations remain disabled;
- database restore execution remains unimplemented; the local restore preflight is read-only and adds no restore authority.

### Known limitations

- privacy-safe private-tunnel/reverse-proxy guidance is available, but automatic tunnel/TLS/DNS/firewall/proxy provisioning remains operator-managed;
- untrusted public-fork code is not sandboxed for execution on a privileged persistent runner;
- PostgreSQL restore/PITR orchestration and automated retention pruning are not implemented;
- the optional built-in GitHub-issue notifier requires a private destination and GitHub credential; notification transport remains independent from mailbox execution.
- managed-cron removal disables future supervision but deliberately does not blindly terminate an already-running component; immediate local termination remains an operator action.

## Release format

Future releases should move relevant entries from **Unreleased** into a dated version section. Release notes should link to the exact validated tag/commit and call out security-boundary changes explicitly.
