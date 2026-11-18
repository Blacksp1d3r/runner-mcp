# #713 — Source-pinned rootless local first-host staging

## Parent and ownership

Operator request: prepare new Black for later *first-party Runner-MCP → Fabric* management. Related Runner-Fabric #1554/#924, AIfordable #428/#584/#585, actual per-hop ACK #1556. This child owns ONLY the local first stage. Host enrollment/secret provision and activation are separate.

## Inputs

- Operator-private 0600 manifest with exact stable host asset, dedicated runner subject, independently confirmed local machine-id hash, source revision and install.sh SHA256.
- Clean canonical runner-mcp Git source at the exact expected revision and canonical origin, Python 3.12+, unprivileged service user.

## Execution

- identity: local fingerprint only, no service action.
- plan: deterministic read-only plan hash after identity/source/custody checks.
- stage: explicit exact hash accept, existing install.sh in fresh private isolated non-serving prefix with sanitized environment, post-install pip check and CLI help.
- Persist immutable marker with no service activation, no relay enrollment, no original-client ACK.

## Fail closed

Wrong host or revision, caller root, untrusted origin, changed installer, dirty/ignored workspace, unsafe path/manifest, mismatched approval, already-present/partial stage, interrupted installer or source/manifest swap deny success; never clean up or retry a partial stage automatically.

## Outside this child

No public or privileged network listener, no direct SSH/Desktop Commander/GitHub runner remote shell, no new agent/protocol, no systemd or crontab writes, no credentials, no HDD formatting, no website deployment, no actual Claude invocation. Subsequent physical first-party receiver/enrollment must prove external identity + actual command/result/ACK and recovery independently.

## Acceptance

Test guard negatives and local simulated stage; exact-head validation + Ubuntu installer proof + attribution green before source merge. Follow docs/LOCAL_HOST_BOOTSTRAP.md for later physically attended operator work.
