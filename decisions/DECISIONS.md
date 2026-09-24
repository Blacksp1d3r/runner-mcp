# Runner MCP — Decisions

Canonical record of durable project-wide decisions. Keep entries concise and append new decisions; do not put secrets or private infrastructure values here.

## Current durable decisions
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
