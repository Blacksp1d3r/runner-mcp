# BPA-02-T — Validate the proposal with the real JSON Schema engine

Parent: [Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Related **blocked operator gate**: [#634](https://github.com/Blacksp1d3r/runner-mcp/issues/634). Scope: offline synthetic test correctness of the *already-merged candidate only*; do not modify or promote the operational manifest. No overlap with separate #381 Claude owner.

## Problem / outcome

BPA-02 [PR #633](https://github.com/Blacksp1d3r/runner-mcp/pull/633) currently uses a handwritten `_assert_draft_contract` test interpreter for a tiny JSON Schema vocabulary. Such a helper does not independently prove that the published Draft 2020-12 document is itself a valid JSON Schema or that the real evaluator enforces additionalProperties, required, const and distinct JSON types. A hand-rolled test may pass while a real consumer disagrees.

Use the permissively licensed, zero-subscription `jsonschema` dev-only dependency and `Draft202012Validator.check_schema` plus real `.validate` in synthetic tests. Preserve the YAML proposal and actual JSON Schema unchanged. Explicitly deny false qualification, private/nested extra fields, missing required fields, malformed type, wrong lane limit, and child contract order.

## Topology and hard boundaries

- Source of truth: `docs/standards/project_manifest_candidate.yml` and `.schema.json`. These remain documentation in `BLOCKED_AUTHORITY` state with `UNKNOWN` code/evidence/coordination, not `project.yml` at repository root.
- Test code: `tests/unit/test_repository_manifest_candidate.py`. Packaging: development extras in `pyproject.toml`, not runtime dependency.
- Never add a new runtime validator, host authority, path input, automated Git claim, Fabric scaffold endpoint, real storage/mirror action, issue #381 actuator, or live migration.
- No operator or filesystem authority granted by CI, JSON Schema validation, draft docs or this child.

## Execution algorithm

1. Inspect actual current main, prior exact-head PRs and active owners.
2. Replace handwritten test mini-validator with official Draft 2020-12 schema check and instance validation; make versioned dev-only dependency explicit.
3. Add synthetic denial tests for false qualification, type confusion, missing/unknown nested keys and untrusted private selectors.
4. Run exact-head Ruff/pytest plus built-artifact and clean demo CI, attribution, review. If failures occur, resolve only confirmed branch failures. Never bypass CI.
5. Merge only source-test scope and record exact SHA/evidence; keep parent #630 and operator issue #634 OPEN, status of actual BPA-02B BLOCKED.

## Failure Museum and handoff

Root cause class: *schema self-test false confidence through a bespoke test interpreter*. Failure when Draft202012 spec semantics change, schema malformed, or runtime dependency implied by transient packages. Prevention: official validation engine, check_schema, explicit dev dependency, adversarial tests. No physical or installed-runtime claims. Resume from STATE, branch/PR exact HEAD and CI evidence.
