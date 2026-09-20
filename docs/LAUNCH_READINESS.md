# Public launch readiness

Runner MCP should be promoted only as fast as a new user can safely understand, install and verify it.

The goal is a useful open-source launch without paid advertising or paid infrastructure.

## Launch gate

Before a wider public launch:

- installation works from a clean supported Linux environment;
- QUICKSTART can be completed without reading Python source;
- `runner-mcp doctor` gives actionable pass/fail guidance;
- the security baseline and threat model match implemented behavior;
- the public repository contains no real infrastructure details;
- a minimal demonstration can be reproduced with placeholder/sample configuration;
- releases have clear version notes and upgrade guidance;
- known limitations are explicit;
- the GitHub mailbox bridge is documented as an optional transport, not a shell bypass;
- public examples contain no credentials, private endpoints or deployment-specific paths.

## Free discovery plan

The first discovery layer is the repository itself:

1. a short problem/solution statement at the top of README;
2. a five-minute path to first successful `doctor` run;
3. a small architecture diagram using repository-safe placeholders;
4. clear security guarantees and non-goals;
5. a reproducible demo;
6. tagged releases with concise release notes.

After that, prepare launch material for appropriate developer and self-hosted communities. External posting remains a separate human-controlled action.

## Launch package

Prepare reusable copy for:

- GitHub repository description and topics;
- MCP ecosystem/registry submission when packaging requirements are met;
- a technical Show HN-style introduction;
- developer-tool launch directories;
- relevant self-hosted, MCP and Python communities;
- LinkedIn or similar professional announcement.

The copy should lead with the problem and the working technical design, not marketing superlatives.

Suggested core sentence:

> Runner MCP gives AI clients a narrow, auditable path to self-hosted development and staging operations without exposing a general-purpose remote shell.

## Metrics without tracking users

Prefer platform-level public signals instead of embedding analytics in Runner MCP:

- GitHub stars and forks;
- issues and discussions from new users;
- release downloads where the hosting platform exposes aggregate counts;
- external references and community feedback.

Do not add application telemetry solely for marketing.

## Cost rule

The default launch path must remain usable without buying advertising, paid hosted CI minutes or a new hosted service. Standard GitHub-hosted CI may be used for this public repository while GitHub provides it free of charge and no private secrets are exposed. Any future paid promotion or infrastructure requires an explicit decision rather than becoming a hidden dependency.
