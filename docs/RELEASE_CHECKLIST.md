# Release checklist

Runner MCP releases should be boring, reproducible and free of deployment-specific information.

This checklist applies to public releases. A release does not authorize any production mutation or weaken the runtime safety model.

## Code and validation

- version and release scope are intentional;
- the release commit is on `main`;
- public CI is green on the exact release commit;
- Python compile, Ruff, pytest and whitespace checks are green;
- `bash scripts/release-check.sh` is available as a fail-fast local convenience check for the same validation families plus artifact/demo smoke tests; it does not replace green GitHub CI on the exact release commit;
- security-sensitive changes have dedicated fail-closed tests;
- no test is being treated as green merely because a runner or quota prevented it from starting.

## Public-repository hygiene

Review the release diff for:

- credentials, tokens or private keys;
- real IP addresses, hostnames or internal domains;
- private endpoints or ports;
- usernames;
- real absolute deployment paths;
- database endpoints, DSNs, dumps or backups;
- private service names;
- raw logs copied from a real installation.

Only generic placeholders belong in public examples.

## Documentation

- README reflects current behavior;
- QUICKSTART uses commands that exist in the release;
- known limitations are explicit;
- security documentation matches implemented boundaries;
- CHANGELOG contains the user-visible changes;
- upgrade or migration notes exist when configuration semantics changed;
- AIfordable branding remains secondary to the Runner MCP product identity.

## Package metadata

Before publishing a package or registry entry:

- package version matches the release tag;
- supported Python version is correct;
- license metadata is correct;
- README renders correctly as package documentation;
- project URLs point to the public repository and documentation;
- no private configuration file is included in the built artifact;
- the wheel and source distribution pass `scripts/release-artifact-smoke.sh`;
- a clean environment can install the built wheel and run the documented CLI smoke checks;
- dependency, build-backend and interpreter changes have an explicit bootstrap/upgrade path consistent with `docs/SELF_UPDATE_COMPATIBILITY.md`; the no-dependency self-update path is not used to resolve them.

## Release notes

Release notes should contain:

1. what changed;
2. why it matters;
3. security-relevant behavior changes;
4. upgrade notes;
5. known limitations;
6. the validation result for the tagged commit.

Avoid claims such as “production safe”, “unhackable” or “fully autonomous”. Describe concrete guarantees and boundaries instead.

## Tag and release

Use a semantic version tag such as `v0.1.0`.

Before creating the tag, verify that the commit SHA is the one that passed CI. Do not move an existing release tag to a different commit.

## After release

- verify the release page and source archive;
- verify installation from the documented path;
- run `runner-mcp doctor` in a clean evaluation environment when practical;
- only then update launch copy or ecosystem submissions to the released version.

External community posts remain a separate human-controlled action.

## Cost rule

A release must not silently introduce a paid runtime dependency. Optional paid services may be documented in the future, but the basic self-hosted path and public project documentation should remain usable without them.
