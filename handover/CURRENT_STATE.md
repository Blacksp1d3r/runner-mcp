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
- OpenAI Secure MCP Tunnel is the preferred future private ChatGPT connectivity path;
- a hosted public relay remains optional and outside the MVP.

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
