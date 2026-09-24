# Task 38 — multi-project adapter boundary completion review

Date: 2026-09-24

Status: **COMPLETE — review only. One bounded adapter follow-up is justified.**

## Scope

This review checks whether a new project family can normally be added through configuration and a built-in adapter without teaching core configuration code about that framework.

No adapter/runtime behavior is changed by this review.

## What is already cleanly separated

Runner MCP has a small built-in adapter registry with only `generic` and `python`.

The adapter protocol currently owns:

- stable adapter identity and display metadata;
- safe capability inspection;
- supported test/migration preset names;
- automatic test-preset selection;
- automatic migration-preset selection.

The registry is code-owned and deny-by-default. Configuration cannot name an importable Python module or load project code as a plugin.

The generic adapter deliberately guesses nothing.

The Python adapter performs bounded local inspection only. It checks allow-listed markers/executables and returns booleans/preset names. It does not return filesystem paths or command arrays.

Existing adapter tests also prove that symlinked roots, marker files and executables do not become trusted capabilities.

## Core paths that are correctly project-generic

The execution layers are largely project-agnostic after configuration has been produced:

- `TestRunner` executes only predefined validated profiles;
- service control uses configured safe aliases rather than framework knowledge;
- deployment consumes configured tests, service alias and migration flag;
- source synchronization is a Git/GitHub platform capability, not application-framework branching;
- PostgreSQL backup/migration support is an explicit supported database substrate, not a per-project special case;
- approval, audit, queueing, emergency-stop and retention logic operate on project codes and typed configuration.

Those platform choices may be narrow, but they do not require project-specific branches such as “if project X”.

## Concrete Phase 8 gap

The adapter currently chooses **which preset name** should be used, but core `config_manager.py` still knows **how framework presets are materialized**.

For test profiles, core configuration contains Python-specific branches for `pytest`, `ruff` and Python virtual-environment executable discovery.

For migrations, core configuration contains Alembic-specific branches for locating `alembic`, `alembic current` and `alembic upgrade head`.

This means a future built-in Node, Ruby or another Python-framework adapter that needs its own safe presets cannot be added solely by registering the adapter. Core configuration would also need another preset branch.

That is the exact project-family leakage Phase 8 is intended to remove.

This is not an alpha security defect: every existing branch is fixed, local, validated and covered by tests. It is an extension-boundary incompleteness.

## Safe capability summaries

The current public adapter surfaces are appropriately bounded. `AdapterInfo.public_dict()` returns only adapter ID/name, supported preset names and service/deployment support booleans.

Project inspection returns capability booleans and selected preset names. It does not return project root paths, detected executable paths, argv, environment values, service units, health URLs or credentials.

That contract should remain unchanged when preset construction moves behind the adapter boundary.

## Built-in adapters versus dynamic plugins

Phase 8 does **not** require a runtime plugin loader.

A dynamic “module from configuration” model would widen the trust boundary because project configuration could choose executable Python code. That would conflict with the current deny-by-default design.

The safer extension model remains configuration first, then a reviewed built-in adapter for reusable project-family detection/presets, then a new core capability only when configuration/adapter semantics cannot express the need.

## What should remain core

Safety/emergency-stop enforcement, command sandboxing/output limits, service alias authorization, database credential/storage handling, deployment/rollback locking, approval/audit logic, Git source-integrity rules and public/private output scrubbing remain core.

Adapters may choose from safe built-in recipes; they must not become a second execution engine.

## Bounded follow-up

One CODE follow-up is justified: move **built-in non-custom preset materialization** behind the adapter boundary.

The follow-up should:

- extend the adapter contract with typed methods/recipes for supported test and migration presets;
- move Python-specific executable discovery and fixed `pytest`, `ruff` and `alembic` recipe construction out of generic core branching;
- keep `custom` as an explicit local-operator configuration path with the existing validation;
- make adding a new reviewed built-in adapter possible without adding another framework-specific preset branch to core configuration;
- preserve the same fixed/safe argv semantics and symlink checks;
- preserve capability-summary privacy;
- keep the registry code-owned and deny unknown adapters;
- add adversarial tests proving adapters cannot expose paths through public inspection and unknown presets fail closed.

The follow-up must not add dynamic imports, entry-point loading, arbitrary shell strings, project-code execution during inspection, new framework dependencies or speculative adapters.

## Alpha decision

Phase 8 is **functionally usable but not structurally complete**.

The current generic/Python adapters are safe for the existing alpha use cases, so no release-blocking framework adapter is required. However, the hardcoded Python/Alembic preset materialization is a concrete architectural seam worth closing before claiming that new project families normally require only adapter/configuration work.

Queue one bounded refactor; do not add more adapters until a real reusable need exists.
