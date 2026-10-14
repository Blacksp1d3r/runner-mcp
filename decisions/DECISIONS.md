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
- 2026-10-12 ACCEPTED operator decision: ship one universal Runner-MCP binary/package/version containing the complete tool set on every managed server. Never maintain per-host/per-project source forks or strip disabled tools from the wheel; use host/tenant/role-scoped policy to expose/enable only needed tools while keeping the installed inventory identical. A tool being installed/advertised does not grant mutation rights, leases or Fabric authority. See `docs/architecture/ADR-2026-10-12-UNIVERSAL-TOOLSET.md`.
- 2026-10-12 PROPOSED legacy compatibility: stable supported old tool contract IDs, schemas/defaults/semantics/errors and authorization across newer Runner-MCP packages; breaking behavior gets a separately named v2 tool. Fabric negotiates the actual supported protocol/tool contracts with authenticated hosts, never assumes new tools are present on an old binary. Unsafe obsolete versions can be blocked; customer/LTS support duration requires approval. See docs/architecture/ADR-2026-10-12-LEGACY-TOOL-CONTRACTS.md.
