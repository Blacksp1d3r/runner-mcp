## 2026-10-17 — Local first-host staging does not bootstrap host authentication

On new Black, a successful operator-attended immutable, non-serving stage does NOT create `~/.config/runner-mcp`, generate a bearer, select actual project checkout, enroll Agent Bus, start a listener, or prove original-client ACK. The independent physical receipt is stage-only; these steps demand explicitly selected real project/UID and owner-held private issuer authority. If uninitialized, read-only status may safely say NOT_INITIALIZED; malformed/partial/wrong-owner private config must still fail closed. Source issue #735; downstream Fabric #1563 owns target-bound ACK. Existing central 0.1.27 can never attest to Black by itself. No duplicate tunnel or generic shell.

---

# Runner MCP — Decisions

Canonical record of durable project-wide decisions. Keep entries concise and append new decisions; do not put secrets or private infrastructure values here.

## Current durable decisions
- AI/client text is intent, never execution authority; security gates are deterministic and proportional to blast radius, keeping contained read/edit/test work automatic while protected mutations require independent authority.
- Runner Fabric is a separate product/repository; Runner-MCP remains the small security-first execution core and does not absorb Runner Fabric orchestration scope.
- Runner MCP is deny-by-default and project-agnostic.
- Arbitrary remote shell/process/package-manager control is not a supported feature.
- Real deployment values stay in private configuration.
- GitHub mailbox operations are strict, versioned and allow-listed.
- High-risk mutations retain explicit approval boundaries.
- Self-update is canonical-repository, exact-commit and fail-closed.
- Package-install recovery is local operator-only and requires the emergency stop.
- GitHub live state is authoritative when documentation lags.
- Feature/code changes use branch -> PR -> review/tests; coordination docs may be updated directly on the agreed documentation surface.


## 2026-10-16 — Operator prioritizes actual controlled fleet upgrade; freeze new version-development work

Until the existing live Runner-MCP is actually upgraded with independently witnessed recovery, pause further source version increments, code PRs for updater enhancements, and alternative updater implementations. Read-only verification, exact evidence checks and canonical handover may continue. Topology is already known.

Confirmed v0.1.9 -> v0.1.27 adds a required cryptography runtime dependency. Canonical no-deps self-update cannot satisfy a changed dependency contract: do not bypass policy or edit historical state. Use the normal attended dependency-resolving isolated-prefix installation path, preserve prior generation and demand actual original-client ACK plus independent rollback proof before switching the live control plane. Source CI/unapproved archive is not release authority. Operator is away: live install WAIT.

This is an execution priority, not a permanent product version policy.
