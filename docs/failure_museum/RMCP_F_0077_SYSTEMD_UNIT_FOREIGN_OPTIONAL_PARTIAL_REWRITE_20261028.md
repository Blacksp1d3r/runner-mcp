# RMCP-F-0077 — Systemd unit installation could rewrite a managed unit before rejecting a foreign optional unit

- Date: 2026-10-28
- Owner/workstream: Runner-MCP #866; existing `autostart.py` rootless systemd-user backend
- Actual source recovery: [PR #884](https://github.com/Blacksp1d3r/runner-mcp/pull/884), version 0.1.111, merged `d7330b58fd251b3720a7a89d10a8bc278e372703`
- Evidence scope: source inspection, isolated regression fixtures and exact-head CI. **No failure observed on a production host.**

## Root cause and potential impact

Before PR #884, `install_user_services()` validated and **atomically replaced desired managed unit files** in iteration order, then traversed `KNOWN_UNITS` to remove obsolete optional units. If an existing *obsolete optional unit* (for example `runner-mcp-tunnel.service`) had foreign content or was an unsafe symlink, the later check rejected the operation **after** `runner-mcp.service` could already have been rewritten. No daemon-reload/enable was reached, but the existing on-disk unit could have changed despite the rejected install. This is a partial-write risk, not proof that any real cron role was interrupted.

## Correction

The existing installer now **preflights every known unit path read-only before the first desired-unit content replacement**. Existing foreign files, wrong file kinds and dangling symlinks are refused before updates; permitted files still use the original atomic private writer. Existing activation-permit and peer-cron checks remain unchanged. There is **no second service manager**, new timer, updater, relay, user identity or host mutation.

Two regression cases create a previously managed server unit and a foreign or dangling optional tunnel unit. With the activation permit otherwise clear, the new installer must reject the request, preserve original server bytes and foreign path, and perform only the pre-existing read-only `systemctl --user show-environment` manager probe. Exact-head tests, Ruff, release admission, build, demo, clean Ubuntu installation and commit attribution for PR #884 passed:
`40648646566`, `40648646517`, `40648646484`.

## Separate systemd syntax qualification

[PR #882](https://github.com/Blacksp1d3r/runner-mcp/pull/882) merged `c0cd0c2f24826235d3984cba2563378f56e889fa` (test-only). On disposable Ubuntu CI, the **real** `systemd-analyze verify` parser accepted rendered server and dependent tunnel units, and rejected malformed `ExecStart`. The initial test-only CI failure was an incorrect expected alphabetic filename order in an assertion, not a systemd parser failure. Replacing the order assertion with set equality yielded complete validation `40647970469` and attribution `40647970446` SUCCESS.

## Remaining qualification and no-repeat rule

**SOURCE_READY is not LIVE_READY.** Neither fix proves `systemd --user` boot/session-bus continuity, a live supervised worker's crash recovery, a real reboot or a fully rehearsed cron rollback. Even after the preflight improvement, a failure **during** atomic updates or systemctl activation can require a separately verified recovery transaction. That belongs to #866 M2/M3 and Fabric #924/#943. The original `github-runner` and Blacky cronjobs, existing LAB systemd-user services, Windows Task Scheduler and production wheels/processes were **not modified** by these source PRs.

Future work must re-use the same `autostart.py`, `cron_autostart.py`, immutable AIfordable topology and existing handover. Run fail-closed owner/host/revision checks and an isolated true boot/rollback test before the first physical cron→systemd transition. Do not re-create a supervisor or presume a GitHub release is running on a server.
