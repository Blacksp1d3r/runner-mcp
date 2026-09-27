# Task 46 — cross-process release-mutation lock boundary review

Date: 2026-09-24

Status: **COMPLETE — review only. No mutation locking behavior changed here.**

## Why this review became necessary

Task 40 specified that local release pruning must share the deployment/rollback project lock.

Implementation preparation for Task 43 found that the current `DeploymentManager._lock_for()` returns a per-instance `threading.Lock`.

That is sufficient to serialize deploy/rollback work inside one Runner MCP process, but Task 43 is intentionally a local CLI action. A CLI process and the long-lived MCP/server process do not share Python thread locks.

Therefore Task 43 cannot safely proceed using the existing lock contract. A local prune could otherwise race:

- deployment release creation;
- migration-before-activation state changes;
- `current` symlink activation;
- one-step rollback activation/recovery;
- service restart/health recovery tied to release state.

This is a real cross-process safety gap for the proposed local mutation path, not a reason to weaken Task 43's local-only authority.

## Executive conclusion

A shared **cross-process release-operation lock** is required before Task 43.

The smallest safe implementation is a Linux `fcntl.flock` lock file inside each configured private deployment release root, combined with the existing in-process threading lock for server concurrency.

Recommended lock order for deploy/rollback:

1. acquire existing per-project in-process thread lock, non-blocking;
2. validate/prepare the private release root;
3. acquire the release-root cross-process file lock, non-blocking;
4. perform release mutation work;
5. if database mutation is needed, acquire it only through the existing `DatabaseManager` path after the release-operation lock is already held;
6. release file lock;
7. release thread lock.

Recommended lock order for local prune:

1. validate configured staging deployment/release root;
2. acquire the same release-root cross-process file lock, non-blocking;
3. recompute strict retention state and execute the bounded prune transaction;
4. release file lock.

This preserves the established deployment -> database ordering and prevents local pruning from racing a server deploy/rollback.

## Lock location and identity

Use one fixed private path under the configured release root, for example:

`<release_root>/.runner-mcp-operation.lock`

Why the release root is the correct namespace:

- it is already the private authority boundary for the project's release history;
- it is stable across Runner MCP processes;
- each configured deployment root identifies exactly one release mutation domain;
- no global hostname/project-code mapping is required;
- lock paths never need to appear in public output.

Do not put the lock under the project source tree. Source checkout changes or repository permissions must not control operational locking.

Do not derive a caller-supplied lock path.

## Safe lock-file open contract

The helper must:

- require an absolute, existing, non-symlink release root;
- verify the release root is a directory with mode 0700, consistent with existing deployment storage rules;
- construct only the fixed child filename;
- reject a symlink at the lock path;
- open with `O_CREAT | O_RDWR` and `O_NOFOLLOW` when available;
- create with mode 0600;
- verify with `fstat` that the opened object is a regular file;
- verify mode 0600;
- verify file owner UID matches the current process UID;
- verify the opened file still resolves to the expected fixed child under the validated release root where a stable identity check is available;
- never read caller-controlled content from the file;
- never place secret/process metadata in it.

The lock file may be zero bytes. Its existence is not itself evidence that an operation is active.

## Lock acquisition semantics

Use `fcntl.flock(fd, LOCK_EX | LOCK_NB)`.

Contention must fail immediately with a bounded category such as:

`release_operation_busy`

Do not wait indefinitely and do not poll/retry automatically.

Fail-fast behavior matters because a delayed prune/deploy may run after its plan, approval, source commit or retention state is stale.

## Crash semantics

The operating system releases the `flock` when the owning file descriptor is closed or the process terminates.

The lock file itself intentionally persists. Do not delete it at operation completion.

This avoids stale-file cleanup races: a persistent zero-byte 0600 lock file is merely the stable rendezvous object; the kernel lock state is the authority.

Do not use PID text, timestamps or 'locked=true' file contents as authority.

## Why keep the existing thread lock

Keep the `threading.Lock` in DeploymentManager for now.

It already provides simple same-process exclusion and avoids relying on nuanced same-process file-lock semantics among multiple threads/file descriptors.

The combined model is:

- thread lock serializes deploy/rollback calls inside one manager process;
- flock serializes that process against other Runner MCP/CLI processes sharing the release root.

All server release mutations should acquire both in the fixed order: thread lock first, file lock second.

Local prune has no shared thread lock and therefore acquires the file lock directly.

## Reentrancy

Do not make the cross-process lock implicitly reentrant.

Nested acquisition from the same operational call graph should be avoided by ownership design rather than hidden recursion counters.

Deployment manager methods that already own the release-operation lock may call private helpers that assume it is held; those helpers must not reacquire it.

## Mutation-path inventory

The following release-root mutation paths must be inside the shared file lock:

- `DeploymentManager.deploy()` from before release creation/state snapshot through final activation/recovery completion;
- `DeploymentManager.rollback_one()` from fresh rollback-plan recomputation through activation/restart/health recovery completion;
- future Task 43 release quarantine/deletion;
- future prune transaction recovery that changes quarantine or active release state.

Read-only release listing/rollback planning/retention preview do not need the exclusive file lock, but any plan used for mutation must be recomputed after the mutation lock is acquired.

## Current symlink activation implications

`_activate_release()` atomically replaces the `current` symlink and fsyncs the release root.

The shared lock does not replace those atomicity/durability steps. It prevents another Runner MCP release mutation process from changing the same release-root state concurrently.

## Deployment test duration

Current deploy holds its in-process lock across required tests and subsequent release/migration/activation work.

The cross-process lock should cover the same mutation transaction boundary rather than being acquired only immediately before `current` activation.

Reason: local pruning must not remove a release that deployment has just created or alter historical state while the deployment plan is being materialized.

This means a local prune can fail `release_operation_busy` for the entire deployment. That is intentional and safer than waiting.

## Database lock ordering

Some deployments call `DatabaseManager.apply_migrations()` while the deployment release lock is held.

Keep one global ordering:

`release thread lock -> release flock -> database operation lock`

Never add a path that acquires the database operation lock and then tries to acquire the release flock.

Task 43's first slice does not touch backups/database state, so it acquires only the release flock.

Future combined release+backup pruning must follow the same release-before-database order.

## Service-manager interaction

Deploy/rollback may restart the configured service while the release lock is held.

Keep the release lock through health/recovery decisions so another process cannot prune/reactivate release state while service recovery is still deciding which release is authoritative.

Do not share this lock with unrelated service start/stop actions that do not alter release-root state.

## Supported platform

Runner MCP's current operational target is Linux/systemd-oriented. A first implementation may explicitly require `fcntl.flock` support.

If `fcntl`/`flock` is unavailable, release mutation must fail closed rather than silently falling back to process-local locking.

## Public/privacy contract

Public errors/status may say only that another release operation is active/busy.

Never expose:

- lock path;
- release root path;
- file descriptor;
- PID/process identity;
- hostname;
- raw OSError text.

## Recommended reusable primitive

Create a small private helper, for example `release_operation_lock.py`, with a context manager such as:

`acquire_release_operation_lock(release_root, *, blocking=False)`

The helper owns only file-system validation/open/flock/release behavior.

It must not know about projects, deployments, approvals or pruning policy.

`DeploymentManager` remains responsible for the in-process project thread lock and calls this primitive after resolving the configured release root.

Task 43's pruner calls the same primitive against the configured release root.

## Required multi-process regression tests

At minimum:

- two separate processes opening the same private lock object cannot both acquire exclusive non-blocking locks;
- second process gets only a bounded busy error;
- lock releases after normal fd close;
- lock releases after holder process exits without cleanup;
- persistent lock file after holder exit can be reacquired;
- symlink lock path is rejected without following referent;
- non-regular lock path is rejected;
- broad-permission lock file is rejected or safely repaired only at controlled creation time;
- wrong-owner lock file is rejected;
- unsafe/broad/symlink release root is rejected;
- different release roots do not block each other;
- same-process DeploymentManager concurrent operations remain excluded by the thread lock;
- deploy/rollback acquire file lock before any release-tree mutation;
- database migration from deployment occurs only after release file lock acquisition;
- public failure text does not contain lock/release-root paths or raw exceptions.

## Code follow-up justified

Task 48 is justified as a narrow CODE prerequisite:

- add the reusable cross-process release-operation lock primitive;
- integrate it into `DeploymentManager.deploy()` and `rollback_one()` without changing approval or public execution authority;
- preserve existing thread-lock behavior;
- add multi-process/adversarial tests;
- no pruning code in Task 48.

After Task 48 is integrated, Task 43 may use the exact same primitive and proceed with its previously reviewed one-release local pruning scope.

## Non-goals

This review does not authorize:

- a global generic filesystem lock API;
- arbitrary lock paths;
- remote lock management;
- changing database-operation lock semantics;
- prune execution before Task 48;
- deleting releases/backups;
- changing deployment/rollback approval rules.

## Conclusion

Task 43 exposed a process-boundary assumption that the current in-memory deployment lock cannot satisfy.

A fixed private release-root `flock` rendezvous object, combined with the existing thread lock and a strict release->database ordering, is the smallest auditable solution. Implement that independently in Task 48; only then should local pruning mutate release storage.
