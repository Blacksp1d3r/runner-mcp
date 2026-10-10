# #381 — exact Q7 assignment request count (source security child)

## Problem
The fixed Q7 response verifier expected one assignment request but used Python `== 1` with no type check; JSON `true` and `1.0` also compare equal to integer 1. This could falsely attest an expected exactly-one assignment count in a remote Fabric qualification payload.

## Implementation
Require `type(assignment_requests) is int` AND `assignment_requests == 1`. Keep all other strict output checks, fixed selected cases, no unknown fields, no arbitrary backend/user/host/path, no provider/worker action beyond the already existing bounded Q7 mechanism. Negative synthetic cases `true`, `false`, float `1.0`, string `"1"`, integer 2; positive exact integer 1 unchanged.

## Scope, dependencies, acceptance
Runner-MCP #381 owns source consumer correctness. Fabric #972 owns real AIfordable MCP round-trip, #1400/#1398 owns durable issuer/lease, #590 owns actual installed tool/response correlation. AIfordable #370 owns rootless worker. Exact-head Ruff, pytest, artifact, clean demo, attribution GREEN before source-only merge. No live service operation or paid API; parent #381 stays OPEN. Retain blocked NO_DISPATCH.
