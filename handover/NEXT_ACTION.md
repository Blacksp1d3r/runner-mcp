# NEXT ACTION

Updated: 2026-10-03

## Goal

Finish the replacement-host Runner MCP self-update safely, then resume Agent Bus / Runner Fabric live qualification without repeating already-proven checks.

## Current invariant state

- Installed/source baseline: `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`.
- Exact target/main: `fa2bedc3d9e9f8181fe2c27043a6d75c3dfe81fe`.
- Source tree is clean and still at baseline after failed self-update.
- MCP server, auth/session bridge, bounded local lint/unit and mailbox lint are proven healthy.
- `self_update_ready=true` before the failed update.
- Failed self-update job: `48a3cb362da249f0925b5cee18fdfe86`; category `self_update_failed`; no target checkout occurred.
- Generic baseline wheel build succeeds manually.
- Persistent server/autostart is not installed yet.

## Next engineering action

Reproduce only the internal pre-sync baseline-staging path using Runner MCP's own `SelfUpdatePackageInstaller` with the canonical private config directory and runtime Python, with a disposable unique job id and cleanup afterward. Capture only the bounded exception/category. Do not install a wheel, change the Git checkout, or submit another self-update until this exact path is understood.

If internal staging succeeds, inspect the remaining pre-sync guards in order: self-update project source guard, installed-baseline comparison, private artifact-root safety/permissions, and state persistence. Add a bounded diagnostic category/step preservation fix if needed so future failures do not collapse to `self_update_failed`.

## After the self-update is green

1. Verify installed commit/version, `runner-mcp doctor`, restart state and `runner-mcp agent-bus convergence`.
2. Run the bounded Runner Fabric isolated Agent Bus work-unit qualification with GitHub credentials absent and GitHub network denied as defined by Fabric #590.
3. Prove worker-process restart/replay and convergence.
4. Only then qualify/register the separate GitHub fallback and persistent activation.
