# Task 32 — alpha launch-readiness gap audit

Date: 2026-09-24

## Scope

Repository/readiness review only.

This review does **not** create a tag, GitHub release, package publication, registry/ecosystem submission, repository-description/topic change or external community post.

## Executive conclusion

Runner MCP's code, package metadata and public validation pipeline are technically close to a first alpha release candidate, but the repository is **not yet ready to tag**.

The blocking work is documentation reconciliation, not a demonstrated runtime/code failure.

At the reviewed checkpoint:

- package version is `0.1.0`;
- package classifier is Alpha;
- exact current-main checkpoint `955f596d6ece4eeba602fc4d23b79139ca47cd77` passed public CI run 35966712012;
- that run passed compile, Ruff, whitespace, **1267 pytest tests / 3 warnings**, built release artifact and clean five-minute demo;
- no `v0.1.0` tag exists;
- no GitHub release exists;
- the repository description still uses older wording;
- GitHub topics are empty.

Before a tag is created, several public documents need to be reconciled with the current implementation and actual release state.

## Package metadata

`pyproject.toml` is internally suitable for an alpha candidate:

- package: `runner-mcp`;
- version: `0.1.0`;
- Python: `>=3.12`;
- MIT license metadata;
- Alpha classifier;
- public Homepage/Repository/Issues/Documentation/Changelog URLs;
- bounded runtime dependency ranges;
- console entry point `runner-mcp = runner_mcp.cli:main`.

No package-metadata blocker was demonstrated in this review.

The final release tag must still point to the exact commit whose package version is `0.1.0` and whose exact-main CI is green.

## Release validation mechanics

The public validation path is present and coherent:

### GitHub CI

`.github/workflows/validation.yml` runs on main/pull requests and contains:

- Python compile;
- Ruff;
- pytest;
- whitespace validation;
- built release-artifact smoke;
- clean five-minute demo.

The workflow uses read-only repository contents permissions and pinned checkout/setup-python action commits.

### Local release convenience check

`scripts/release-check.sh` covers:

- compile;
- Ruff;
- pytest;
- whitespace;
- built artifact;
- clean demo.

It correctly states that local checks do not replace exact-commit GitHub CI.

### Artifact smoke

`scripts/release-artifact-smoke.sh`:

- builds both sdist and wheel;
- checks artifact names against package version;
- rejects several private/runtime artifact path patterns;
- installs the built wheel into a clean venv;
- verifies the CLI version/help surface.

At the Task 32 claim checkpoint, exact main `955f596d6ece4eeba602fc4d23b79139ca47cd77` passed CI run 35966712012 fully green.

Because documentation must still change, that checkpoint must **not** be treated as the final release/tag commit. The final documentation-reconciled commit needs its own exact green main CI evidence.

## Five-minute demo and onboarding

`docs/DEMO.md` remains consistent with the core launch promise:

- local installation;
- one allow-listed project;
- doctor/status/guide;
- predefined tests;
- emergency stop;
- loopback-only server;
- no database/service/deployment/production setup required for the demo.

`QUICKSTART.md` reflects the current local read-only PostgreSQL restore preflight and clearly states that restore execution/PITR remain unimplemented.

No five-minute-demo blocker was demonstrated.

## Security policy

The root `SECURITY.md` is structurally suitable:

- pre-tag support model is explicit;
- private vulnerability-reporting guidance is safe;
- public reports are told not to include credentials or infrastructure;
- trust boundaries are linked.

One wording defect is now present:

> `database restore is not implemented`

Task 31 added a **local read-only restore preflight**. Database restore **execution** remains unimplemented.

The security policy should therefore distinguish:

- implemented read-only restore preflight;
- unimplemented restore execution/PITR/production recovery.

This is documentation drift, not a widening of restore authority.

## Public repository hygiene

The repository has concrete public-data hygiene controls:

- bug issue form warns against credentials/private infrastructure/customer data;
- feature form requires generic examples and no private infrastructure values;
- pull-request template contains a public-repository hygiene checklist;
- `tests/security/test_public_examples.py` verifies the public env/project examples retain placeholders/no bearer secret;
- release checklist requires a manual release-diff review for secrets, real hosts, usernames, paths, DSNs, service names and raw private logs;
- artifact smoke rejects several private/runtime artifact shapes.

### Launch-readiness wording defect

`docs/LAUNCH_READINESS.md` currently says:

> the latest privacy scan is clean

No repository-wide automated privacy scanner was demonstrated by this review. The directly verifiable automation is narrower: public-example tests plus artifact checks, with a manual release-diff hygiene review required by the release checklist.

The readiness document should name the controls that actually exist rather than imply a broader generic scan.

## Changelog drift — release blocker

`CHANGELOG.md` currently says:

- `## Unreleased`
- “No user-visible changes recorded after the v0.1.0 release-candidate cut.”
- `## 0.1.0 - 2026-09-23`
- “First alpha release candidate.”

This is no longer accurate.

User-visible work landed after that candidate text, including at least:

- privacy-safe guided connectivity/updated private-tunnel guidance;
- local read-only PostgreSQL restore preflight;
- deployment/rollback completion-delivery expansion and related user/operator behavior.

Also, there is currently **no `v0.1.0` tag and no GitHub release**.

Before tagging, the changelog must be reconciled so it does not make a dated version section look like an already-published release while simultaneously claiming there were no later user-visible changes.

The documentation follow-up should keep the distinction explicit between:

- unreleased/current 0.1.0 alpha candidate contents;
- an actually tagged 0.1.0 release.

Do not fabricate a release date before the tag is authorized.

## Launch copy drift — release blocker

`docs/LAUNCH_COPY.md` says the optional GitHub mailbox is:

> for a very small allow-list of status/test actions

That understates the current implementation. The bridge remains strict and bounded, but it now has configured operational actions beyond status/test, including bounded service/database/deploy/rollback/self-update paths with their own safety gates.

The launch copy should describe it as a strict bounded allow-list of configured operational actions and retain the important non-goals:

- no arbitrary command;
- no arbitrary path;
- no generic shell;
- no approval grant through the mailbox;
- no restore/production mutation authority.

## README formatting defect — release blocker

README currently contains the literal characters:

`\n\n`

between the self-update compatibility paragraph and the Fools2Tools/public-launch paragraph.

That is a public rendering defect and should be replaced with a real paragraph break before the release tag.

## Connectivity known-limitation wording

The changelog known limitations still says:

> guided private-tunnel/reverse-proxy onboarding is not yet one-click

Task 29 added privacy-safe guidance, while automatic tunnel/TLS/DNS/firewall/proxy provisioning intentionally remains outside Runner MCP.

The limitation should be narrowed to the actual missing automation/provisioning rather than suggesting that guidance itself is absent.

This is lower severity than the changelog release-state mismatch, but it should be reconciled in the same documentation slice.

## Private-host Task 10 proof

Task 10 remains externally BLOCKED on a usable private-host self-update/recovery proof.

That does **not** by itself invalidate a repository-level public alpha candidate, provided the public release wording stays bounded to what public code/tests/CI demonstrate.

Current reviewed launch material does not claim that a specific private installation has successfully completed the blocked live proof.

Release notes must therefore avoid claims such as:

- live-proven upgrade on the private production host;
- proven end-to-end private-host recovery;
- production readiness.

The public alpha may accurately describe implemented/tested self-update and recovery mechanisms, while recording private-host live proof as an external operational limitation.

## GitHub repository metadata

Live GitHub metadata at review time:

- repository is public;
- current description:
  `Secure, self-hosted MCP server for controlled remote development, testing, deployment and server operations.`
- topics: empty.

Prepared launch copy proposes:

- description:
  `Security-first self-hosted MCP for controlled AI development and staging operations without a general-purpose remote shell.`
- topics:
  `mcp`, `model-context-protocol`, `self-hosted`, `ai-tools`, `developer-tools`, `devops`, `staging`, `security`, `python`, `automation`.

Changing repository description/topics is a public repository-setting action and remains explicitly human-controlled.

This review does not perform it.

## Tag and GitHub release state

At review time:

- `v0.1.0` does not exist;
- no latest GitHub release exists.

That matches the fact that launch readiness still lists the first tagged alpha as pending.

The first tag must be created only after:

1. repository documentation reconciliation lands;
2. the final intended release commit is on `main`;
3. exact-main GitHub CI is fully green for that exact commit;
4. the user explicitly authorizes the tag/release.

## Registry/ecosystem publication

No registry/ecosystem submission should be made from this review.

Before any submission:

- verify the target registry's current packaging/metadata requirements;
- use the actually tagged/released version;
- verify its installation path;
- avoid adding a paid runtime dependency or hosted service merely for discovery.

This remains a separate human-controlled/publication step.

## External community publication

Show HN, Reddit/community, LinkedIn and other launch posts remain separate human-controlled actions.

Prepared copy is useful after the release is real, but must first be reconciled with current mailbox capability and populated with the exact released version/link/validation evidence.

## Demonstrated repository blockers before tag

The bounded repository blockers are documentation-only:

1. reconcile `CHANGELOG.md` with the actual unreleased/tag state and post-RC user-visible changes;
2. update `SECURITY.md` to distinguish read-only restore preflight from restore execution;
3. update `docs/LAUNCH_COPY.md` mailbox wording to current bounded operational capability;
4. remove literal `\n\n` from README;
5. replace the unsupported broad “latest privacy scan is clean” wording in `docs/LAUNCH_READINESS.md` with the actual public-example/artifact/manual-diff controls;
6. clarify the old “guided connectivity not one-click” limitation so it refers to automatic provisioning, not missing guidance.

No implementation/runtime change is required to address these findings.

## Smallest justified follow-up

Queue one documentation-only task:

**Alpha release documentation reconciliation**

Acceptance:

- touch only public release/readiness documentation needed by the six demonstrated drift items;
- no version bump;
- no tag;
- no GitHub release;
- no repository settings mutation;
- no package publication;
- no ecosystem submission;
- no external post;
- after merge, require exact-main green CI before any release authorization is requested.

## Human-controlled actions after repository blockers are cleared

The following remain explicit user decisions/actions:

1. authorize the exact `v0.1.0` tag target after final green main;
2. authorize/create the GitHub release and final release notes;
3. set GitHub repository description/topics;
4. decide whether/where to publish a package or MCP ecosystem/registry entry after current requirements are checked;
5. decide timing/content of external community posts.

## Conclusion

Runner MCP is technically close to a first public alpha: package metadata is coherent, artifact/demo validation exists, and the reviewed main checkpoint is fully green.

Do not tag the current repository yet.

First reconcile the six bounded public-documentation drift items, let that exact final main commit pass the complete CI pipeline, and only then ask for explicit authorization for the tag/release/publication steps.
