# Runner MCP roadmap

This public roadmap is intentionally infrastructure-neutral. Real deployment details belong only in private configuration.

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

Still planned for onboarding: service auto-start packaging, guided TLS/reverse-proxy setup and optional graphical administration.

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

- service auto-start packaging;
- guided private-tunnel/TLS setup;
- optional graphical administration;
- framework adapters only when concrete reusable use cases justify them.

## Phase 3.7 — GitHub mailbox bridge protocol

Formalize the proven GitHub to Runner MCP transport without turning it into a remote shell:

- public, infrastructure-neutral mailbox protocol documentation;
- strict versioned JSON request model;
- fixed allow-list for project inspection and predefined test execution;
- unknown fields, duplicate keys and oversized requests fail closed;
- no client-supplied shell, executable, path, environment, service or arbitrary MCP tool name;
- migration, deployment, rollback and restore remain outside the mailbox allow-list;
- watcher implementation stays private until deployment-specific parts are separated from reusable protocol logic.

Next:

- migrate the private watcher to the shared protocol validator;
- package a generic watcher only when it can be done without exposing credentials or infrastructure details.

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

Next:

- migrate the private watcher from its pilot request/result shape to the shared validator, result envelope and replay ledger;
- add watcher-level integration tests using only generic placeholder configuration.

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

Pilot transport state:

- project-local CI completion notifications are proven for success, failure and cancellation;
- a private mailbox notification workflow exists for completed `run_tests` results;
- the private mailbox notifier currently depends on a repository-specific self-hosted Actions runner, so delivery jobs queue when that runner is unavailable;
- the central completion path therefore still needs a fresh end-to-end proof after the notification transport is activated.

Next:

- make the private notifier use the deterministic event ID as an idempotency marker;
- activate a notification transport that does not require widening Runner MCP execution authority;
- prove that one fresh `run_tests` result produces exactly one user-facing completion notification;
- keep heartbeat/stale-request recovery as a separate resilience concern;
- map other existing asynchronous Runner MCP jobs to the same completion-event contract before adding any new mailbox actions.

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
- transport retry policy never authorizes operational action replay.

Next:

- migrate the private watcher to claim -> execute -> persist safe result -> mark completed;
- publish the sanitized heartbeat through the private transport;
- add watcher-level integration tests using placeholder-only configuration;
- prove restart recovery against a fresh backlog without replaying completed work;
- keep notification delivery and heartbeat/stale recovery independent.

## Phase 3.9 — public launch readiness

Prepare Runner MCP for free, responsible discovery without changing its security boundaries.

Implemented launch-readiness foundation:

- Runner MCP remains the product identity under the Fools2Tools umbrella;
- README leads with the problem, safety boundary and architecture;
- Quickstart remains the full guided path while a separate five-minute local demo provides a shorter evaluation path;
- root security-reporting policy added;
- public changelog and release checklist added;
- reusable factual launch copy prepared for GitHub and developer communities;
- privacy-safe GitHub bug/feature forms and a security-focused pull-request template added;
- package metadata improved for future distribution;
- discovery metrics remain platform-level; no application marketing telemetry is added;
- no paid advertising, paid hosted CI or paid hosted infrastructure is a hidden dependency; standard free CI for this public repository is acceptable when it carries no private secrets.

Remaining before a broader launch:

- verify the five-minute demo from a clean supported Linux environment;
- create the first tagged alpha release with exact release notes;
- set the public GitHub description/topics to the prepared values;
- prepare an MCP ecosystem/registry submission only when packaging requirements are met;
- publish external community posts only as a separate human-controlled action.

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

Journal/log access remains a later bounded addition.

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
- CLI database and migration configuration without manual YAML editing.

Not implemented yet:

- database restore;
- WAL archiving/PITR orchestration and verification;
- automated retention pruning.

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

- automatic release pruning;
- production rollback;
- database restore/recovery workflow.

## Phase 8 — multi-project adapters

Move project-specific behavior behind a common adapter interface. New projects should normally require configuration/adapters rather than core changes.

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
