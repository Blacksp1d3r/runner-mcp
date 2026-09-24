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

Still required before a broader launch:

- create the first tagged alpha release from an exact green commit;
- verify the release installation path and release notes;
- set the GitHub repository description/topics to the prepared wording;
- prepare an MCP ecosystem/registry submission only after its current packaging requirements are verified;
- decide the timing of external community posts.

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
