# Current state

Date: 2026-09-20

## Status

Runner MCP Phases 0 through 9 and Phase 3.9 launch-readiness are merged to main. Phase 3.7 formalizes the GitHub mailbox transport; Phase 3.8 adds bounded results and replay protection. Phase 3.8.1 adds a strict public task-completion event contract with deterministic notification IDs. Phase 3.8.2 adds watcher heartbeat and restart-recovery semantics on the current feature branch. GitHub remains the source-code surface, while Runner MCP remains the local execution and safety boundary.

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
- Fools2Tools project identity and a free public-launch-readiness plan were added without changing Runner MCP's product identity or security boundaries;
- public CI validates pull requests and main on a fresh standard GitHub-hosted runner with read-only repository permissions, pinned official actions and no private secrets; standard runners are free for this public repository.


Phase 3.9 public launch readiness:
- README now leads with a concise problem statement, architecture and safety boundary;
- Fools2Tools remains a light umbrella identity; Runner MCP retains its own product/package identity;
- five-minute local evaluation demo added alongside the full Quickstart;
- root security-reporting policy added;
- public changelog and release checklist added;
- factual launch copy prepared without publishing external posts;
- privacy-safe bug and feature request forms added;
- pull-request template reinforces security invariants and public-repository hygiene;
- package metadata expanded for future public distribution;
- launch-readiness gate explicitly tracks what is complete and what still needs clean-environment/release verification;
- no marketing telemetry or paid runtime dependency added.

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
- existing private mailbox notification workflow is currently blocked by unavailable repository-specific Actions capacity and has not yet completed an end-to-end delivery proof.

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
- OpenAI Secure MCP Tunnel is the preferred future private ChatGPT connectivity path;
- a hosted public relay remains optional and outside the MVP.

## Validation

Phase 3.8.1 branch validation is green:
- Python 3.12 compile: green;
- Ruff: green;
- pytest: 270 tests green, with one third-party Starlette/AnyIO deprecation warning;
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

Validate and merge the watcher-resilience branch, then migrate the private mailbox watcher to the shared request/result/replay lifecycle and publish the sanitized heartbeat. Prove restart recovery against a fresh backlog without replaying completed work. Keep the idempotent completion-notification path separate. After that, verify the five-minute demo from a clean Linux environment and continue service/tunnel onboarding.

Before activating real project test/service/database/deployment profiles, create the private runtime configuration and verify Linux-account, service-health and PostgreSQL recovery boundaries on the actual host.

Do not add real environment values to this repository.
