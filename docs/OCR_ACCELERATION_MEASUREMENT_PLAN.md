# OCR acceleration: measured-stage plan (no requalification)

Tracking: existing Runner-MCP Faster #514/#458/#467 and OCR measurement PR #537. Scope: **performance investigation only**; canonical OCR qualification is historical and should not be repeated merely to explore speed.

## First principle

End-to-end OCR time is the critical measure. A faster communication microbenchmark does not imply faster OCR or higher pages/hour. Preserve the same source document, language mix, OCR pipeline and output-quality checks across any comparison. Do not optimize by reducing required language detection, integrity evidence, security isolation or cleanup.

## Read-only baseline instrumentation by stage

| Stage | Measurement | Isolation / caveat |
|---|---|---|
| Source acquisition | source size, page count, canonical SHA-256, acquisition elapsed | Source content and customer document names must not enter public GitHub |
| Dispatch / scheduling | queued-to-admitted time, active worker count, host-pressure refusal | Separate queue starvation from OCR compute time |
| Disposable environment | allocation, image startup and readiness elapsed | Record exact pipeline/image fingerprint; cleanup still mandatory |
| Transfer / staging | bytes, transfer elapsed, SHA-256/size verification elapsed | Compare same data volume, with/without transport changes |
| Language sampling | pages inspected, mixed-language detections, language fallback/recheck elapsed | Dutch/French/German may coexist on one page; preserve language quality |
| OCR execution | per-page wall time, CPU time, peak memory, timeout/retry distribution | Normalize by source type/pages; compare unchanged OCR settings |
| Postprocess | output PDF normalization, quality/sample verification, output hash time | Never remove integrity or fidelity requirements for speed |
| Result / cleanup | upload/receipt/cleanup elapsed, target-destroyed and staged-input-removed receipts | Destruction and no residual customer data are hard gates |

For each run store a sanitized symbolic test-case ID, input/output hashes and sizes, pipeline revision, stage durations, host class/worker count, timestamp/freshness, retries, resource pressure, error category and redacted evidence reference. No host-specific private path, address, token, personal document content or raw OCR text in public results.

## Reuse existing transport evidence — do not overinterpret

Existing hosted shadow lab #458, CI validation run 37522524389 job 112471504336, includes synthetic 256-byte benchmarks:
- urllib loopback HTTP p50 0.7799 ms;
- persistent HTTP p50 40.9038 ms on that setup (**slower**, not faster);
- a separate Unix envelope E2E synthetic variant p50 52.288 microseconds versus its reference p50 132.698 microseconds (reported 2.538x at p50).

These are measurements of synthetic transport and must **not** be used as OCR page-processing speedups. The persistent transport latency anomaly deserves independent controlled explanation; do not promote a protocol change to production on these numbers.

## Safe decision gates

1. Retrieve existing bounded benchmark and historical OCR evidence first. Check if stage timings and hashes already exist; don't perform another OCR workload merely to rediscover them.
2. Locate the dominant end-to-end elapsed stage using identical input/pipeline and at least a small fixed repeated-case set. CPU/IO contention and queue time must be separated.
3. Propose one isolated shadow experiment at a time: no real customer jobs, no privileged host, no additional paid CI minutes without explicit budget authorization.
4. Require comparable hardware class, input, warm/cold status, software revision and workload concurrency. Report p50/p95 and uncertainty, not one flattering average.
5. Before any rollout, show total elapsed benefit **and** unchanged quality/integrity, source policy, confidential handling, watchdogs and cleanup receipts.
6. If runtime connector read-only status cannot be obtained (current #590), label live benchmark **BLOCKED** rather than inventing host load or worker availability.

## Work ownership / non-duplication

- #514: already-open Faster local MCP baseline implementation; do not create a duplicate benchmark.
- #458 and #467: existing hosted shadow experiments; reuse output, don't redeploy them.
- #537: already-open OCR timing/qualification hardening; do not re-run completed qualification.
- #584/#589: CI cost reduction through a separately qualified isolated runner, **not** an OCR speed project.
- #590: connector invocation reliability before making fresh live performance claims.

This document grants no production OCR activation, server command, runner enrollment or Fabric scheduler authority.
