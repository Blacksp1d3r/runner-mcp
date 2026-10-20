# #669 — independent six-role process pins

status: SOURCE_CANDIDATE_CI_PENDING
source_version: 0.1.63 (candidate; not on production)
owner_issue: Runner-MCP #669
existing_comparator: src/runner_mcp/serving_witness_preflight.py
new_entry: signed_six_role_process_pin_preflight
public_result: six_role_process_pins_consistent_offline (NEVER live attestation)
live_original_client: 0.1.38 / wheel SHA NULL / source NULL / A6 0 of 11
existing_a6_repair: #509 CLOSED source, no live invocation
production_mutation: false
operator_pre_admission: WAIT correct-host owner-pinned real six role inventory and old installed wheel
