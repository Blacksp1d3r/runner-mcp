# Child TASK — #333 fixed tunnel client under minimal cron PATH

- **Parent:** Runner-MCP #333
- **Child ID:** RMCP-333-CRON-PATH
- **Owner:** this bounded Runner-MCP tunnel/source lane
- **Profile:** EXPANDED / existing `roadmap/children` mapping
- **Source PR:** #670; base #668, whose base is #661
- **Release:** proposed 0.1.6, not an approved/published/live version

## Goal

Ensure cron-managed tunnel startup resolves an existing trusted service-user local installation even when the cron environment offers only a minimal PATH; preserve system PATH fallback when no service-user installation exists. Prevent the same issue recurring after future managed-autostart reconciliation.

## Evidence / data lineage

An attended local operator observed: complete restart configuration; tunnel cron installed and enabled yet runtime absent. Interactive service-user environment could resolve the binary in a local user executable directory, but a restricted PATH could not. A narrowly scoped tunnel cron PATH repair changed live readiness to `local_ready/control_plane_not_authenticated`. This proves process/local MCP health, **not** authenticated polling or end-to-end routability. Record public-safe categorical facts only; no token, exact private host path, tunnel identifier, or environment values in Git.

## In scope

- `src/runner_mcp/tunnel_runtime.py`: deterministic fixed user-local binary lookup, fallback to standard PATH only when local target is absent, bounded failure if unreadable, unusable or broken symlink
- `tests/test_tunnel_cron_path_v016.py`: isolated minimal PATH, PATH fallback, non-executable local binary, broken symlink
- Release metadata: `pyproject.toml`, `server.json`, `glama.json`, `src/runner_mcp/__init__.py`, monotonically increasing version

## Explicit exclusions

No reconnect/rotating tunnel credentials; no changes to auth, certificate trust, launcher privileges, network transport or connector permissions. No generic host shell or test-production authority; no installation on the physical operator host, cron reconciliation, reboot, rollback activation, or Claude dispatch through this source PR.

## Algorithm and idempotence

1. Establish exact PR #668 base commit and verify no concurrent ownership.
2. Resolve user-owned local executable first; require regular resolved file and executable permission.
3. If no local path exists, retain ordinary PATH lookup.
4. Fail closed on existing unusable local installation; do not silently swap to a different executable.
5. Run focused tests and full CI, with attributable reviewed HEAD.
6. Await independent review + protected merge of #661 then #668; rebase/retarget and rerun tests as necessary.
7. Require offline escrow, verified artifact/source/protocol, original-client ACK and independent A6/A7 before activation.

## Acceptance

- All four negative/positive minimal-path tests pass.
- Ruff/full pytest, installer clean proof, exact version check and commit-attribution CI succeed at the **final** PR HEAD.
- Independent review submitted; branch chain reconciled.
- Live installation remains outside scope; separate operator ACK tracks `tunnel-status` through authenticated and routable states after safe promotion.
- Incomplete control-plane poll or missing original-client tool catalogue => remains WAIT/BLOCKED, not COMPLETE.

## Failure Museum

Cross-reference central #333 and #590: cron PATH resolver hid errors because managed cron redirected stderr to null. No new separate failure-ID until the central Failure Museum owner allocates a stable canonical ID.

## Recovery / handover

Operator previously escrowed the crontab and can restore via attended procedure if necessary. Do not overwrite cron state or use standalone tunnel duplicate. Refer to PR #670 and `STATE.md` for current head and CI.
