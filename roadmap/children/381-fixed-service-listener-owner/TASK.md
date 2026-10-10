# Runner-MCP #381 — exact fixed service listener-owner evidence (source child)

## Motivation and owner
Runner-MCP chat owns source-level host-local actuator. AIfordable #370 owns actual packaged rootless service lifecycle. Fabric #1172/#1400/#1398 owns signed issuer, durable leased/fenced authority and topology; #972 owns real Q7 return path. Runner-Fabric PR #1448 proves only an isolated synthetic peer, not the installed Claude subscription worker.

The existing fixed actuator #628/#637 checks an exact localhost listener, but that socket can belong to a different process. This child does **not** issue authority or install/activate any service. It narrows the meaning of local `LOOPBACK_ONLY` evidence: it now requires all matching TCP socket inodes to be open under the fixed `systemd --user` unit's `MainPID` for the exact dedicated OS account. Unknown/foreign/unreadable PID or multiple owners -> `UNVERIFIED` -> no successful status/action proof.

## Source boundary
- Read **only** the fixed user unit `MainPID` with fixed systemctl argv under the exact dedicated worker UID; no arbitrary pid/unit/host parameter.
- Inspect only kernel `/proc/net/tcp{,6}` listener sockets and file-descriptor socket symlinks under that MainPID. Never inspect command line, env, account session, bearer, prompt or task payload.
- Observe all matching port inodes, reject IPv6/public binds, deny if any inode is not held by the fixed MainPID, and re-read MainPID to reject obvious restart races.
- Read failures, missing service PID, foreign socket, extra conflicting listener and drift return bounded `listener-owner-unverified`. This is **local supporting evidence only**, not signed Fabric permission, durable lease or proof of end-to-end Claude assignment.
- Dedicated account running the service may intentionally delegate to a child process. That currently fails closed; extending to child cgroup attribution requires separate strict first-party review/qualification.

## Acceptance
1. Missing/zero/invalid MainPID never gives a successful listener attestation.
2. A foreign process on exactly the expected numeric loopback port does not produce `LOOPBACK_ONLY`.
3. Every listener inode must map to the fixed MainPID, including reuse-port collisions.
4. PID change between reads denies.
5. Foreign/unsafe address or IPv6 denies; no listener remains `ABSENT` for STOP proof.
6. START/STOP/RESTART and STATUS block unknown ownership without executing systemctl actions.
7. No unbounded process scan or credentials/raw private paths in results; synthetic negative unit cases, then full exact-head Ruff/pytest/artifact/demo/attribution required.
8. Parent #381 remains OPEN pending genuine installed right-host owner/service evidence, external Fabric durable issuer/lease/fence and actual Q7 correlation.

## Risks and decisions
Socket-owner-to-unit relation is a bounded time-of-check snapshot, not a race-free executor authorization. Fabric must revalidate at mutation boundary and reconcile unknown side effects. No source CI can establish the live right-host identity or lift NO_DISPATCH.
