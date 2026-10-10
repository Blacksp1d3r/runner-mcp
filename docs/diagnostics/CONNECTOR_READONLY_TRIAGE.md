## 2026-10-10 — Bounded build identity unavailable source contract now merged\n\nPR #629 has full exact-head green CI and source merge `7deb63cd8d623a74389c9f582d6e2d1ec688b2eb`. The application source now responds with `runner-mcp/build-identity-unavailable/v1`, `state=unavailable`, `identityEvidenceComplete=false` if the first-party identity provider cannot be verified. Successful build identity shape is unchanged. This is NOT evidence of active runtime upgrade or matching external client/tool-catalogue response route; #590 remains OPEN. Check the installed identity and client/transport lineage using approved private read-only evidence first. No tunnel/server restart, raw logging, secret exposure, provider artifact deletion, or physical storage assumption.\n\n## 2026-10-10 — Source-only bounded status failures landed; runtime generation remains unproved

PR [#627](https://github.com/Blacksp1d3r/runner-mcp/pull/627) exact head `e70e11702504c3fe161900ced4afceff8c7df084`, attribution `38042225385` SUCCESS, full validation `38042225393` SUCCESS and squash `e06fe5b7f44c92ae22d4fa291a142b6b67803db3` on main. New application *source* contract: a failed/malformed self-update, Fabric bootstrap or Fabric update status provider returns a safe fixed `runner-mcp/runtime-status-degraded/v1` envelope with `state=degraded`, `runtimeEvidenceComplete=false` and one fixed `reasonCode`. Normal successful status shape unchanged. Private exception text, private partial evidence and raw path text do not cross the MCP response boundary. A degraded envelope MUST NOT be treated as healthy runtime or authority to mutate.

Observed connected `runtime_doctor` on the same date returned only the older set of 12 checks (0 failed, 3 warning); current main code always adds `self_update_source_baseline`, `self_update_runtime_activation`, and `fabric_a6_binding_state` fields/check names, none observed. `runtime_status` and `build_identity` returned generic internal errors. This is **not** evidence that the merged fix is installed or that the tunnel's response path is correct. Before claiming acceptance, independently verify authenticated, bounded installed build/source generation, catalog schema and request↔response lineage through authorized private diagnostics. Do not infer instance identity from an advertised tool name, a successful doctor call or a past successful tunnel-forward event. Never restart or replace the working service to fix a hypothesized version mismatch without separate owner/change authority.

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

## External tunnel read-only response-delivery evidence (2026-10-09)

The official tunnel-client health contract documents separate loopback-only component projections for `dispatcher`, `response-delivery`, `queue` and `control-plane`. They provide a safer first-hop diagnosis than counting journal message labels. Relevant semantics:

- `dispatcher`: active operations, completion/failure/timeout counters and bounded oldest active age. Forwarded requests do **not** imply completed operations.
- `response-delivery`: attempts, retries, active deliveries, HTTP 200 acceptance and logical completion; compatible benign HTTP 404 is **not** acceptance.
- `queue`: local commands waiting/enqueued/dequeued and backpressure; not remote queue depth.
- `control-plane`: polls/last successful observations, but a historical success is not current authentication without freshness policy (source fix #599 already complete).

Reference: upstream `openai/tunnel-client/docs/health.md`. The upstream documentation explicitly notes observations are historical snapshots, not continuous connectivity guarantees. To locate #590, use an authorized operator's local, private **read-only** snapshots of only sanitized counter/status fields immediately before and after a single bounded client invocation; correlate to server receipt/completion and user-visible outcome. Do not upload health payloads containing private connection identities or addresses, do not enable raw HTTP logging, and do not expose listener addresses, credentials or tunnel IDs in public issues. If the available projection does not expose a qualified per-request association, classify exact return-route identity as UNKNOWN even when counters move. No operator-only live state is inferred by this document.
