# Task 51 — remote service-journal disclosure boundary review

Date: 2026-09-30

## Scope

Review only. No MCP, bridge, mailbox or Agent-Bus journal action is added.

This review reconciles the integrated Task 47 local service-journal reader against the current bridge/Agent-Bus disclosure boundary.

## Integrated local boundary

Task 47 / PR #145 provides a local CLI-only reader with:

- per-service `allow_log_read: false` by default;
- public caller inputs limited to project, public service alias and 1–100 lines;
- fixed trusted `journalctl` discovery;
- fixed argv equivalent to `journalctl --user --unit <private-unit> --no-pager --output=cat --lines=N`;
- fixed environment, `shell=False`, timeout <= 10 seconds;
- at most 32 KiB retained raw stdout;
- Task-41 bounded redaction using known runtime secrets/private paths plus the private unit and health URL;
- bounded result shape: project, service alias, line_count, truncated, content;
- no unit, cursor, host metadata, health URL, argv, stderr or raw exception detail.

The local reader remains available during emergency stop because it is read-only.

## What Task 47 does not prove

The redactor removes known literals and common secret patterns. It cannot classify arbitrary application-controlled business or personal data.

Examples that may remain after correct redaction:

- customer names, email addresses or identifiers;
- request/response bodies;
- database values that are not configured as known secrets;
- session or application tokens with novel formats;
- proprietary payloads;
- free-form stack/context text that is sensitive for reasons unrelated to its syntax.

The bridge result sanitizer is an additional structural/size bound only. It is not a privacy classifier for arbitrary log text.

Therefore local operator opt-in does not automatically authorize network disclosure.

## Decision

**Do not add remote service-journal access at this time.**

A remote action is not justified merely because the local reader is bounded and redacted.

If remote disclosure is reconsidered later, it must use a second independent private per-service authorization such as `allow_remote_log_read: false`; local `allow_log_read` alone is insufficient.

Any future remote contract would also need all of the following before code is queued:

- explicit project + public service alias + bounded 1–100 line request only;
- no unit/path/cursor/query/time-range/grep/argv/env input;
- a second remote-disclosure opt-in configured locally, never remotely;
- the existing local redaction before transport;
- existing bridge 32 KiB envelope as a secondary bound;
- per-request audit using only project/service alias and safe outcome;
- rate limiting independent of ordinary service status calls;
- emergency stop may keep the read available, but does not grant privacy authorization;
- clear operator documentation that redaction cannot guarantee removal of arbitrary personal/customer/business data.

## Outcome

Task 51 is complete as a review.

No CODE task is queued because the privacy boundary is not yet strong enough to justify remote journal disclosure. The local Task 47 feature remains the intentional boundary.
