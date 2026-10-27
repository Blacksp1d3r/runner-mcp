# RMCP-F-0075 — read-only cron status changed lock state (2026-10-27)

Owner: Runner-MCP #669; source candidate [PR #837](https://github.com/Blacksp1d3r/runner-mcp/pull/837), v0.1.89. **Not deployed by a source merge.**

## Failure mode

`cron_status` called `component_active`, which called the **writer** `_open_component_lock`. This creates absent `autostart-*.lock` with O_CREAT and chmods existing locks to 0600. Simply reading current status could alter evidence on the original host. The same status search also used a substring `" cron-run {component}"` over the whole managed block, so a comment, misleading suffix (`server-old`), or noncanonical command could be misreported as installed.

## Correction

Retain the existing cron role registry and writer path for `run_cron_component`. For observation only, open existing lock fd with O_RDONLY | O_NONBLOCK | O_NOFOLLOW, check fstat owner/current effective UID, single hardlink, regular file and private permissions, and use nonblocking flock. An absent lock returns **not currently held**, not a scheduled-job failure or a source/wheel witness. An unsafe/unauthorized lock refuses without chmod/replace. Detect installed roles only from exact canonical timed commands in the one existing managed block; reject comments, aliases, malformed redirects and invalid ports.

## Boundary

This is a safe local lock observation, **not** independent physical source/installed wheel attribution or signed six-role witness. Short-lived scheduled jobs need separate actual recent execution/result receipts. No original host service, cron entry, release, credential, extra monitor/updater or backup was changed. GitHub v0.1.89 must not be confused with the original physical :8000 v0.1.88 until independently installed and verified.

## Prevention

A status/diagnostic function must be side-effect free and verify complete exact managed identity, never a text substring. Tests must assert no new lock, original inode/mode/bytes/mtime unchanged, and bounded denial of unsafe linked/nonregular locks.
