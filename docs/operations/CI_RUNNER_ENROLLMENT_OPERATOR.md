# Local CI runner enrollment — operator checklist

Status: **CODE-ONLY / NOT LIVE-AUTHORIZED**. This CLI operation must not be performed merely because the source PR has green tests. Follow the canonical runner admission and isolation requirements in `docs/operations/ISOLATED_CI_RUNNER_ADMISSION.md` on current `main`.

## Credential separation

- Normal source/mailbox transport: `RUNNER_MCP_GITHUB_TOKEN`. Do **not** give this token repository administration/runner-registration permissions.
- Explicit one-off operator enrollment: `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN`. This must be a **different** credential with narrowly scoped repository runner registration authority, short lifetime and a private local delivery method.
- There is no fallback to the normal mailbox credential. With only `RUNNER_MCP_GITHUB_TOKEN` configured, `ci-runner enroll <configured-alias>` must refuse before requesting a registration token. If both variables contain the **same** credential value, the command also refuses; a second environment-key name does not create a separate security principal.
- Never store real token contents in Git, Actions logs, issues, CI caches or public handover docs. Configure the one-off credential only in the approved private runtime environment. Retire it after successful enrollment.

## Operator admission before invoking enrollment

1. Independently verify a dedicated disposable/isolated CI VM, no production secrets/routes, no persistent cross-tenant caches, and adequate capacity. Ordinary staging/deployment runner identity is NOT sufficient.
2. Confirm fixed private runner alias, repository, root/work paths and labels. The local configuration parser accepts only preconfigured aliases. Do not put real private paths in this document.
3. Verify root and `config.sh` are not group/world writable; verify the work root and all intermediate directories are protected. Confirm ownership and no untrusted local users with permission to replace executable paths.
4. Be aware GitHub's `config.sh --token` runner registration protocol receives a short-lived token via process argv. Local process inspection is an exposure risk; do not perform this on a multi-user or shared-privilege host. Stdout sanitization alone is not a remedy.
5. Use a controlled operator session with a freshly provisioned narrowly scoped credential. Approve any actual enrollment or local service activation separately from a source-code merge.
6. Verify remote GitHub identity, exact custom labels and the local marker; reject incomplete runner inventories, symlink markers, unexpected labels and ambiguous identities. Fail closed on any error.
7. Prove isolated job execution and teardown with negative tests before changing `runs-on`. Keep existing required CI checks and the hosted fallback operational until qualification is complete.

## Boundaries

- This command does not authorize production deployments, arbitrary shell execution, CI workflow selector changes or broad GitHub administration for normal Runner-MCP operation.
- A successful local registration is **not** proof that PR execution is sandboxed. Disposable VM lifecycle, egress policy, protected caches and test cleanup are separately qualified.
- Runner-MCP is public; standard GitHub-hosted CI minutes are currently free. Therefore the motivation for self-hosting must be operationally justified rather than a presumed public-repo minute saving.
- In case of uncertainty, leave the candidate runner unadmitted, preserve existing hosted validation and record the blocker in runner-mcp #584.

No live runner installation or credentials were used to author this document.
