# Task 42 — durable migration-job substrate boundary review

Date: 2026-09-24

Status: **COMPLETE — review only. Existing migration execution remains synchronous.**

## Scope

This review evaluates whether Runner MCP can add a dedicated persisted migration-job model so migration completion delivery has a real durable source identity.

No migration command is changed or executed by this review. No approval is consumed. No new MCP, bridge or mailbox mutation action is added.

## Executive conclusion

A **durable internal migration-job substrate is justified as a bounded CODE follow-up**, but the existing MCP/mailbox `apply_migrations` path must remain synchronous until that substrate is independently proven.

The first code slice should add:

- a separate private migration-job store and runner;
- explicit queued/running/terminal metadata;
- fail-closed restart conversion of queued/running jobs to `interrupted` with no replay;
- exact migration-plan binding revalidation before execution;
- strict bounded public job status;
- a read-only completion scanner for terminal migration jobs.

It should **not** wire the current MCP/bridge `apply_migrations` action to the new asynchronous runner yet. That would change an established request/result contract and deserves a separate integration review after the substrate has test evidence.

Deployment-triggered migrations also remain synchronous inside deployment. They must not enqueue a nested migration job.

## Current migration execution contract

`server.apply_migrations(project, approval_id)` currently performs one synchronous action:

1. recompute `_migration_approval_material(project)`;
2. consume the short-lived migration approval against that exact binding;
3. call `DatabaseManager.apply_migrations(project)` directly;
4. return the bounded migration result to the same MCP call.

The approval binding includes:

- staging environment;
- configured repository identity;
- complete configured database/migration model;
- clean source-control HEAD evidence.

The public approval summary includes the approved clean commit and states that a pre-migration backup is required and automatic database restore is disabled.

`DatabaseManager.apply_migrations()` then:

- rechecks that the project mutation is allowed for staging;
- acquires the per-project non-blocking database-operation lock;
- validates database and migration configuration;
- rechecks the safety guard;
- creates the mandatory `pre_migration` backup;
- rechecks the safety guard after the backup;
- invokes the fixed migration command with `shell=False`, bounded timeout/process-group termination and scrubbed bounded output;
- never automatically restores the database;
- releases the database-operation lock in `finally`.

This synchronous path is already a coherent safety boundary. The new job substrate must preserve it rather than reimplement migration internals.

## Why a migration-job substrate is needed

Task 24 correctly kept migration completion delivery blocked.

The completion schema reserves:

- source `migration_job`;
- operation `apply_migration`;

but no durable migration job ID/state store exists today.

Do not synthesize migration completion from:

- audit records;
- bridge request IDs;
- deployment job IDs;
- pre-migration backup IDs;
- transient MCP request state;
- nested deployment result dictionaries.

Those identifiers have different lifecycle and replay semantics and would create ambiguous or duplicate completion events.

## Job identity and state model

The new substrate should have its own private root and its own 32-lowercase-hex job IDs.

Recommended states:

- `queued`;
- `running`;
- `completed`;
- `stopped`;
- `error`;
- `interrupted`.

Recommended terminal-state interpretation:

- `completed`: migration command returned the existing `applied` result;
- `stopped`: operator stop blocked execution before the migration command began;
- `error`: bounded known failure category;
- `interrupted`: Runner MCP restarted or state became ambiguous while a job was queued/running.

Do not add an automatic `retrying` or `resuming` state.

## Private persistence contract

Use a distinct configuration root such as `RUNNER_MCP_MIGRATION_JOBS_ROOT`, represented separately in `Settings` and private onboarding configuration.

Required storage properties:

- absolute root;
- root non-symlink and mode 0700;
- one metadata file per job, mode 0600;
- strict 32-hex filename/job identity agreement;
- strict exact JSON shape, duplicate-key rejection and standard JSON only;
- timezone-aware timestamps;
- bounded metadata size;
- durable atomic private writes with parent-directory fsync semantics consistent with Runner MCP's hardened private I/O primitives;
- no raw exception text;
- no DSN, executable path, cwd, repository filesystem path or migration output in fields needed for completion delivery.

Persisted private binding fields may include hashes/fingerprints that are never exposed publicly.

## Approval consumption timing

A future asynchronous integration must preserve this ordering:

1. recompute exact migration approval binding;
2. consume the approved single-use approval;
3. durably create the queued migration job;
4. only after durable job creation, start the worker.

This order intentionally prefers a harmless wasted approval over an unauthorized queued mutation.

If the process crashes after approval consumption but before job persistence, no migration may run and that approval remains consumed. The operator must request a new approval.

Do **not** create a runnable queued job before approval consumption. A crash in that order could leave work that has durable execution intent without durable proof that the approval was consumed.

Do not persist the raw approval binding object if it contains private configuration. Persist only a private cryptographic fingerprint plus the minimum non-secret expected fields needed for revalidation, such as the approved clean commit.

## Enqueue and worker revalidation

A future integration should pass the job runner only bounded expected state, not arbitrary commands.

Before a worker changes `queued` to `running`, it must recompute the same migration material used for approval and compare the private binding fingerprint.

If repository HEAD, cleanliness, database/migration configuration or staging environment changed, the job becomes terminal `error` with category `plan_changed` without creating a backup or running migration code.

Only after successful binding revalidation should the worker durably mark the job `running` and invoke the existing `DatabaseManager.apply_migrations(project)`.

Do not duplicate backup/migration command logic in the job runner.

## Database-operation locking

The job runner should **not** acquire `DatabaseManager`'s project lock itself and then call `apply_migrations()`, because `apply_migrations()` already acquires that non-reentrant lock.

Instead:

- job runner performs only non-mutating plan revalidation;
- it calls `DatabaseManager.apply_migrations()` exactly once;
- the database manager remains the owner of database serialization, mandatory backup and safety rechecks.

If another backup/migration/deployment-triggered migration holds the database lock, the job fails terminally with a bounded `database_busy`/`migration_error` category. It must not automatically wait and retry because a later retry could run against changed code or schema state.

## Interaction with deployment-triggered migrations

Deployment currently holds the deployment-operation lock and may synchronously invoke `DatabaseManager.apply_migrations()`, producing the established deployment -> database lock order.

Keep that behavior.

Do not make deployment enqueue a migration job because deployment must know the migration result before deciding whether release activation may continue.

A direct migration job and a deployment-triggered migration naturally serialize at the database-operation lock. The loser fails closed; neither operation should poll and replay until the lock becomes free.

## Restart and crash semantics

On startup, a migration-job runner may load existing metadata read-only and mark any valid `queued` or `running` record as terminal `interrupted`.

It must never automatically execute or resume those records.

This rule is essential because a process can crash:

- after the pre-migration backup;
- while the migration process is running;
- after the migration command changed database state but before the job record was persisted as completed.

In all of those cases, automatic replay can repeat a partially or fully applied migration.

Therefore after restart:

- `queued` -> `interrupted`;
- `running` -> `interrupted`;
- `finished_at` is set;
- error category is a bounded `runner_restart` or `execution_ambiguous` category;
- result/output is not reconstructed from guesses.

The operator can use the existing read-only `migration_status` and backup evidence to decide what to do next.

## Crash after successful migration but before completion persistence

This is deliberately reported as `interrupted`, not `completed`.

That can create a false-negative completion alert, but it is safer than claiming success without durable proof. Completion delivery should surface attention required; it must never rerun the migration to obtain certainty.

## Public job result contract

Recommended public status fields:

- `job_id`;
- `project`;
- `operation = migration`;
- `state`;
- `created_at`;
- `started_at`;
- `finished_at`;
- bounded `migration_state` such as `applied`, `failed`, `timed_out`, or null;
- bounded `error_category`;
- `pre_migration_backup_created` boolean;
- `output_truncated` boolean if needed.

Do not expose:

- migration stdout/stderr in completion/status metadata;
- DSN or database endpoint;
- source/project filesystem paths;
- executable/cwd;
- backup path;
- archive contents;
- private approval fingerprint;
- raw exception text.

The existing synchronous `apply_migrations` result may continue to return its current scrubbed output. The new durable job metadata should be smaller because its primary purpose is state, restart safety and completion identity.

## Error categories

Use a fixed allow-list, for example:

- `operator_stop`;
- `safety_configuration`;
- `plan_changed`;
- `database_busy`;
- `migration_failed`;
- `migration_timed_out`;
- `runner_restart`;
- `unexpected_error`.

The implementation should map exceptions/results into these categories without persisting exception strings.

## Completion-delivery integration

Once the migration job store exists, `completion_delivery.py` may scan it directly using the same strict read-only posture used for deployment/rollback completion scanning.

Do not instantiate the mutation-capable job runner merely to discover completion events.

Scanner requirements:

- migration-job root must be private/non-symlink;
- bounded file count and metadata size;
- filename/job ID exact match;
- exact operation discriminator = `migration`;
- known strict state only;
- ignore queued/running;
- terminal record must have timezone-aware `finished_at`;
- apply notifier bootstrap cutoff;
- never copy result output, backup metadata, commit, error text or private fingerprints into the event.

Mapping:

- completed/applied -> `CompletionState.SUCCEEDED`;
- stopped -> `CompletionState.CANCELLED`;
- error/interrupted -> `CompletionState.FAILED`.

Source must be `CompletionSource.MIGRATION_JOB`, operation `CompletionOperation.APPLY_MIGRATION`, and source ID is the persisted migration job ID. Existing source-scoped event ID and delivery-ledger idempotency can then be reused unchanged.

## Existing MCP/mailbox contract must stay synchronous for the first slice

The current bridge action `apply_migrations` calls the MCP tool synchronously and persists the bridge result after that call returns.

Changing that same tool to return only a queued job would alter:

- bridge result meaning;
- client expectations;
- approval consumption/error timing;
- audit result semantics;
- completion semantics.

Do not hide that contract change inside the substrate implementation.

Therefore the first CODE task should leave:

- `server.apply_migrations()` synchronous;
- bridge `APPLY_MIGRATIONS` synchronous;
- `BridgeExecutor.apply_migrations()` synchronous;
- existing approval action and status unchanged.

A later review may choose either a new explicit asynchronous migration action/status tool or a versioned transition of the current action after evidence exists.

## Direct `migration_status` remains schema/status, not job status

Do not overload the existing `migration_status(project)` tool to return asynchronous job metadata.

If asynchronous migration execution is later exposed remotely, use a distinct job-status contract such as `migration_job_status(job_id)`.

## Smallest justified CODE follow-up

Task 44 is justified as an **internal substrate + read-only completion source**.

Recommended scope:

1. add `migration_jobs.py` with strict private durable job metadata and no automatic replay;
2. add a distinct private migration jobs root to Settings/onboarding;
3. implement a migration job runner that accepts only project plus expected private binding/commit evidence and calls existing `DatabaseManager.apply_migrations()` once after revalidation;
4. expose safe in-process `start/status` methods for tests/future integration, but do not wire them to MCP/mailbox yet;
5. add strict read-only migration completion scanning to `completion_delivery.py` using only terminal safe metadata;
6. add direct state-machine, persistence, restart, plan-change, lock-contention, privacy and completion-idempotency tests;
7. keep existing synchronous MCP/bridge migration execution unchanged.

This code slice creates real evidence without changing remote mutation semantics.

## Required regression matrix for Task 44

- private jobs root absolute/non-symlink/0700;
- metadata regular/non-symlink/0600 and exact shape;
- duplicate keys/non-standard JSON/oversize fail closed;
- queued metadata is durable before worker start;
- expected binding change prevents backup/migration;
- one worker calls `DatabaseManager.apply_migrations` at most once;
- database busy becomes terminal without retry;
- operator stop becomes terminal without retry;
- migration failed/timed out maps to bounded state/category;
- success persists completed/applied;
- queued/running startup records become interrupted and are never executed;
- crash/ambiguous state is never guessed as success;
- public status omits paths/DSN/raw output/private fingerprint;
- completion scanner ignores queued/running;
- completed -> succeeded, stopped -> cancelled, error/interrupted -> failed;
- completion event is source-scoped/idempotent;
- scanner never instantiates the mutation runner;
- existing synchronous MCP/bridge apply_migrations behavior remains unchanged;
- deployment-triggered migration remains synchronous;
- no automatic database restore is introduced.

## Follow-up integration review

After Task 44 is green and integrated, a separate review should decide whether and how remote asynchronous migration execution is worth exposing.

That review must explicitly cover:

- whether to add a new `start_migration` action versus versioning `apply_migrations`;
- bridge replay and durable-result ordering;
- approval consumption vs durable enqueue proof;
- job status authorization;
- audit semantics;
- compatibility for current clients;
- completion-delivery user experience.

Do not pre-authorize that change from this review.

## Conclusion

Migration completion can safely gain a durable substrate without weakening current execution, but only if the substrate is additive first.

Keep the proven synchronous migration path in place while Task 44 builds strict persisted job state and read-only completion evidence. Once that foundation is proven, remote asynchronous migration can be evaluated as a separate contract change rather than silently changing the meaning of `apply_migrations`.
