# Changelog

All notable user-visible changes to Runner MCP will be documented here.

Runner MCP is under active development. New changes remain under **Unreleased** until an exact validated commit is explicitly tagged and released.

## Unreleased

### Distribution and discovery

- prepare the `0.1.1` Python package metadata for PyPI Trusted Publishing;
- add official MCP Registry metadata under `io.github.blacksp1d3r/runner-mcp`;
- add release automation that publishes the Python package first, then the MCP Registry entry through GitHub OIDC, and finally creates the GitHub pre-release;
- add regression checks keeping `pyproject.toml`, `server.json` and the PyPI README ownership marker synchronized;
- sharpen the README's first-screen positioning and discovery metadata without widening Runner MCP runtime authority.

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
- Fools2Tools project identity;
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
