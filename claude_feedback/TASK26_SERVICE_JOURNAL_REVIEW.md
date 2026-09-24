# Task 26 — bounded service journal/log access contract review

Date: 2026-09-24

## Scope

Review only. No service/runtime code, journal access, bridge action or process-control capability is added here.

Goal: determine whether Phase 4 journal/log access can be added without exposing private systemd units, paths, credentials, arbitrary unbounded output or a generic journalctl interface.

## Current service-management boundary

Runner MCP currently maps:

`project + public service alias -> private ServiceConfig.unit`

The private systemd unit is used only inside `ServiceManager` / `SystemdUserBackend`.

Public service operations currently expose:

- service alias;
- load/active/sub state;
- bounded health state;
- explicit allow-start/allow-stop/allow-restart capabilities.

They deliberately do not expose:

- systemd unit names;
- health-check URLs;
- executable paths;
- subprocess stderr/stdout.

The systemd backend uses a detected fixed `systemctl` binary, fixed argument arrays, `shell=False`, a fixed environment and bounded timeout.

Read-only service status remains available while the emergency stop is active; mutating actions do not.

## Current mailbox / bridge boundary

The bridge has explicit actions for:

- list services;
- service status;
- start;
- stop;
- restart.

There is no service-log/journal action.

The bridge does have `job_log`, but that capability is tied to persisted Runner MCP test jobs and is not a generic log primitive.

Therefore a future service-log feature must not reuse `job_log` by substituting service/unit/path identifiers.

## Existing text/log scrubbing

`TestRunner._scrub_text()` currently redacts:

- explicit secret values passed by the test runner;
- explicit private paths passed by the test runner;
- several generic secret patterns such as Bearer tokens, token/password/secret/api-key assignments and common GitHub token shapes.

This is useful prior art but is currently:

- a private TestRunner helper;
- dependent on caller-supplied known secret values/private paths;
- not a guarantee against arbitrary application data, personal data or an unknown secret printed without a recognizable key/pattern.

The bridge result sanitizer is **not** a substitute for log redaction:

- sensitive dictionary keys are redacted;
- whole strings that look like a URL or absolute/private location are redacted;
- arbitrary text strings are otherwise passed through (subject to length limits).

A line such as `customer secret is abc123...` can therefore remain visible if it does not match an existing scrub pattern.

## Primary risk

Service journals are application-controlled output.

Unlike Runner MCP's own bounded state records, a journal line may contain:

- application credentials;
- session IDs;
- access tokens;
- customer/user data;
- request bodies;
- database values;
- stack traces with local paths;
- host/process metadata;
- arbitrary strings that Runner MCP cannot classify reliably.

Therefore simply adding a fixed `journalctl --unit <configured unit>` command is not sufficient to claim a privacy-safe remote log capability.

## Classification

**Direct MCP/mailbox service journal access: REQUIRES PREREQUISITES.**

The current alias and subprocess boundaries are strong enough to prevent arbitrary unit/command selection, but the content-disclosure boundary is not explicit enough.

No service-log CODE task should be queued from this review until both conditions below are accepted:

1. **explicit per-service disclosure opt-in**, default false;
2. **a reusable bounded text-redaction contract** with clear limitations and tests.

## Safe future contract

If the prerequisites are introduced, the first log capability should still be deliberately narrow.

### Service configuration

Add an explicit private configuration flag such as:

`allow_log_read: false`

Rules:

- default is false;
- configured per public service alias;
- never inferred from `allow_start`, `allow_stop` or `allow_restart`;
- listing services may report a boolean `log_read` capability but never the unit name;
- enabling log-read is a local configuration choice, not a mailbox mutation.

Optional future redaction configuration should reference approved secret sources by identifier/name, not place raw secret values in public YAML or response data.

### Backend

A future journal backend should:

- detect only a fixed trusted `journalctl` path (for example `/usr/bin/journalctl` or `/bin/journalctl`) using the same no-symlink/executable checks as other system binaries;
- use `shell=False`;
- use the private configured systemd unit, never a caller-supplied unit;
- use a fixed environment;
- use a short bounded timeout;
- return only captured stdout after redaction;
- never return raw stderr or exception text.

### Allowed journal query

The first version should be **tail-only**, not arbitrary search/pagination.

Caller-controlled inputs should be limited to:

- project code;
- service alias;
- line limit, e.g. 1–100.

Do not accept:

- unit;
- path;
- `--since` / `--until`;
- cursor;
- boot ID;
- grep/regex;
- priority;
- output format;
- namespace;
- executable;
- environment;
- any raw journalctl argument.

Recommended fixed argv shape:

`journalctl --user --unit <private-unit> --no-pager --output=cat --lines=<bounded N>`

The exact production argv should be covered by an adversarial test; callers never see or control `<private-unit>`.

Using `--output=cat` avoids exposing journal metadata fields such as hostname/unit/process fields by default. Message content still requires redaction and explicit opt-in.

### Response shape

Recommended read-only result:

- `project`
- `service` (public alias)
- `line_count`
- `truncated`
- `content` or a bounded line list

Never return:

- private unit name;
- host name;
- executable path;
- journal cursor;
- raw stderr;
- command argv;
- service health URL;
- configured redaction literals;
- timestamps/metadata unless separately justified.

### Bounds

Suggested first-version caps:

- maximum 100 requested lines;
- maximum 32 KiB raw captured stdout before further processing;
- maximum 2 KiB per rendered line or equivalent total-envelope bounds;
- timeout <= 10 seconds;
- no historical pagination beyond the bounded tail.

The bridge's own result envelope remains an additional bound, not the primary privacy control.

## Redaction prerequisite

Before remote service-log exposure, extract or introduce a reusable bounded text scrubber with explicit inputs and no exception/path leakage.

It should at minimum support:

- known Runner MCP secret values available to the local runtime;
- known private paths;
- the existing generic secret patterns;
- deterministic output;
- an explicit maximum input/output byte budget;
- tests for secrets embedded inside otherwise ordinary log lines.

Important limitation:

Even a strong scrubber cannot prove arbitrary application logs contain no sensitive business or personal data. The per-service `allow_log_read` opt-in therefore remains mandatory and must be documented as a trust decision by the operator.

## Emergency stop semantics

A log-read capability would be read-only and could remain available while emergency stop is active, consistent with current service status and test-log reads.

This does not mean log disclosure is harmless; privacy authorization comes from the explicit service opt-in, not from the emergency-stop state.

## Mailbox sequencing

Do not add a bridge action at the same time as the first backend implementation.

Safer sequence:

1. shared text-redaction primitive and tests;
2. local/private service-log backend with explicit service opt-in;
3. adversarial privacy review of its returned result;
4. only then consider a separate bridge action with strict project/service/limit input.

This preserves the rule that mailbox authority is not broadened merely because a local implementation exists.

## Required adversarial tests for any later implementation

- arbitrary service alias cannot select another unit;
- unknown alias fails before subprocess execution;
- log-read disabled fails before subprocess execution;
- caller cannot provide unit/path/argv/env/query flags;
- fixed `journalctl` executable path is no-symlink and executable;
- `shell=False`, fixed environment and bounded timeout;
- raw stderr/exception text cannot escape;
- private unit name cannot appear in result;
- health URL cannot appear in result;
- known bearer/API/database/GitHub token literals embedded in ordinary text are redacted;
- private absolute paths embedded in text are redacted;
- generic token/password/secret patterns are redacted;
- oversized stdout is bounded/truncated;
- line count outside allowed range is rejected;
- output format contains no journal cursor/host/process/unit metadata;
- emergency stop does not accidentally convert log read into a mutation;
- bridge/mailbox execution is unreachable until separately authorized.

## Recommendation

Keep Phase 4 journal/log access **deferred at the remote/MCP boundary** for now.

The next safe prerequisite is a reusable bounded text-redaction primitive plus an explicit per-service log-read opt-in. Only after those are independently reviewed should a local service-journal reader be implemented, followed by a separate mailbox review.

This is preferable to adding a superficially bounded `journalctl` action whose output can still disclose arbitrary application data.
