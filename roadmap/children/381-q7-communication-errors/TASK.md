# #381 — Q7 bounded communication failure results

Owner: Runner-MCP #381 communication lane. Related live #590/#540 (connector/catalogue) and Fabric #972 (Q7 wire + worker). Fabric #1398/#1400 lease/fence source is owned by Fabric; do not duplicate it.

## Goal
When the existing authenticated MCP `fabric_coding_availability_qualify` handler encounters a known application-level qualification failure, return a **strict bounded failure result**, not an opaque generic exception. Distinguish verifiable **not-started** errors (fixed invalid case/revision, operator stop, launcher/private configuration missing) from **unknown effect** errors (launch/process/transport/nonzero code/untrusted result). This reduces communication triage ambiguity without letting a client blindly retry an unknown work item.

## Changes
- Add a pure allow-list failure categorizer with constant public schema `runner-mcp/coding-availability-qualification-unavailable/v1`.
- Keep fixed `result_verified=false`, `dispatch_authorized=false`, `retry_authorized=false`, never return raw exception text, sensitive identifiers, provider output or work unit.
- Return `qualification_effect=not_started` only when failure occurs before launching the known Q7 attempt; otherwise `qualification_effect=unknown` and require independent correlation/side-effect reconciliation.
- Preserve the existing success schema and no generic shell, arbitrary path/host/user or provider selection.
- Synthetic negative unit tests and authenticated MCP HTTP tool-call response plus redacted audit tests.

## Non-goals and safety
Source-only changes do NOT prove installed current Runner-MCP version/response route (#590), Fabric real peer availability (#972), dedicated rootless service (#370), durable Fabric lease/fence (#1400/#1398), safe A6/A7 rollout or active Claude subscription session. Do not introduce retry logic or restart any live service. If the client does not have source-merged tool contracts, qualify release generation through existing approved fleet path; no tunnel workaround.

## Acceptance
Exact HEAD Ruff/pytest, artifact, clean demo, commit attribution all terminal SUCCESS. New positive Q7 success payload unaffected. Every failure only static schema/reasons, pre/post effect correct, NO_DISPATCH. Failure Museum and handovers updated. Parent #381 remains OPEN operationally.
