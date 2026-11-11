# 11-tunnel-connectivity — Tunnel, relay en connectivity readiness — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-TUN-0001 | GREEN/MERGED #597 | tunnel readiness evidence type boundary | String `"false"` is truthy, so nonboolean source evidence could incorrectly advance the routability ladder | source audit #333/#597; not a confirmed current incident | require exact booleans for all five readiness inputs; 25 negative type regressions; exact head green, squash `6491d297...` | #333/#597 |
| RMCP-TUN-0002 | GREEN/MERGED #598 | local MCP health fallback | Historical succeeded/auth-required startup probe could override an explicit degraded/error/failed/stopped current health status | source audit #598, not proof of current connector outage | explicit negative status wins over historical startup probe; 8 negative regressions; exact head green, squash `d720a219...` | #333/#598 |
| RMCP-TUN-0003 | OPEN / DESIGN #599 | control-plane auth evidence freshness | Any nonempty last_success timestamp accepted as current auth evidence if status wrapper looks healthy | source review #599; no live proof | qualify actual writer/poll cadence, parse/bound timestamp with deterministic clock; reject malformed/stale/future before claiming current authentication | #333/#599 |

A closed failure remains recorded with fix/revision and regression evidence.
