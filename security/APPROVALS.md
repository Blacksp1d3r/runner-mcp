# Human approval gates

Runner MCP requires a separate human approval for the highest-risk staging actions:

- database migration apply;
- staging deployment;
- one-step code rollback.

The MCP client can request and inspect an approval plan, but it cannot approve one.

## Local human boundary

Approval is performed only through the local Runner MCP CLI on the controlled host:

```bash
runner-mcp approval list
runner-mcp approval status APPROVAL_ID
runner-mcp approval approve APPROVAL_ID
```

The final command shows the safe action summary and requires an explicit confirmation phrase containing the approval ID prefix.

No MCP tool exists for changing an approval from pending to approved. This keeps the approval boundary outside the AI client's authority.

## Short-lived and single-use

Approvals default to ten minutes and can be configured only between 60 and 1800 seconds.

An approval is:

- bound to one action;
- bound to one project;
- bound to a cryptographic fingerprint of the concrete plan;
- single-use;
- expired automatically after its TTL.

Consumed approvals cannot be replayed.

## Plan binding

Deployment approval binds the approved clean Git commit plus the configured deployment/service/database plan held by the running service.

Rollback approval binds the current and direct previous release. A changed current or target release fails closed.

Migration approval requires a clean Git working tree and binds the Git HEAD plus the configured database/migration profile. Source changes after approval invalidate the approval.

## Environment gate

Mutating project actions are currently permitted only when the configured environment is exactly `staging`.

Production projects remain read-only. This applies even if another permission or service flag would otherwise permit the action.

Production write capability is deliberately outside the current roadmap implementation.

## Storage

Approval state is stored in a private 0700 directory. Individual approval files and the approval lock use mode 0600.

Public MCP/CLI output never exposes the binding fingerprint or private host paths.
