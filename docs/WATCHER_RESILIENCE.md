# GitHub mailbox watcher resilience

Runner MCP treats mailbox execution, result publication, liveness and notification delivery as separate concerns.

The public resilience contract is infrastructure-neutral. It does not contain repository names, hostnames, paths, service names, credentials or transport endpoints.

## Request lifecycle

The replay ledger now tracks two lifecycle states:

- `claimed`: the watcher accepted the request ID and reserved it for execution;
- `completed`: the watcher finished the request and the authoritative result is durable.

The watcher must claim before execution and mark the request completed only after its bounded result has been safely persisted.

An existing completed request ID is never executed again.

## Restart recovery

After a watcher restart, a request/result pair is classified as follows:

| Result exists | Replay state | Recovery disposition | Execute? |
| --- | --- | --- | --- |
| yes | any/none | `result_exists` | no |
| no | none | `process` | yes, after a normal replay claim |
| no | `claimed` | `ambiguous_claim` | no automatic retry |
| no | `completed` | `result_missing` | no automatic retry |

`ambiguous_claim` means the watcher cannot prove whether execution had already begun or completed before interruption.

`result_missing` means the ledger says execution completed but the transport-visible result is missing.

Both conditions are fail-closed and require recovery attention. The watcher must never resolve either state by blindly rerunning the operational action.

For `result_missing`, a transport may republish a previously persisted safe result if it has one. Republishing a result is not task execution.

### Explicit fail-closed operator resolution

When no trustworthy prior safe result exists, Runner MCP provides a local operator escape hatch that still refuses action replay:

```bash
runner-mcp github-watcher resolve REQUEST_ID
```

This command is local CLI only and requires an exact confirmation phrase. It does not call the bridge executor.

Before changing recovery state it verifies all of the following:

- the original request still parses under the strict bridge protocol and matches its mailbox filename;
- no durable result already exists;
- the replay ledger contains the exact same request fingerprint/action;
- the replay state is already `claimed` or `completed`.

Only then it publishes a bounded terminal failed result with error code `RECOVERY_REQUIRED` and an explicit statement that no action was replayed. If the request was still `claimed`, lifecycle completion happens only after that safe failure result is durable.

The watcher cursor is not reset or advanced by the resolve command. The operator runs a normal watcher cycle afterwards. That cycle sees the durable result, reconciles replay state, and advances the cursor through the ordinary restart-safe path.

A request with no replay record is rejected by this command because normal processing is still authoritative. A request with an existing durable result is also rejected because normal watcher reconciliation is authoritative. Result-persistence failure leaves the prior replay state unchanged.

## Backlog and stale requests

The public heartbeat exposes only:

- `state`: `healthy`, `backlog` or `degraded`;
- pending request count;
- stale request count;
- recovery-attention count;
- age in seconds of the oldest pending request.

It intentionally exposes no request IDs or infrastructure metadata.

A fresh unclaimed request produces `backlog`.

The watcher becomes `degraded` when:

- transport health is degraded;
- a pending request exceeds the configured stale threshold;
- an ambiguous claimed request exists;
- a completed request is missing its result.

The stale threshold is bounded to 30 seconds through 24 hours in the reusable public contract.

Heartbeat freshness itself should be established by the transport metadata that publishes the heartbeat, such as the modification time of the heartbeat record. The payload therefore does not need to disclose a local clock, host identity or process identity.

## Transport retry policy

Only transient transport failures may be retried automatically.

The generic retryable categories are:

- timeout;
- rate limited;
- transport unavailable.

The default public retry delays are bounded to 2 seconds and 5 seconds after the original attempt.

Authorization failures and invalid responses are not automatically retried.

Most importantly, transport retry policy applies only to:

- reading/writing mailbox transport records;
- publishing a heartbeat;
- publishing a result already produced;
- delivering a notification already derived from a completed result.

It does not authorize re-execution of `run_tests` or any other Runner MCP action.

## Relationship to completion feedback

The sequence is:

1. validate request;
2. claim request ID;
3. execute the allow-listed Runner MCP action;
4. persist the bounded/scrubbed result;
5. mark replay lifecycle `completed`;
6. derive a completion event;
7. deliver the notification independently.

If steps 6 or 7 fail, the operational action remains completed and is not repeated.

See [COMPLETION_FEEDBACK.md](COMPLETION_FEEDBACK.md).

## Private watcher migration

A private watcher adopting this contract should:

- use the shared strict request parser;
- use the shared replay ledger;
- refuse changed content under an existing request ID;
- mark lifecycle completion only after durable safe result publication;
- scan backlog after restart;
- classify ambiguous/missing-result states rather than rerunning them;
- publish a sanitized heartbeat;
- retry only transient transport operations;
- keep notification delivery idempotent.

Deployment-specific supervisor configuration remains private and is not part of this public repository.


## Processor integration

The transport-neutral processor in `runner_mcp.bridge_processor` implements the lifecycle ordering described here.

A private watcher should not duplicate that orchestration. Its remaining responsibilities are transport-only:

- discover request records;
- provide an explicit allow-listed executor adapter;
- persist already-scrubbed results;
- publish heartbeat state;
- deliver completion notifications independently.

This keeps restart/replay semantics in tested public code while deployment-specific credentials and mailbox locations remain private.


## Incremental GitHub watcher

The public `runner_mcp.github_watcher` module combines the GitHub mailbox transport, bridge processor, replay ledger and heartbeat contract.

It uses a local request-branch cursor rather than rescanning all historical requests.

First start is deliberately fail-closed:

1. without a cursor, the watcher reports `uninitialized` and executes nothing;
2. the operator explicitly bootstraps the cursor at the current request-branch head;
3. historical requests before that point are not replayed;
4. later cycles compare only fast-forward changes since the cursor.

The cursor is private local state. It is stored with restrictive permissions, file locking, symlink refusal and an expected-previous-SHA check to detect concurrent watcher instances.

A durable existing result is reconciled into replay state without action execution. A claimed request with no result and a completed request with a missing result both require recovery attention and are never blindly rerun.

## External supervisor restart contract

A deployment-specific supervisor may restart the watcher process after a crash or host restart.

The supervisor should only restart the process. It must not:

- delete or reset the replay ledger;
- delete or reset the watcher cursor;
- rewrite request/result mailbox content;
- treat heartbeat failure as permission to rerun an action;
- automatically bootstrap a missing cursor over an unknown backlog.

After restart, the watcher reuses the persisted cursor and replay lifecycle. If the cursor cannot be read, the request branch is no longer a strict fast-forward, or replay/result state is ambiguous, the watcher remains degraded and requires operator recovery.

Supervisor unit names, filesystem locations, credentials and repository/ref values remain private deployment configuration and are intentionally excluded from this public repository.
