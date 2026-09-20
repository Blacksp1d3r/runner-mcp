# Operator safety and rollback retention

Runner MCP must remain safe even when an agent makes a bad decision. Operator safety therefore lives outside normal tool execution and is fail-closed.

## External emergency stop

A private runtime setting points to an operator-controlled stop file:

`RUNNER_MCP_OPERATOR_STOP_FILE`

The public repository never contains the real path.

When the file exists:

- read-only tools remain available;
- cancel/stop operations remain available;
- new tests, service changes, backups, migrations, deploys and rollbacks are blocked;
- long-running jobs must observe the stop state and terminate at a safe checkpoint;
- database work must not be interrupted in a way that risks corruption.

The stop mechanism is intentionally external to MCP. An agent cannot clear it through a normal MCP tool.

## First-run retention confirmation

An unattended server process must not ask interactive questions on every reboot. Instead, Runner MCP starts future operator capabilities in read-only mode until the owner has explicitly selected or accepted retention values.

The gate is:

`RUNNER_MCP_RETENTION_CONFIRMED=true`

Until this is true, operator actions fail closed.

Default values shown in the public example are only proposed safe starting points:

- minimum releases to keep: 20;
- minimum release age before deletion: 90 days;
- database PITR retention: 30 days;
- pre-migration backup retention: 180 days.

Private runtime configuration may choose stricter or longer values.

## Release retention uses count AND age

A code release is deletable only when both conditions are true:

1. it falls outside the minimum number of newest releases to retain;
2. it is at least the configured minimum age.

Example: with 20 releases and 90 days, a year with only 10 deployments keeps all 10. A busy month with 50 deployments still keeps every release younger than 90 days.

## Database history is different from code history

Rolling back application code must not automatically roll back the database.

Preferred order:

1. reactivate a compatible previous code release;
2. keep the current database when migrations are backward-compatible;
3. use database restore only when a separate recovery plan proves it is necessary.

A database restore can discard data created after the restore point. It therefore always requires explicit human approval.

Automatic production database restore is prohibited.

## Point-in-time recovery

For PostgreSQL deployments, later database phases should support point-in-time recovery using a base backup plus WAL archiving where practical.

PITR allows recovery to a selected moment close to the failure instead of blindly restoring an old daily backup.

PITR retention and pre-migration backup retention are separate controls.

## Rollback depth

One approved code rollback action may move back exactly one release.

After the rollback:

1. stop;
2. run health checks;
3. inspect database compatibility and application state;
4. require a new decision before another rollback.

Runner MCP must never cascade automatically through multiple historical releases.

## Dangerous-operation preflight

Before migration, deploy or rollback, future phases must record a recovery plan containing at least:

- currently active release;
- target release;
- database migration presence;
- backup or PITR recovery point;
- database compatibility assessment;
- expected data-loss window if a database restore became necessary;
- health checks to run after the action.

If recovery safety cannot be determined, the operation must fail closed.

## Safe stop behavior for future jobs

Different operations require different stop semantics:

- tests and analysis jobs: terminate child processes promptly;
- service actions: do not start the next step;
- deploys: stop at a defined checkpoint and preserve the previous active release;
- migrations: prefer transactional migration behavior and do not kill a database operation at an unsafe point;
- database restore: never start without explicit approval.

These rules are mandatory requirements for Phases 3 through 7.
