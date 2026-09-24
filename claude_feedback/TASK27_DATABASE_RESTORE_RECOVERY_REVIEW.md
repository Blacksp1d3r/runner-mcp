# Task 27 — database restore / recovery boundary review

Date: 2026-09-24

## Scope

Review only. No database is restored, no restore executable is invoked, no approval action or mailbox action is added, and no runtime/database state is changed here.

Goal: define the safety and approval boundary for any future database restore/recovery capability while preserving Runner MCP's existing fail-closed separation between code rollback and database recovery.

## Current implemented boundary

Runner MCP currently supports:

- PostgreSQL custom-format backups through a fixed trusted `pg_dump`;
- private backup storage under a configured root;
- 0700 backup directories;
- 0600 dump and metadata files;
- safe public backup metadata only;
- migration status/apply with bounded scrubbed output;
- mandatory pre-migration backup before migration apply;
- code rollback that is blocked across a database-migration boundary.

Runner MCP does **not** currently support:

- database restore;
- `pg_restore` execution;
- WAL archive management;
- PITR target selection;
- restore approvals;
- restore MCP tools;
- restore mailbox actions;
- automatic restore after migration failure.

This absence is intentional and should remain fail-closed until each layer is separately proven.

## Existing safety invariants

The current code already establishes several important policy anchors:

- `ActionClass.DATABASE_RESTORE` exists as a distinct action class;
- retention policy requires explicit approval for database restore;
- retention policy cannot enable automatic production database restore;
- `OperatorSafetyGuard.assert_database_restore_approved()` rejects restore without explicit human approval;
- ordinary mutating project actions are staging-only;
- the bridge protocol has no database-restore action;
- `ApprovalManager.ALLOWED_ACTIONS` does not include database restore;
- Phase 3.7 explicitly keeps restore outside the mailbox allow-list.

These are design reservations, not evidence that restore execution is implemented.

## Recovery classes must remain distinct

### 1. One-backup logical restore

A logical restore means restoring one known Runner MCP PostgreSQL custom-format backup.

Potential future tool:
- fixed trusted `pg_restore`;
- exactly one selected backup ID owned by the configured project;
- no caller-supplied dump path or arbitrary pg_restore arguments.

This is the only restore class that appears bounded enough for a future Runner MCP implementation.

### 2. WAL / PITR recovery

PITR is materially different from restoring one dump. It may require:

- WAL archive configuration;
- base-backup lifecycle;
- recovery target time/LSN/name;
- timeline selection;
- database/server restart orchestration;
- archive completeness verification;
- replication/storage integration;
- infrastructure-specific PostgreSQL ownership and permissions.

PITR therefore remains **separately deferred**. It must not be represented as an option on a simple logical-restore command.

### 3. Code rollback

Code rollback changes only the active release pointer and service state.

It must never:
- select a database backup;
- call pg_restore;
- infer that a matching database restore is safe;
- cross a migration boundary automatically.

The existing behavior is correct: code rollback is blocked when the active release crossed a database migration boundary.

### 4. Migration failure recovery

A failed migration currently keeps its mandatory pre-migration backup and reports `database_restore_performed: False`.

That backup is a recovery point, not authorization to restore automatically.

Runner MCP must not auto-restore after:
- migration command failure;
- timeout;
- deployment health failure;
- code rollback failure.

## Backup identity available today

The current safe backup metadata exposes:

- `backup_id`;
- project;
- kind: `manual` or `pre_migration`;
- creation time;
- size;
- PostgreSQL engine;
- availability.

A backup ID has a strict timestamp/random-suffix format and the dump is expected at a project-owned private location with mode 0600.

The metadata does not currently include a cryptographic content digest.

For a future restore, metadata identity alone is not enough to bind a human decision to exact dump bytes.

## Recommended restore authorization model

Database recovery should **not** be added to the current remote approval request/consume path first.

The current approval system is designed for a remote client to request a plan, a local operator to approve it, and the remote client to consume that approval for migration/deploy/code rollback.

Database restore has a different risk profile:
- it can destructively replace database state;
- it may be needed specifically during incident recovery;
- it should remain unavailable to mailbox/remote clients in the first implementation.

### Recommended first execution authority

Future actual restore, if implemented, should be:

- local CLI only;
- staging only;
- unavailable through MCP/mailbox;
- unavailable through the GitHub bridge;
- protected by a dedicated typed local confirmation bound to a previously generated restore plan;
- single-use;
- revalidated immediately before execution.

No generic `ApprovalManager` action needs to be added merely to support the first local recovery path.

## Emergency-stop semantics

An ordinary database restore is a mutation, so it must never silently bypass the emergency-stop model.

However, incident recovery benefits from keeping all normal mutations stopped while the operator performs a deliberate restore. Requiring the operator to disable the emergency stop would re-enable unrelated mutations and is therefore undesirable.

Recommended model:

- normal migration/deploy/service mutations remain blocked while emergency stop is active;
- a future **local-only recovery command** may require the emergency stop to be ACTIVE as a maintenance/quiescence gate;
- this local recovery exception must be explicit and narrow, analogous in spirit to local self-update installation recovery;
- no remote or mailbox action may use that exception;
- restore completion does not automatically clear the emergency stop.

This requires a separate recovery-specific guard, not a call to the normal `assert_project_action_allowed(DATABASE_RESTORE)` path that would simply fail while stopped.

## Pre-restore evidence required

Before actual restore can ever be enabled, a read-only preflight must prove at least:

1. project exists and is staging;
2. database config exists and engine is PostgreSQL;
3. backup root/project directory is safe and contained under the configured root;
4. selected backup ID has the exact allowed form;
5. metadata identity matches backup ID + project + PostgreSQL engine;
6. metadata file and dump are regular non-symlink files with private permissions;
7. dump size is positive and matches the recorded metadata size;
8. a trusted non-symlink executable `pg_restore` is available;
9. `pg_restore --list` can parse the archive successfully using fixed arguments;
10. preflight output is bounded and never exposes object data, DSN, paths or raw stderr;
11. the exact archive bytes are cryptographically fingerprinted for private plan binding;
12. no other database operation for the project is active.

For the first preflight, the archive fingerprint should remain internal to the plan binding. Public/status output does not need to expose a dump hash.

## TOCTOU / binding requirement

A future restore decision must be bound to the exact backup bytes, not only the backup ID.

Recommended plan binding contains private canonical values such as:

- project;
- backup ID;
- backup content SHA-256;
- backup size;
- database configuration fingerprint;
- restore mode;
- environment = staging.

Immediately before restore, all values must be recomputed/revalidated.

If archive bytes or target configuration changed, the plan is invalid and a new local plan/confirmation is required.

The implementation must also address the interval between final validation and `pg_restore` opening the archive. A later implementation review should choose a stable-open-file or equivalent fail-closed strategy rather than assuming path validation alone removes all same-user TOCTOU risk.

## Pre-restore safety backup

Any future actual logical restore should first create a **new manual/pre_restore recovery point** of the current target database before destructive restore begins, unless the target is proven empty and the operator explicitly selected a separately designed initialization workflow.

This likely requires a new backup kind such as `pre_restore`.

Do not overload `pre_migration` because its retention and meaning are different.

The safety sequence should be:

1. emergency stop active;
2. validate restore plan;
3. acquire database-operation lock;
4. revalidate plan;
5. create pre-restore backup;
6. revalidate stop/plan;
7. execute restore;
8. verify restore outcome;
9. keep emergency stop active for operator verification.

Failure after step 5 keeps the pre-restore recovery point. No automatic second restore/rollback cascade is allowed.

## Restore execution constraints for a later task

If actual logical restore is eventually implemented:

- detect a fixed trusted `pg_restore` binary; no caller-supplied executable;
- DSN goes only into a child environment, never argv/output;
- `shell=False`;
- fixed bounded argument set;
- no arbitrary schema/table/role/owner/filter arguments;
- no caller-supplied dump path;
- stdin/output handled so archive/path details do not escape;
- bounded timeout with process-group termination;
- stdout/stderr either suppressed or strictly bounded/scrubbed;
- no SQL or restored data returned to the caller;
- no automatic retry that could replay a partially applied destructive restore.

Whether restore should target an existing database with `--clean` or require a separately prepared empty target is a destructive semantic decision and must be resolved by a later implementation review. It must not be guessed in this boundary review.

## Production policy

Automatic production database restore remains prohibited.

Recommended v0.x boundary:
- Runner MCP does not execute production database restore at all;
- production recovery remains an external DBA/operator procedure;
- Runner MCP may eventually expose read-only backup/recovery readiness metadata if it can do so without leaking infrastructure.

This is stricter than merely requiring approval and is consistent with the current project rule that production mutations are read-only/disabled.

## WAL / PITR prerequisites

PITR should not be queued as an implementation follow-up yet.

Before any PITR implementation, a separate design must define:

- base-backup source and provenance;
- WAL archive storage contract;
- integrity/completeness checks;
- retention interaction;
- timeline/target semantics;
- target database lifecycle;
- service/database stop/start authority;
- verification after recovery;
- operator rollback path after a failed recovery;
- infrastructure-specific privilege boundary.

Those prerequisites do not exist in the current generic project model.

## Safe metadata surface

A future read-only restore preflight may safely return:

- project code;
- backup ID;
- backup kind;
- created_at;
- size_bytes;
- engine;
- availability;
- preflight state using bounded categories;
- whether local restore eligibility is blocked by environment/configuration.

It should not return:

- dump path;
- backup root;
- DSN or database endpoint;
- database name/user/host;
- pg_restore path;
- archive listing/object names;
- SQL;
- archive hash;
- raw command output;
- exception text.

## Smallest recommended CODE follow-up

The smallest justified implementation is **read-only local restore preflight/plan only**.

Proposed scope:

- add a private/local `DatabaseManager.restore_preflight(project, backup_id)` or equivalent helper that performs strict archive/metadata validation and fixed `pg_restore --list` parseability check;
- add a local CLI command such as `runner-mcp database restore-plan PROJECT BACKUP_ID`;
- do not add actual restore execution;
- do not add `database_restore` to generic approvals;
- do not add MCP/bridge/mailbox actions;
- do not add PITR;
- do not change production mutation policy;
- return only safe bounded plan metadata;
- keep the exact archive digest/private binding internal.

This slice creates evidence needed to design an actual local restore later without putting destructive authority in the product prematurely.

## Required regression matrix for restore-preflight

- unknown project rejected;
- non-staging project rejected;
- unconfigured database/backup root rejected;
- malformed backup ID rejected before filesystem traversal;
- metadata project/ID/engine mismatch rejected;
- symlink metadata or dump rejected without following referent;
- broad-permission/irregular dump rejected;
- missing/empty/size-mismatched dump rejected;
- trusted pg_restore detection refuses symlink/non-executable candidates;
- fixed `pg_restore --list` uses `shell=False` and no DSN;
- parse failure returns bounded category only;
- raw stderr/object listing/path cannot escape;
- archive fingerprint is not exposed;
- no database connection or mutation occurs;
- no approval/mailbox action is created;
- emergency-stop state does not affect the read-only preflight;
- production project reports ineligible rather than becoming restorable.

## Conclusion

The current project has the right fail-closed foundation: backups exist, migration failures preserve them, database restore is a distinct safety class, production auto-restore is prohibited, and no remote restore authority exists.

Keep that boundary.

The next safe step is a local read-only restore-preflight/plan. Actual staging restore, WAL/PITR and any remote restore capability must remain separate later decisions.
