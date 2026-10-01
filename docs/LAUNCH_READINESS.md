# Public launch readiness

Runner MCP should be promoted only as fast as a new user can safely understand, install and verify it.

The goal is a useful open-source launch without paid advertising or paid infrastructure.

## Current launch gate

Completed:

- README states the problem and safety boundary before the feature inventory;
- repository-safe architecture overview is visible near the top of README;
- QUICKSTART provides the full guided installation path without requiring source-code reading;
- a separate [five-minute local demo](DEMO.md) exists and is exercised end to end on clean Ubuntu 24.04 / Python 3.12 in public CI;
- `runner-mcp doctor`, status, guide and emergency-stop workflows are documented;
- security baseline, threat model, operator-safety rules and test-execution trust boundary are public;
- root [security reporting policy](../SECURITY.md) is present;
- the public repository rule forbids real infrastructure details, public-example tests verify placeholder/no-secret examples, artifact smoke rejects private/runtime artifact shapes, and the release checklist requires a manual public-data diff review;
- mailbox transport is documented as optional and bounded rather than a shell bypass;
- [CHANGELOG](../CHANGELOG.md), [release checklist](RELEASE_CHECKLIST.md) and reusable [launch copy](LAUNCH_COPY.md) are prepared;
- bug/feature issue forms warn against posting private installation data;
- pull requests get a security/public-repository hygiene checklist;
- public CI installs the package and runs compile, Ruff, pytest and whitespace validation;
- no application telemetry is added for marketing.
- `v0.1.0` is published as the first GitHub pre-release from exact green commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`;
- the published release notes preserve the alpha limitations and exact validation provenance;
- the GitHub repository description and discovery topics are live with the prepared wording;
- PyPI Trusted Publishing is live and `aifordable-runner-mcp` `0.1.1` was publicly published;
- canonical `0.1.2` publication completed from exact commit `83175f439c60346f92b5759a90993c3b8f5352f8`;
- PyPI `aifordable-runner-mcp==0.1.2`, the official MCP Registry entry `io.github.Blacksp1d3r/runner-mcp`, and GitHub pre-release `v0.1.2` were verified through issue #101;
- the GitHub `v0.1.2` tag points to the exact validated release commit.

Still required before a broader launch:

- keep clean published-package installation verification current for each release candidate;
- complete the remaining free secondary-directory submissions tracked in issue #101;
- publish one technical launch post only when the current release/docs are ready, then adapt later outreach from real feedback rather than mass cross-posting.

## Free discovery plan

The repository itself is the first discovery layer:

1. problem and safety boundary;
2. five-minute evaluation path;
3. architecture overview;
4. concrete security guarantees and non-goals;
5. reproducible demo;
6. tagged releases with concise release notes.

After that, use the prepared material for appropriate developer and self-hosted communities. External posting remains a separate human-controlled action.

## Launch package

Prepared copy covers:

- GitHub repository description and topic suggestions;
- first-release headline/intro;
- a technical Show HN-style introduction;
- developer-tool launch directories;
- relevant self-hosted/MCP/Python community posts;
- a professional-network announcement.

See [LAUNCH_COPY.md](LAUNCH_COPY.md).

The copy leads with the problem and the implemented technical design, not marketing superlatives.

Core sentence:

> Runner MCP gives AI clients a narrow, auditable path to self-hosted development and staging operations without exposing a general-purpose remote shell.

## Metrics without tracking users

Prefer platform-level public signals instead of embedding analytics in Runner MCP:

- GitHub stars and forks;
- issues and discussions from new users;
- release downloads where the hosting platform exposes aggregate counts;
- external references and community feedback.

Do not add application telemetry solely for marketing.

## Cost rule

The default launch path must remain usable without buying advertising, paid hosted CI minutes or a new hosted service. Standard GitHub-hosted CI may be used for this public repository while GitHub provides it free of charge and no private secrets are exposed.

Any future paid promotion or infrastructure requires an explicit decision rather than becoming a hidden dependency.
