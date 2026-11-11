# #669 — independent six-role process pins

status: SOURCE_MERGED_LIVE_UNQUALIFIED
source_version: 0.1.63 (MERGED, not on production)
owner_issue: Runner-MCP #669
existing_comparator: src/runner_mcp/serving_witness_preflight.py
new_entry: signed_six_role_process_pin_preflight
public_result: six_role_process_pins_consistent_offline (NEVER live attestation)
live_original_client: 0.1.38 / wheel SHA NULL / source NULL / A6 0 of 11
existing_a6_repair: #509 CLOSED source, no live invocation
production_mutation: false
operator_pre_admission: WAIT correct-host owner-pinned real six role inventory and old installed wheel

ci_regression_initial: 39478798560 (1 failed, 3865 passed; negative synthetic test fixture mapped explicit None to default)
ci_fix: distinct sentinel for omitted pins; explicit None must reach validator; RMCP-F-0068
ci_exact_head_revalidation: 39479195410 SUCCESS

merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/781
merged_sha: 8d0405490c73bc324a522e66e5e596649d169371
ci_head: a9b9df31aa8e79e29cf85183e75e6ba25dca1215
ci_validation: 39479195410 SUCCESS
ci_clean_ubuntu: 39479195458 SUCCESS
ci_attribution: 39479195285 SUCCESS
source_result_is_not_actual_serving_process_attestation: true
