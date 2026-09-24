# Task 24 — asynchronous completion-delivery expansion review

Date: 2026-09-23

## Scope

Review only. No runtime or delivery behavior is changed here.

Question: can the existing completion-delivery runtime safely consume persisted terminal metadata for migration, deployment and rollback jobs without widening execution authority or weakening idempotency?

## Executive conclusion

- **Deployment jobs: SAFE CANDIDATE for one bounded CODE slice.**
- **Rollback jobs: SAFE CANDIDATE for the same bounded CODE slice.**
- **Migration jobs: BLOCKED pending a real persisted migration-job substrate.**

The current completion schema already reserves distinct source/operation bindings for all three classes, but only deployment and rollback currently have durable asynchronous job metadata suitable for read-only scanning.

## Existing completion contract

`completion_feedback.py` already binds:

- `DEPLOYMENT_JOB -> DEPLOY_STAGING`
- `ROLLBACK_JOB -> ROLLBACK_RELEASE`
- `MIGRATION_JOB -> APPLY_MIGRATION`

Completion event IDs are deterministic and source-scoped:

`event_id = SHA256("runner-mcp-completion:v1:<source>:<source_id>")[:32]`

That means a deployment job ID and a rollback job ID with the same text still produce distinct event IDs because the source differs.

Non-test completion events must not carry a test profile.

## Candidate inventory

### Deployment

Persisted source:
- `Settings.deployment_jobs_root`
- `DeploymentJobRunner`
- one private JSON file per job

Persisted public metadata shape:
- `job_id`
- `project`
- `operation`
- `state`
- `created_at`
- `started_at`
- `finished_at`
- `result`
- `error_category`

Durable terminal states:
- `completed`
- `stopped`
- `error`
- `interrupted`

Recommended completion mapping:
- `completed -> SUCCEEDED`
- `stopped -> CANCELLED`
- `error -> FAILED`
- `interrupted -> FAILED`

Recommended completion identity:
- source: `DEPLOYMENT_JOB`
- source_id: persisted `job_id`
- operation: `DEPLOY_STAGING`
- project: persisted project identifier
- profile: none

Classification: **SAFE CANDIDATE**.

### Rollback

Rollback uses the same `DeploymentJobRunner` and persisted JSON model.

The explicit persisted discriminator is:
- `operation == "rollback"`

Recommended completion mapping is identical to deployment state mapping.

Recommended completion identity:
- source: `ROLLBACK_JOB`
- source_id: persisted `job_id`
- operation: `ROLLBACK_RELEASE`
- project: persisted project identifier
- profile: none

Classification: **SAFE CANDIDATE**.

### Migration

Current mutation path:
- `server.apply_migrations()`
- synchronous call to `DatabaseManager.apply_migrations(project)`
- approval is consumed before execution
- audit records the result
- no asynchronous migration job object exists
- no migration job root exists in `Settings`
- no persisted migration job ID / terminal metadata file exists

The presence of `CompletionSource.MIGRATION_JOB` and `CompletionOperation.APPLY_MIGRATION` is therefore only a schema reservation today; it is not evidence of a durable completion source.

Do not synthesize migration completions from:
- audit entries;
- nested deployment migration result data;
- deployment job IDs;
- transient MCP request state.

Those alternatives either lack a dedicated durable source identity or risk duplicate/ambiguous notifications.

Classification: **BLOCKED** until a separately reviewed persisted migration-job model exists.

## Safety requirements for a deployment/rollback scanner

A future scanner should be read-only and should not instantiate `DeploymentJobRunner`, because that runner has recovery behavior that can mutate persisted queued/running jobs on startup.

Instead, scan the configured deployment job directory directly with a strict parser.

Required checks:

1. deployment job root must be an existing non-symlink directory;
2. enforce a bounded file count;
3. each candidate must be a non-symlink regular file;
4. enforce a bounded metadata size;
5. filename stem must be exactly the persisted 32-lowercase-hex `job_id`;
6. JSON must reject duplicate keys and non-standard constants;
7. require an explicit `operation` of exactly `deploy` or `rollback`;
8. validate `project` with the existing completion identifier contract;
9. parse `state` only through `DeploymentJobState`;
10. ignore non-terminal `queued` and `running` records;
11. terminal records must have a valid timezone-aware `finished_at`;
12. apply the existing notifier bootstrap `started_at` cutoff;
13. do not copy `result`, `error_category`, commit IDs, release IDs, paths or other dynamic metadata into completion events.

### Legacy metadata

`DeploymentJobRunner._load_existing_metadata()` currently tolerates old records with no `operation` by defaulting them to `deploy`.

The completion scanner should **not** inherit that permissive default.

For notification identity, missing operation makes deployment-vs-rollback source binding ambiguous. Such records should fail closed or be excluded by an explicitly documented compatibility rule; they must never be guessed to be deployment completions.

## Privacy assessment

The existing persisted deployment result may contain release IDs, commits and other operational fields. None are needed for completion delivery.

The smallest safe event contains only:
- source-scoped deterministic event ID;
- allow-listed source;
- allow-listed operation;
- validated project code;
- terminal completion state.

No result body or error message should enter the notification event.

The delivery ledger remains suitable unchanged because it keys on:
- destination ID;
- deterministic event ID.

## Idempotency and replay assessment

The existing completion pipeline already has two independent duplicate protections:

1. local delivery ledger by destination ID + event ID;
2. remote GitHub notification marker containing the event ID.

Using persisted job ID as `source_id` preserves these properties for deployment and rollback.

Restarted `queued`/`running` deployment jobs become persisted `interrupted` terminal jobs through the existing job runner recovery path. The completion scanner can then report them as failed/attention-required without executing or repairing the job.

## Demonstrated integration issue in current notifier rendering

`GitHubIssueCompletionNotifier.deliver()` currently always renders:

- `Test profile: <event.profile>`

For non-test completion events the schema requires `profile is None`.

Therefore deployment/rollback delivery should not be enabled without a small rendering adjustment. The existing test-job text can remain unchanged, while non-test events should render their allow-listed operation and omit the test-profile line.

This is presentation only; it must not expose result/error metadata.

## Smallest recommended CODE slice

Create a separate CODE task limited to:

1. add a strict read-only deployment/rollback completion scanner in `completion_delivery.py`;
2. optionally wire `settings.deployment_jobs_root` into `CompletionNotifierRuntime.from_private_config()` without changing the existing test-job requirement in the first slice;
3. merge deployment/rollback events with test-job events after the common bootstrap cutoff;
4. preserve deterministic event IDs and the existing delivery ledger;
5. update notification rendering so non-test events omit `Test profile: None` and show only the allow-listed operation;
6. add focused security/regression tests.

Do not:
- add migration completion in this slice;
- add a migration job store;
- change deployment/rollback execution;
- instantiate `DeploymentJobRunner` from the notifier;
- read or emit deployment `result` contents;
- add new MCP/mailbox authority.

## Required regression matrix for the CODE follow-up

- deployment completed -> succeeded event;
- rollback completed -> succeeded event;
- stopped -> cancelled;
- error/interrupted -> failed;
- queued/running ignored;
- source/operation binding is exact;
- same textual source ID remains source-scoped;
- missing/unknown operation fails closed;
- job ID / filename mismatch fails closed;
- unsafe project identifier fails closed;
- symlink metadata rejected without following referent;
- oversized/broad or malformed metadata rejected according to the chosen private-file contract;
- duplicate JSON keys and NaN/Infinity rejected;
- timezone-less/missing terminal `finished_at` rejected;
- pre-bootstrap terminal jobs ignored;
- `result`, `error_category`, commit/release/path literals cannot enter the completion event or notification body;
- repeated scans do not duplicate delivery;
- test-job notification rendering remains unchanged;
- deployment/rollback rendering contains no `Test profile: None`;
- no execution call is reachable from scanning/delivery.

## Recommendation

Queue one bounded CODE follow-up for deployment + rollback only.

Keep migration completion blocked until the project introduces a separately reviewed, durable persisted migration-job identity/state model.
