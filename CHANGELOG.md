# Changelog

All notable user-visible changes to Runner MCP will be documented here.

Runner MCP is under active development. Until the first tagged release, changes are collected under **Unreleased**.

## Unreleased

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
- Fools2Tools project identity;
- five-minute local demo, release checklist and launch-readiness documentation;
- clean Ubuntu 24.04 / Python 3.12 CI coverage for the documented five-minute demo;
- short per-job private test temporary directories that avoid Unix-domain socket path exhaustion while preserving restrictive permissions and cleanup;
- bounded operational GitHub mailbox actions for scrubbed test logs, configured service control, backups, migration/deployment/rollback planning and approval-bound high-risk execution;
- canonical main-only Runner MCP self-update jobs with fixed lint/unit gates, local no-dependency installation and internal component self-reexec;
- recoverable self-update activation markers that block overlapping updates and preserve pending restart intent when a fixed component re-exec fails;
- private staged self-update wheels with durable install transactions, verified baseline rollback for caught package failures and fail-closed pending-recovery state for unproven interruption.

### Fixed

- the loopback mailbox executor now accepts the MCP SDK's bounded multi-item text encoding for list-returning tools such as project and test-profile listings, while still rejecting multi-item content for scalar tools.

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
- database restore remains unimplemented rather than being automated unsafely.

### Known limitations

- guided private-tunnel/reverse-proxy onboarding is not yet one-click;
- untrusted public-fork code is not sandboxed for execution on a privileged persistent runner;
- PostgreSQL restore/PITR orchestration and automated retention pruning are not implemented;
- the optional built-in GitHub-issue notifier requires a private destination and GitHub credential; notification transport remains independent from mailbox execution.
- managed-cron removal disables future supervision but deliberately does not blindly terminate an already-running component; immediate local termination remains an operator action.

## Release format

When the first release is tagged, move the relevant entries from **Unreleased** into a section such as:

```text
## 0.1.0 - YYYY-MM-DD
```

Release notes should link to the exact validated tag/commit and call out security-boundary changes explicitly.
