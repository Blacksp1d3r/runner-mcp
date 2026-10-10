# Runner-MCP #381 — fixed rootless Claude subscription actuator (source-only)

Status: `PR_OPEN / SOURCE_ONLY` until CI and Fabric admission. Cross-repo owners: Runner-Fabric #1172/#240 (one control plane), Runner-MCP #381 (host-local actuator only), AIfordable #370 (rootless worker proof), Fabric #972 (loopback qualification). EnerCue #89 remains NO_DISPATCH until full end-to-end proof.

## Why same-user ServiceManager must NOT be reused

The existing `SystemdUserBackend` addresses the user manager of the Runner-MCP process. The Claude subscription coding worker runs under a different dedicated identity on a different intended host. Merely adding an `aifordable` service alias on the ChatGPT-connected github-runner would misroute service operations. Calling `sudo -u`, modifying the worker identity, accepting user/unit/path/argv arguments or enabling linger is NOT permitted.

## New source contract (no MCP endpoint)

`src/runner_mcp/fixed_coding_worker_actuator.py` provides:
- one exact symbolic capability `aifordable.subscription-coding-worker.lifecycle.v1`;
- only the Fabric draft typed intent fields; no extras, user/unit/path, command or environment arguments;
- strict version/action/lease/id/fence/revision/expiry field checks;
- a mandatory *injected trusted Fabric verifier*, absent by default (zero mutation);
- one fixed Linux service target and rootless identity baked into the backend; refusal when the running effective UID differs;
- user-manager socket ownership/mode checks, fixed `systemctl --user` argv and minimal environment; no arbitrary shell or cross-user `sudo`;
- a semantic loopback-only 127.0.0.1:8030 TCP-listener observation, never raw /proc/socket output;
- post-action semantic observation and explicit `mutationTriggered`; issuing systemctl is **not** equivalent to verified active worker.

The `RootlessCodingWorkerHost` actuator is a library component. It is NOT currently exposed through MCP, a network listener, CLI or system unit, nor installed on the dedicated account. This is intentional: a public endpoint before the Fabric lease/authority validator would widen privileges and break the accepted single-control-plane ADR.

## Authority and security caveats

- The injected verifier is an integration port, NOT itself a Fabric-signed/lease-fenced implementation. It must be bound to the trusted first-party Fabric authority on the intended host before production; no host-local boolean from a caller is acceptable. The document in Fabric draft PR #1422 describes the future exact envelope.
- Fabric must durably enforce lease owner/generation/fence, current inventory revision, idempotency key + payload digest, authorization/approval, emergency stop and drain, catalog generation, identity, expiry and cancellation. On any ambiguity, `BLOCKED`, and no helper invocation.
- The local port observation is evidence of a loopback listener, **not** proof of the listener PID or worker registration. Fabric #972 and AIfordable #370 must separately prove the exact service owner, approved revision/session and authenticated availability/return path. Neither a successful TCP connect nor a user-service active state qualifies the worker alone.
- User service default must remain disabled for automatic reboot activation; the helper never calls enable/linger and never grants commit/push/merge/deploy.
- No Anthropic API, Bedrock, Vertex, provider fallback, paid API token or cross-project source authority is created here.

## Completion checklist (child tasks)

| Child | Task | Current status | Owner |
|---|---|---|---|
| 381.1 | Strict fixed intent schema and wrong-target rejection | SOURCE PR | Runner-MCP |
| 381.2 | Dedicated-user rootless systemctl + listener observation, no sudo | SOURCE PR | Runner-MCP |
| 381.3 | Synthetic no-mutation & identity/listener negative tests | SOURCE PR | Runner-MCP |
| 381.4 | Exact-head validation incl Ruff/pytest, built artifact and clean demo | WAITING_CI | Runner-MCP |
| 381.5 | Bind trusted Fabric intent/lease/fencing verifier and one exact fixed transport to the right local host | BLOCKED_EXTERNAL | Fabric #1172/#1422 + site owner |
| 381.6 | Install/verify actuator as dedicated rootless identity without allowing arbitrary invocations | BLOCKED_OPERATOR | AIfordable #370 / operator |
| 381.7 | Controlled start/status/stop/listener-gone packaged service qualification; do not enable permanently | BLOCKED_OPERATOR | AIfordable #370 |
| 381.8 | Fabric #972 loopback availability + correlation/fence/return proof and bounded synthetic claim | BLOCKED_EXTERNAL | Fabric |
| 381.9 | Expose safe `list_services(aifordable)` projection **only if** it cannot hide the cross-identity boundary; else a separate fixed Fabric capability/status projection | BLOCKED_DESIGN | Fabric + Runner-MCP |
| 381.10 | EnerCue #89 first isolated proposal work, review/CI gate, no auto-merge | NO_DISPATCH | EnerCue |

A code PR can complete 381.1–381.4, not the issue acceptance across host identities. Do NOT mark #381 COMPLETE or start Claude work units before 381.5–381.9 pass with real authoritative evidence.

## Failure/decision ledger

- 2026-10-09: same-user SystemdUserBackend cannot reach another user's manager safely; refuse generic sudo or caller-selected UID.
- 2026-10-09: operator ADR settled ONE Fabric control plane, no second Runner-MCP scheduler.
- 2026-10-10: observed ChatGPT tunnel points to a different configured instance without AIfordable project; no inference that Claude worker is absent.
- 2026-10-10: rootless typed fixed source actuator prepared; all mutation denied without a Fabric verifier and correct dedicated host identity; no live activation.
