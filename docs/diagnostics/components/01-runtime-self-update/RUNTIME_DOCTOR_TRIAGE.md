# Runtime doctor — source baseline vs active generation

## A6 safety classification is not installation admission (2026-10-20)

Original-client Doctor may report `fabric_a6_binding_state=pass/not_configured_0_of_11`. This specifically means BOTH private A6 journal/evidence roots are absent and NONE of the 11 approved keys are present: safe no-op configuration, not readiness. The independent read-only Fabric bridge simultaneously reports `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`. NEVER count that green diagnostic row as permission to update. Existing conditional repair in `fabric_a6_binding_repair.py` only applies if both correct-host 0700 roots already exist; calling its parent `fabric_agent_restart` is a SERVICE mutation and is not a discovery substitute. See `docs/operations/F30_FIRST_NODE_ADMISSION_GATES.md` and #509/#942.

## Public diagnostic interpretation (2026-10-19)

The original connected central instance was confirmed running 0.1.38 after guarded owner-operated cutover. The two outstanding doctor FAIL results are **safety refusals**; they do not show that the server is down.

| Check | Origin | Current detail | Interpretation |
| --- | --- | --- | --- |
| `self_update_source_baseline` | `SelfUpdateManager.runtime_status().source_baseline_aligned` | `source_baseline_drift` | Historical self-update commit and source checkout are not proven aligned |
| `self_update_runtime_activation` | `active_runtime_revision` and `runtime_activation_aligned` | `active_revision_unavailable` | No independently attested revision of the actually serving process |
| `self_update_ready` | combined preflight gates | `false` | Do not use in-place self-update |

`build_identity.installed_source_revision()` intentionally returns `None`; the old self-update history must **not** be promoted to an active build label. A matching installed distribution version is necessary for package identity checks but insufficient for loaded-module, source and wheel proof.

## Earliest evidence gap
Manual cutover records established active package version, first-party response and retention of the older release. They did **not** establish independent source/wheel signer trust, installed RECORD/module bytes and currently loaded process generation. Until those are qualified on the correct server, the errors must remain visible.

## Safety boundaries
- No mutation to state files merely to turn doctor green.
- No fabricated hashes, keys, host identities, or deployment evidence.
- Do not treat the new-Black non-serving staged host as the central connected host.
- Source-only offline checks cannot attest a serving process.
- Keep old release and rollback custody; A6/A7 remain separate admission requirements.

## Provenance and follow-up
See #669, #341 and #590, `roadmap/children/669-runtime-doctor-reconciliation/TASK.md`, `docs/diagnostics/topology/TRACEABILITY_RULES.md` and `docs/diagnostics/FAILURE_INDEX.md`. This is an existing, documented safety-gap family, not a newly proven defect requiring an invented Failure Museum ID.

## Independently attested generation design — 2026-10-19

See [SERVING_GENERATION_ATTESTATION.md](SERVING_GENERATION_ATTESTATION.md).
No source SHA, wheel SHA-256, provider callback, package version or offline signature
alone may turn these historical Doctor checks green. The eventual guarded path
requires trusted signer custody, installed bytes, actual loaded serving process
and original-client generation ACK on the correct physical host, with a separate
authorized manual-install baseline. PR #742 separately contains RMCP-F-0045
exception containment in the provider boundary; that small source fix makes
unknown remain unknown and does not claim active provenance.
