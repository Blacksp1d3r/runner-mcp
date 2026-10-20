# Owner-local Claude/Qwen coding workspaces through Runner-MCP (#747)

## What it does

`coding_workspace_preflight(worker_id)` is read-only. `coding_workspace_prepare(worker_id, work_unit_id)` allocates **only** two owned 0700 folders under the exact root already created by the operator: `jobs/<work_unit_id>` and `patches/<work_unit_id>`. It reports `prepared`, `already_prepared`, `blocked` or `unavailable`, with no absolute path. The worker may write files there later under separately qualified task authority; this tool does **not** checkout source, send prompts, call models, or run tests.

One runtime is fixed to exactly one worker alias and one local non-root operating-system account by trusted private configuration:

```text
RUNNER_MCP_CODING_WORKSPACE_WORKER=claude
RUNNER_MCP_CODING_WORKSPACE_OWNER=<approved-local-dedicated-account>
RUNNER_MCP_CODING_WORKSPACE_ROOT=<pre-existing-absolute-worker-owned-root>
```

For Qwen, use `qwen` and a trusted root **inside the isolated guest**, not a path on the host. These values belong in an owner-private service configuration, never a GitHub file, chat transcript, or general Runner-MCP env handoff. With no complete binding, the universal MCP tool remains visible but responds `private_binding_unavailable` or `private_binding_incomplete` without effects. The serving process must already be the **same effective UID** that owns the root; a shared central Runner-MCP user cannot impersonate the dedicated worker or cross into a guest. Existing `jobs` and `patches` must be same-owner private directories (0700). The configured root itself may be owner-owned 0755 if not group/other writable.

## Operator flow (after authorized deployment)

1. Qualify exact installed source/tool catalogue and owner-local UID for the correct worker. Use current pre-existing worker runtime or an already-approved rootless first-party service binding. **Do not** launch a new unqualified daemon just to use the tool.
2. Check `coding_workspace_preflight("claude")` or `coding_workspace_preflight("qwen")` using the authenticated **correct-host** MCP client.
3. Call `coding_workspace_prepare("claude", "example-task-1")` on the Claude endpoint, or `coding_workspace_prepare("qwen", "example-task-2")` on the Qwen guest endpoint. A repeated same worker/task request is idempotent; no caller-controlled path/host/UID/symlink.
4. Verify returned original-client request ID and effect before a separate model work assignment. Future Fabric-issued cross-host commands still require dedicated signed/fenced Agent Bus issuer, exact destination identity, durable result/outbox/terminal ACK and replay denials; relay UNKNOWN remains NO_DISPATCH.

## Safety and limits

- 128 existing task-directory pairs maximum per worker-root. Never delete old tasks automatically; storage quota, task-retention and backups are independent policy.
- Fail closed for symlinks, unsafe owner/mode, mismatched worker/UID, incomplete pair, invalid work-unit ID, unconfigured root or full namespace. Partial create cleanup never removes user files; uncertainty returns `workspace_recovery_required`.
- No generic `mkdir`/shell/SSH/Incus/sudo executor, arbitrary environment overwrite, general cross-host file access, GitHub push or model subscription/API configuration.
- Source merge or remote tool visibility is not actual worker activation. The first host-bound authenticated request/response remains a separate operator/Agent Bus milestone.

Tracking: Runner-MCP #747, Fabric #972 (Claude), #1579 (Qwen).
