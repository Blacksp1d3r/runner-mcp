# Task 37 — local staging database restore execution boundary review

Date: 2026-09-24

Status: **COMPLETE — review only. Restore execution remains deferred.**

## Scope

This review uses the implemented Task 31 read-only restore preflight to decide whether Runner MCP can safely add a first local-only PostgreSQL logical-restore execution path.

No database is restored, created, dropped or switched. No approval, MCP, mailbox, bridge or production mutation authority is added.

## Executive conclusion

Do **not** implement restore execution yet.

Task 31 proves archive identity, private-file safety and parseability, but it does not prove a safe destructive target lifecycle or application quiescence. Those are now the dominant risks.

The current project model has one PostgreSQL DSN for Runner MCP and optional service aliases. It does not define a separately prepared recovery database, does not prove that the configured application service is the only database writer, and does not define an atomic application cutover from the live database to a restored target.

Restoring directly into the currently configured database would therefore create semantics Runner MCP cannot honestly describe as a complete rollback. A custom-format `pg_restore --clean` can remove objects represented in the archive, but it does not prove that unrelated/newer objects outside that archive are gone. Ownership, extensions, database-level settings, active clients and external workers also sit outside the current bounded model.

## What Task 31 now proves

The existing local preflight already gives a strong non-destructive foundation:

- project and PostgreSQL configuration validation;
- staging-only eligibility;
- strict backup ID and metadata identity/shape checks;
- private 0700/0600 storage checks and symlink refusal;
- positive dump-size equality with metadata;
- fixed trusted `pg_restore --list` over the already-open dump descriptor;
- archive bytes hashed before and after parseability validation;
- a private binding fingerprint derived from project, backup ID, size and archive SHA-256;
- the per-project database-operation lock blocks concurrent Runner MCP database work;
- no DSN read, database connection or restore mutation;
- no archive hash/path/object list in public output.

This is sufficient evidence for restore **readiness**, not restore execution.

## Target semantics

### Reject restore-in-place as the first execution model

The first restore implementation must not target the currently configured live database with a generic `--clean` recipe.

Reasons:

1. `--clean` is archive-relative, not proof of an exact database replacement. Objects created after the backup but absent from the archive may survive.
2. Database-level ownership, extensions, roles, ACLs and settings are not fully represented by the current backup contract.
3. Active application connections or external workers may continue writing while restore runs.
4. A partially restored live database creates a difficult recovery state even when command failure is detected.
5. Runner MCP currently cannot prove that every database client was quiesced.

### Safe future target model

If restore execution is ever added, the safer first model is a **separately prepared empty staging recovery database** with an explicit, private recovery-target identity distinct from the currently active application target.

That target must be provisioned outside the first Runner MCP restore slice or by a separately reviewed bounded database-lifecycle capability. Runner MCP must not gain generic `CREATE DATABASE`, `DROP DATABASE`, role management or arbitrary SQL merely to support restore.

Before such a target can be used, the product must also define how the application is deliberately switched to it. The current database DSN in Runner MCP configuration is not evidence that application services use the same connection target.

Therefore there is no safe executable target contract in the current model.

## Quiescence requirements

The per-project `DatabaseManager` lock only serializes Runner MCP's own backup/migration/preflight operations. It does **not** stop application traffic.

A future restore execution requires explicit evidence that the target is quiescent. At minimum:

- the operator emergency stop is ACTIVE so unrelated Runner MCP mutations remain blocked;
- the database-operation lock is held for the entire recovery transaction;
- all configured services that can write to the target are stopped or otherwise proven quiescent;
- external/background writers not represented by configured service aliases are explicitly accounted for;
- quiescence is rechecked immediately before destructive execution;
- restore completion does not automatically restart services or clear the emergency stop.

Runner MCP does not currently model "all database writers for this project", so this requirement is not yet satisfiable generically.

## Emergency-stop behavior

The Task 27 recommendation remains correct: local database recovery should require the emergency stop to be **ACTIVE**, not inactive.

That creates a narrow recovery exception while ordinary migration, deployment and service mutations stay blocked. The exception must be local CLI-only and must never become a generic bypass of `OperatorSafetyGuard`.

A future recovery-specific guard must prove:

- retention policy confirmed;
- operator-stop mechanism configured;
- stop currently active;
- project environment is exactly staging;
- invocation is the dedicated local recovery path.

Restore success or failure must leave the stop active. Only the operator may later clear it through the existing typed local unlock.

## Pre-restore recovery point

Any destructive restore into a non-empty target would require a mandatory fresh **`pre_restore`** logical backup before the first destructive command.

`pre_restore` must be a distinct backup kind. It must not reuse `manual` or `pre_migration` because its purpose and retention obligations differ.

Before that kind is implemented, a separate retention rule is required. Task 34's read-only retention preview correctly treats only existing `manual` and `pre_migration` kinds; adding `pre_restore` must update backup metadata validation and retention semantics together.

If a future target is a separately prepared and independently proven empty recovery database, a pre-restore backup of that empty target has no recovery value. That exception should be explicit in the target contract rather than inferred from restore code.

## Final binding and TOCTOU requirements

Task 31 computes an internal archive binding, but execution would need a stronger complete plan binding.

The private execution binding must include at least:

- project code;
- selected backup ID;
- exact archive SHA-256 and size;
- backup kind;
- staging environment;
- immutable database configuration fingerprint;
- explicit recovery-target identity/fingerprint;
- restore recipe version;
- quiescence contract version;
- whether a pre-restore recovery point is required;
- the expected emergency-stop state.

Immediately before execution, while holding the database lock, Runner MCP must recompute the archive/config/target binding. Any drift invalidates the plan and requires a new confirmation.

The archive must remain opened through the final validation and restore handoff, or use an equivalent stable-descriptor design. Reopening a path after confirmation would reintroduce a same-user TOCTOU window.

## Fixed `pg_restore` execution constraints

If the missing target/quiescence model is later supplied, execution must still use a fixed trusted `pg_restore` binary and a versioned, non-user-extensible argument recipe.

Required properties:

- `shell=False`;
- no caller-supplied executable, dump path, schema/table filters, role, owner, jobs or arbitrary arguments;
- archive supplied through a stable already-validated file descriptor/stdin where supported by the chosen recipe;
- target credential only through a private child environment, never argv/output;
- fixed `--no-owner` and `--no-privileges` semantics consistent with current backups;
- fail-fast behavior such as `--exit-on-error` where compatible with the final target contract;
- one bounded timeout with process-group termination;
- no automatic retry, replay, cascade restore or fallback to another backup;
- raw stdout/stderr suppressed or strictly bounded/scrubbed;
- no SQL, object names, archive listing, DSN or paths returned to the operator.

Whether `--single-transaction` is mandatory depends on the eventual empty-target recipe and must be proven by tests before implementation. It should not be guessed into the current product contract.

## Failure semantics

A restore command failure is terminal for that recovery attempt.

Runner MCP must not:

- retry the same restore automatically;
- restore the pre-restore backup automatically;
- cascade to an older backup;
- clear the emergency stop;
- restart application services;
- mark the database healthy merely because `pg_restore` exited zero.

The operator receives only a bounded failure category and retains all recovery evidence for a deliberate next action.

## Post-restore verification

`pg_restore` success is necessary but not sufficient evidence that the application is ready.

A safe generic verification layer would need at least:

- command completed successfully;
- target remains reachable under a bounded read-only check;
- no restore transaction remains active;
- optional project-specific schema/application invariant checks that are predefined and do not return data;
- operator confirmation before any service restart or emergency-stop clear.

Runner MCP currently has migration status profiles but no generic definition of "this restored database is semantically correct for this application". Reusing arbitrary migration output as recovery proof would be unsafe.

## Approval and authority

Do not add database restore to `ApprovalManager.ALLOWED_ACTIONS`, MCP tools, the GitHub mailbox or bridge.

The first future execution path, if eventually justified, should use a dedicated local typed confirmation bound to a fresh private plan. It remains staging-only and single-use.

Production database restore remains an external DBA/operator procedure.

## Decision on a CODE follow-up

No destructive CODE follow-up is justified now.

The blockers are not archive-validation defects; they are missing product contracts for:

1. a separately identified recovery target;
2. complete writer/quiescence ownership;
3. application cutover/activation;
4. `pre_restore` retention semantics;
5. bounded semantic post-restore verification.

Implementing `pg_restore` before those contracts exist would turn a well-validated archive into unsafe mutation authority.

## Smallest safe next task

A later **review/design task**, triggered by a concrete staging recovery use case, may define the recovery-target and quiescence model. It should inventory every writer for one pilot project and prove how an operator-prepared empty target is identified and activated without adding generic database administration.

Only after that review demonstrates a generic bounded contract should Runner MCP queue restore execution code.

## Explicit non-goals preserved

This review does not authorize:

- restore into the current live database;
- database create/drop/rename or arbitrary SQL;
- WAL/PITR recovery;
- production restore;
- automatic restore after migration/deployment failure;
- remote/MCP/mailbox restore;
- generic approval expansion;
- automatic service restart or emergency-stop clearing;
- retention deletion or pruning.

## Conclusion

Task 31 closed the archive-integrity and read-only preflight gap. Task 37 shows that the next boundary is operational database lifecycle, not command construction.

Keep restore execution deferred until Runner MCP can prove an empty recovery target, complete quiescence and an explicit application cutover contract. In the current architecture, that is safer and more truthful than adding a local `pg_restore` command that appears recoverable but cannot prove what state it leaves behind.
