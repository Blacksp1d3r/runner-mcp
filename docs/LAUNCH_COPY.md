# Launch copy

These are reusable drafts for a future Runner MCP release.

They are intentionally factual, low-hype and version-neutral. Update the validation numbers and release version before posting. External posting remains a human-controlled action.

## Core positioning

Short:

> Let an AI run tests and controlled staging operations on your own server without giving it a general-purpose remote shell.

One paragraph:

> Runner MCP is an open-source, self-hosted MCP service for controlled development and staging operations. Instead of giving an AI client an arbitrary shell, you configure projects, predefined test profiles and narrowly scoped operational capabilities. Runner MCP adds audit logging, an external emergency stop, strict argument validation, bounded output, human approval gates for higher-risk staging actions and fail-closed safety checks.

Project signature:

> Runner MCP — a Fools2Tools project. Practical tools from real problems.

## Suggested GitHub description

> Security-first self-hosted MCP for controlled AI development and staging operations without a general-purpose remote shell.

Suggested topics:

`mcp`, `model-context-protocol`, `self-hosted`, `ai-tools`, `developer-tools`, `devops`, `staging`, `security`, `python`, `automation`

## Release headline

> Runner MCP vVERSION — controlled AI operations for self-hosted development and staging

Release intro:

> This is the first public release of Runner MCP, a Fools2Tools project built around a simple constraint: an AI client should be able to help verify and operate real development/staging projects without receiving a general-purpose remote shell.

Then list the actual release capabilities and validation result. Do not copy the entire roadmap into release notes.

## Show HN draft

Title:

> Show HN: Runner MCP – let an AI operate staging without giving it a shell

Body:

> I wanted an AI assistant to keep helping with real development work — inspect configured projects, run tests and eventually handle controlled staging operations — but I did not want the normal interface to be an unrestricted remote shell.
>
> Runner MCP is the result. It is a self-hosted Model Context Protocol service with a deny-by-default model. Projects and test profiles are configured ahead of time, MCP arguments are strict, output is bounded/scrubbed, there is an operator emergency stop, and higher-risk staging actions use short-lived local human approvals.
>
> The project also has an optional GitHub mailbox transport for a strict bounded allow-list of configured operational actions. The bridge uses a fixed request/result protocol, replay protection and the same action-specific safety gates; it does not accept arbitrary commands, executable paths, filesystem paths, approval grants, database restore or production mutation requests.
>
> The repository includes a Quickstart and a five-minute local demo. I would especially value feedback on the security boundaries, onboarding and places where the configuration model is still too complicated.
>
> Runner MCP is open source under the MIT license and is a Fools2Tools project.

Before posting, add the released repository link and exact version.

## MCP Registry / directory draft

Registry name:

> io.github.blacksp1d3r/runner-mcp

Title:

> Runner MCP

Tagline:

> Controlled self-hosted AI operations without a general-purpose remote shell.

Short description:

> Security-first self-hosted MCP for configured development and staging operations. Runner MCP exposes bounded project, test, service, database, deployment and rollback capabilities with audit, emergency-stop and approval controls instead of arbitrary remote shell input.

Primary audience:

> Developers and small teams who want AI-assisted work against self-hosted development or staging systems while keeping authority narrower than SSH or a generic remote-control agent.
## Developer-tool directory draft

Name:

> Runner MCP

Tagline:

> Controlled self-hosted MCP operations without a general-purpose remote shell.

Description:

> Runner MCP is an open-source MCP service for AI-assisted development and staging. It exposes configured projects and predefined operations through a deny-by-default interface, with audit logging, bounded output, an emergency stop and human approval gates for higher-risk staging actions.

## Reddit/community draft

Suggested title:

> I built a self-hosted MCP so my AI tools can run predefined staging operations without arbitrary shell access

Body:

> I kept running into the same trade-off: either the AI could only talk about a project, or I had to give a remote-control tool much broader access than the routine job needed.
>
> Runner MCP takes a narrower approach. You configure projects and exact test profiles locally. The client selects names, not command strings. Staging service/database/deploy/rollback functions are separately constrained, and higher-risk actions require a local approval.
>
> The current public repo includes a safe local demo, threat model and tests for the fail-closed boundaries. I am interested in feedback from people running self-hosted development environments, especially around onboarding and threat-model gaps.

Choose a community whose rules explicitly allow project sharing. Do not cross-post the same text everywhere.

## LinkedIn draft

> A recurring problem in AI-assisted development is access: useful automation needs to verify real systems, but a general remote shell is often much more authority than the task needs.
>
> I have been building Runner MCP, an open-source self-hosted MCP service that turns common development and staging operations into explicit, auditable capabilities. Projects and test profiles are allow-listed, output is bounded, there is an external emergency stop, and higher-risk staging actions require local human approval.
>
> Runner MCP is part of Fools2Tools: practical tools that grow out of problems encountered while doing the work.
>
> The focus now is making the safe core simple enough that people can evaluate it without reading the source code first.

Add the release link only when a public release is ready.

## What not to claim

Do not describe Runner MCP as:

- production-ready unless a future release explicitly reaches and documents that bar;
- a sandbox for untrusted code;
- a replacement for all SSH or all operational tooling;
- immune to compromise;
- a way to bypass human approval;
- a hosted service when the public project is still self-hosted software.

Do not publish real installation screenshots when they contain infrastructure names, paths, addresses, tokens, logs or customer/project identifiers.
