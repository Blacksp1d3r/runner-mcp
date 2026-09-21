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
- short per-job private `TMPDIR` paths for local IPC/socket based test runtimes, with 0700 permissions and terminal cleanup;
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

Service auto-start packaging is implemented with a preferred non-root systemd-user backend plus a managed cron fallback for headless accounts without a usable user bus. Both keep fixed components, explicit watcher bootstrap, duplicate-supervisor protection and foreign-state protection. Still planned for onboarding: guided TLS/reverse-proxy setup and optional graphical administration.

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

Implemented notification runtime and private proof:

- an optional private GitHub-issue notifier observes persisted terminal test jobs without calling the execution path;
- notifier bootstrap deliberately skips historical completions;
- deterministic event IDs are used both in a private 0600 delivery ledger and as remote notification markers;
- existing remote markers are reconciled instead of posted again;
- notification failures remain retryable independently from task execution;
- one fresh predefined test job was proven end to end to produce exactly one user-facing notification, and a repeated notification cycle produced no duplicate;
- the built-in notifier no longer requires a repository-specific self-hosted Actions runner.

Next:

- keep heartbeat/stale-request recovery separate from notification delivery;
- map other existing asynchronous Runner MCP job classes to the same completion-delivery runtime only when their persisted terminal metadata can be consumed without widening execution authority.

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

Next:

- combine the public processor with the fixed-host GitHub mailbox transport;
- migrate the pilot watcher to the public request/replay/result lifecycle;
- prove fresh request processing, restart recovery, heartbeat and completion feedback end to end.

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

Next:

- add a generic watcher/coordinator loop around the public transport, processor, replay lifecycle and heartbeat contract;
- keep credentials, repository/ref selection and supervisor configuration private;
- migrate the private pilot watcher to that thin adapter;
- prove restart recovery and exactly-once completion feedback on the migrated watcher.

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

Next:

- combine the watcher coordinator with the loopback MCP bridge executor;
- migrate the private pilot watcher with private runtime configuration only;
- prove the migrated watcher against one fresh request plus a restart/recovery cycle;
- keep completion-notification delivery independent and idempotent.

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

Next:

- use the private-config runtime and CLI to migrate the existing pilot watcher;
- prove one fresh request and one restart/reconciliation cycle end to end;
- keep completion notification independent and idempotent;
- then return to clean-environment launch verification and service/tunnel onboarding.

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

Next:

- finish the independent completion-notification proof where notification transport capacity is available;
- return to clean-environment launch verification and service/tunnel onboarding.

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
- clean Ubuntu 24.04 / Python 3.12 CI now exercises the documented five-minute demo end to end, including installation, setup, doctor, predefined test-profile configuration, emergency stop and loopback health check;

Remaining before a broader launch:

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
