# Known-project onboarding with multiple trusted project parents (#740)

The `enercue` project is already listed in Runner-MCP's fixed
`KNOWN_PROJECTS` allowlist. It was **not** among the six locally registered
staging projects observed through the connected first-party control plane
on 2026-10-19. GitHub source preflight returned `ready`, but
`known_project_preflight("enercue")` returned `ambiguous-parent` because
registered project checkouts have more than one parent.

## Operator-controlled, narrow destination selection

Runner-MCP version 0.1.39 adds the **optional**
`anchor_project_id` argument to the existing
`known_project_preflight` and `prepare_known_project` operations.
It accepts only an *already registered project's short code*, not a path,
repository, hostname, arbitrary command, secret, or worker identity.

The chosen project's existing trusted checkout determines the
parent folder of the new catalogued clone. No other directory may be
supplied. Select the appropriate already-registered staging project's
parent on the actual authorized Runner-MCP machine; do **not** assume that
the visible GitHub runner, Hyper-V lab, Qwen guest, or Windows desktop
share the same storage or credentials.

Example read-only check, with an **illustrative** anchor only (it is not
a recommendation to use that parent's real storage):

```text
known_project_preflight(
  project_id="enercue",
  anchor_project_id="<an-already-registered-project-code>"
)
```

If the response is `ready-to-prepare`, a separately authorized operator
may call `prepare_known_project` with the same exact two arguments.
The existing `register_known_project(project_id="enercue")` then
discovers exactly one origin-verified clone and registers it, checking a
reload of its private project settings before confirming success.

Fail-closed handling:

- Omitting `anchor_project_id` keeps the existing `ambiguous-parent`
  response when more than one parent is configured.
- Unknown anchors, non-existing root directories, symlinks, missing
  permissions, or a wrong-origin occupied target are rejected.
- If an exact EnerCue clone already exists under another configured
  parent, refuse creation of a duplicate (`exact-clone-elsewhere`).
- A successful source checkout or registration **does not** prove
  Claude/Qwen existence, model operation, the Agent Bus result/ACK,
  or grant CI, GitHub merge, secrets or production access.
- Never copy private absolute host paths, access tokens, environment files,
  customer data or console dumps into a public repository or GitHub issue.

## Evidence and release boundary

0.1.39 is a **source/release candidate**; no live control host change is
implied by a PR or merge. Existing 0.1.27-family installations may expose
only the one-argument tools. Validate version, tool schema and original
host identity using the normal first-party managed update process before
trying the optional argument. Do not override current managed-version
activation gates or force an upgrade to bypass Agent Bus continuity.

The first physically executed Claude #89 / Qwen #118 EnerCue code task
remains independent of this staging registration, using the existing
authorized private model workspace and task-bounded patch handoff.
