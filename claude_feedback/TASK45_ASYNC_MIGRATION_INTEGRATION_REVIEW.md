# Task 45 — asynchronous migration integration boundary review

Date: 2026-09-28

Status: **COMPLETE — review only. Task 44 substrate is integrated and green.**

## Evidence checkpoint

Task 44 merged via PR #118 as `6053b7c3d5aef757055c453d2fd5b7f581248e53`.

Post-merge evidence:
- Runner MCP validation #609: success;
- commit attribution #94: success;
- full Ruff/pytest/Registry/whitespace validation: success;
- built release artifact: success;
- clean five-minute demo: success.

The integrated Task 44 substrate proves:
- a separate private migration-job root;
- strict durable queued/running/terminal metadata;
- exact migration-plan revalidation before mutation;
- one call at most to the existing `DatabaseManager.apply_migrations()`;
- no automatic retry/resume after restart;
- queued/running restart state becomes terminal `interrupted`;
- bounded public status without DSN/path/executable/output/private fingerprint;
- read-only completion scanning using `MIGRATION_JOB` + `APPLY_MIGRATION`;
- existing synchronous MCP/bridge `apply_migrations` remains unchanged.

This review therefore evaluates only the remote integration contract.

## Decision

**Use a new explicit asynchronous action/status pair. Do not version or silently change the current synchronous `apply_migrations` meaning.**

The future bounded surface should be:

- MCP tool: `start_migration_job(project, approval_id)`;
- MCP tool: `migration_job_status(job_id)`;
- bridge action: `START_MIGRATION_JOB`;
- bridge action: `MIGRATION_JOB_STATUS`;
- human approval action: `migration_async`.

Keep all existing contracts unchanged:

- `apply_migrations(project, approval_id)` remains synchronous;
- bridge `APPLY_MIGRATIONS` remains synchronous;
- `migration_status(project)` remains schema/status inspection, not job status;
- deployment-triggered migrations remain synchronous inside deployment;
- completion delivery remains a separate later signal, not the immediate start result.

This is additive and makes the asynchronous behavior obvious to clients and operators.

## Why not change `apply_migrations`

Today `apply_migrations` has a coherent request/result contract:

1. recompute the exact migration approval material;
2. consume one matching human approval;
3. execute `DatabaseManager.apply_migrations()` synchronously;
4. return the bounded migration result;
5. audit the terminal migration result on the same request.

Changing that call to return a queued job would change:
- the meaning of a successful bridge result;
- the timing of migration errors;
- approval/result expectations;
- existing client code;
- audit semantics;
- retry behavior after transport failure.

Even in alpha, there is no need to take that compatibility risk because Task 44 already makes an additive action possible.

## Separate async approval authority

A normal `migration` approval must **not** automatically authorize the asynchronous execution mode.

Add a distinct approval action:

`migration_async`

The async approval binding should include:
- the exact existing migration binding;
- a fixed execution discriminator such as `durable_async_v1`.

Example conceptual binding:

```text
{
  "migration": <canonical migration binding>,
  "execution_mode": "durable_async_v1"
}
```

The public approval summary should say explicitly that:
- the action is an asynchronous migration job;
- staging only;
- the approved clean commit;
- a pre-migration backup remains mandatory;
- automatic database restore remains disabled;
- execution may complete after the initiating request has returned.

This prevents:
- using a sync migration approval to start an async job;
- using an async approval for the old sync `apply_migrations`;
- an AI/client choosing a different execution mode after human approval.

The underlying technical mutation stays `ActionClass.MIGRATION`; the approval distinction is about operator intent and execution semantics.

## Approval consumption and durable enqueue ordering

For `start_migration_job`, the required ordering is:

1. require that migration-job storage/runner is configured;
2. recompute canonical migration material;
3. construct the async-specific approval binding;
4. consume the approved single-use `migration_async` approval;
5. call the proven Task 44 runner with only:
   - project;
   - canonical migration-binding fingerprint;
   - expected clean commit;
6. the runner durably persists `queued`;
7. only then may the worker thread start.

Do not enqueue before approval consumption.

Crash semantics:
- crash before approval consumption: no authority consumed, no job;
- crash after approval consumption but before queued persistence: no job, approval remains consumed; operator must request a new approval;
- crash after queued persistence but before worker start: startup converts queued -> interrupted; never replay;
- crash while running or after DB mutation but before completion persistence: running -> interrupted; never guess success or replay.

A wasted approval is preferable to durable execution intent without durable approval consumption.

## Runner binding

The approval binding and worker revalidation have two related but distinct purposes.

Approval:
- binds the human decision to canonical migration state + async execution mode.

Worker:
- revalidates the canonical migration state immediately before mutation.

Therefore:
- approval fingerprint may cover the async wrapper;
- Task 44 runner should continue receiving the fingerprint of the underlying canonical migration binding that it knows how to recompute;
- do not teach the migration worker about human approvals or bridge requests.

This keeps the job substrate transport-neutral and reusable.

## Bridge replay and durable-result ordering

The current bridge lifecycle is already appropriate for a start-style asynchronous mutation:

1. replay ledger claims the request;
2. executor invokes the allow-listed action;
3. MCP start action consumes approval and durably queues a job;
4. safe start result is serialized;
5. result sink durably persists the bridge result;
6. replay ledger marks the request completed.

Important ambiguity rule:

If step 3 succeeded but step 5 or 6 fails, **never re-enqueue the migration job**.

The replay ledger already leaves such requests non-completed/ambiguous. A duplicate request must remain ambiguous rather than executing again.

The bridge result for `START_MIGRATION_JOB` represents:
- request accepted;
- durable migration job created;
- initial bounded job state.

It does **not** mean the database migration completed.

Use an explicit action name so the existing bridge envelope state `completed` cannot reasonably be confused with migration completion.

## Immediate result contract

The safe start response should be the existing Task 44 public job shape, for example:
- `job_id`;
- `project`;
- `operation = migration`;
- `state = queued|running`;
- timestamps;
- null migration state/error as applicable;
- safe booleans.

Do not include:
- approval fingerprint;
- raw migration binding;
- DSN;
- path;
- executable/cwd;
- migration output;
- backup path;
- raw exception;
- database endpoint.

The client must use `migration_job_status(job_id)` or completion delivery for terminal state.

## Job status authorization

Runner MCP currently uses one authenticated operator boundary rather than per-project identities.

For the first async migration integration:
- accept only a strict 32-lowercase-hex job ID;
- return only Task 44 public status;
- derive project from the persisted job, not client input;
- audit the resolved project and returned state;
- do not accept a path, project override, raw storage key or arbitrary lookup selector.

Do not overload `migration_status(project)`.

No migration job cancellation action is justified:
- a DB migration may be non-transactional or already changing schema;
- forced cancellation would require a separate database/process safety review;
- operator emergency stop can still block work before the migration command begins, but should not be misrepresented as a safe mid-migration rollback mechanism.

## Audit semantics

Recommended audit events:

`request_action_approval(project, "migration_async")`
- existing approval audit path;
- result pending/denied.

`start_migration_job(project, approval_id)`
- `denied` on approval/config/plan/storage/start failure;
- `started` only after durable queued persistence succeeds.

`migration_job_status(job_id)`
- `denied` for invalid/unknown job ID;
- otherwise audit the resolved project and safe job state.

Keep existing `apply_migrations` audit semantics unchanged.

Do not log:
- approval fingerprints;
- DSN;
- migration command;
- raw exception text;
- output;
- storage paths.

## Completion delivery coexistence

Immediate start result and later completion notification have different meanings:

- immediate start result: durable execution intent exists;
- completion event: terminal job state is durably known.

Existing Task 44 mapping remains:
- completed/applied -> succeeded;
- stopped -> cancelled;
- error/interrupted -> failed.

Completion event ID remains source-scoped to the migration job ID and uses the existing delivery ledger for idempotency.

Do not emit completion from audit records or bridge results.

Do not treat a successful `START_MIGRATION_JOB` bridge result as a completion event.

## Direct MCP lost-response ambiguity

A direct MCP caller can theoretically lose the response after the job has been durably queued.

Retrying with the same approval is safe:
- the approval is already consumed;
- no second job should be created.

The retry may therefore return an approval error while the original job continues. That is a safe false-negative.

For this first slice, do not add:
- client-selected job IDs;
- arbitrary idempotency keys;
- approval-to-job search;
- general job listing.

Those are usability/recovery extensions, not required to prevent duplicate mutation. Existing completion delivery and local private state provide operator evidence. A later read-only discovery improvement can be reviewed separately if real use shows it is needed.

## Compatibility

Adding new MCP tools and bridge enum actions is additive.

Do not remove or rename:
- `apply_migrations`;
- `migration_status`;
- `APPLY_MIGRATIONS`;
- `MIGRATION_STATUS`.

Existing clients continue to receive synchronous behavior unless they explicitly choose the new start action.

Bridge protocol version can remain v1 for this additive action extension because existing valid request shapes and meanings do not change.

## Fault-containment requirements

AI/client remains intent, never authority.

The async path must preserve:
- fixed allow-listed action;
- staging-only mutation;
- separate human approval;
- exact plan binding;
- emergency-stop checks;
- fixed migration command from trusted project configuration;
- DatabaseManager-owned lock/backup/execution;
- no shell/arbitrary SQL;
- no automatic restore;
- no automatic retry/resume;
- bounded output-free durable metadata;
- replay ambiguity never causing duplicate execution.

A client must not be able to:
- choose executable/cwd/DSN;
- provide a raw binding fingerprint;
- provide the expected commit directly to the public start tool;
- select a migration job storage path;
- self-assert approval;
- convert a sync approval into async authority.

The server computes all private expected evidence after approval binding recomputation.

## Smallest justified CODE follow-up

Task 49 is justified.

### Task 49 — explicit asynchronous migration start/status integration

Scope:
1. add `migration_async` as a distinct approval operation;
2. add an async migration approval-material helper wrapping canonical migration material with fixed execution mode;
3. instantiate the Task 44 `MigrationJobRunner` only when private migration-job storage is configured;
4. add MCP tools:
   - `start_migration_job(project, approval_id)`;
   - `migration_job_status(job_id)`;
5. preserve approval-consume -> durable queued -> worker ordering;
6. add bridge actions:
   - `START_MIGRATION_JOB`;
   - `MIGRATION_JOB_STATUS`;
7. extend the local MCP executor allow-list and strict argument/result validation only for those actions;
8. preserve existing synchronous migration and deployment migration code unchanged;
9. use the already-integrated completion source unchanged.

Required adversarial validation:
- sync approval cannot authorize async start;
- async approval cannot authorize sync `apply_migrations`;
- async approval binding includes fixed execution mode;
- approval is consumed before queued persistence is attempted;
- enqueue/storage failure after approval consumption never invokes migration;
- successful start returns one bounded 32-hex job ID and nonterminal state;
- no client-supplied commit/fingerprint/path/command is accepted;
- bridge duplicate after start does not create a second job;
- bridge result-persistence/finalize ambiguity does not replay start;
- migration job status accepts only job ID and exposes no private fields;
- existing `migration_status` remains unchanged;
- existing `apply_migrations` remains synchronous;
- deployment-triggered migrations remain synchronous;
- completion remains terminal/idempotent and separate from start result;
- full fault-containment, Ruff, pytest, whitespace, build artifact and clean demo remain green.

## Explicit non-goals

Task 49 must not add:
- migration cancel/kill;
- automatic retry/resume;
- arbitrary SQL;
- arbitrary executable or cwd;
- production database mutation;
- automatic restore;
- job listing/search by arbitrary criteria;
- approval-to-job lookup;
- generic async action framework;
- changes to Runner Fabric authority;
- changes to deployment-triggered migration ordering.

## Conclusion

Task 44 provides enough durable evidence to support an additive async migration contract.

The safe integration is a **new explicit async job action with separate human approval**, not a semantic change to `apply_migrations`.

This keeps current clients stable, keeps bridge replay fail-closed, makes the operator-approved execution mode explicit, and reuses the proven Task 44 substrate without moving database authority into the transport layer.
