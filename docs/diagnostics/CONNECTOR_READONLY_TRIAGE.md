# Read-only connector failure triage (Runner-MCP)

Owner: #590, component 14 (MCP server interface) and component 11 (tunnel connectivity). This playbook is for a tool that is *advertised by the client*, but invocations fail before any sanitized Runner-MCP response.

## Evidence and interpretation

A client reporting only `The tool failed internally.` has not proven that its request reached Runner-MCP. On 2026-10-09, four unrelated bounded reads (`runtime_status`, `runtime_doctor`, `list_projects`, `worker_status`) returned that same generic failure without a structured application result. That is a transport/catalogue/session or runtime-boundary **unknown**, not a diagnosis of host health or workload capacity.

## Safest next probes

1. Reconcile the client's installed/connected plugin state and advertised tool schema generation using supported UI/private connector metadata. Do not print tokens, tunnel addresses or internal service locations.
2. Prefer an authorized, already-defined read-only connectivity/health indicator, if present. Record only success/failure class, UTC time, bounded correlation ID, and sanitized version/schema fingerprint.
3. Distinguish failure at client selection, schema/admission, tunnel/transport, MCP initialization, tool dispatch, and app execution. One known-good bounded action is sufficient at each layer; don't continually retry all actions.
4. If evidence shows the request reached the server, inspect only approved private server-side health and bounded audit diagnostics. Attribute errors to the earliest failing edge. Generic client error alone is not evidence of a server crash.
5. After the owner fixes a verified cause, open a **fresh** client/session if needed to refresh the tool catalogue and run `list_projects` once, then `runtime_status` and `runtime_doctor` once. Require structured, consistent versions before reporting healthy.
6. Keep production update/deploy/worker starts, shell fallback, tunnel restarts, CI selector changes and credential rotation out of this read-only triage. Each would need separate authority, owner coordination and rollback proof.

## Negative/fail-safe interpretations

| Observation | Permitted conclusion |
|---|---|
| Generic tool error before structured result | Transport/application boundary unlocated; runtime state UNKNOWN |
| Tool exists in catalogue but fails | Registration visible; invocation path not proven |
| `list_projects` succeeds while `runtime_status` fails | Localize to status dependencies or response serialization; do not infer complete health |
| Fresh doctor succeeds | Only the checks in that doctor result are proven; isolated CI runner admission still needs its own #584/#589 evidence |
| Healthy host but missing client schema | Client tool-catalogue issue may remain; refresh catalogue before altering server tools |

## Tracking

- RMCP-MCP-0005 / #590 is the canonical unlocated connector failure record.
- #584/#589 concern **isolated disposable runner** qualification and paid CI migration; connector failure provides no positive runner-admission evidence.
- Historical OCR qualification is complete; Faster performance work is separately tracked by #514/#458 and must not be re-triggered as a connector test.

Public documents must not contain private endpoints, hostnames, port maps, absolute deployment paths, credentials, token fragments or customer payloads.
