# Failure Museum — F30 Q7 offline readback initial Ruff import order (2026-10-21)

## Trigger

Runner-MCP #791 first exact-head validation run `39551612601` stopped at Ruff `I001`, before pytest. A newly added test subprocess import left Python standard-library `stat` after `subprocess` and `sys` in `tests/test_fabric_release_private_custody.py`.

## Cause and correction

Simple source formatting defect; no application-level failure or host effect. Sorted `stat` before `subprocess`/`sys` (commit `ab0019bfed71622c57ba3b6c61d4e0e594459aaa`). Subsequent exact-source CI passed Ruff and pytest before additional first-host lab artifact delivery was added to the same feature PR. The final PR head must pass **its own** complete CI; prior partial checks cannot approve a changed head.

## Operational scope

Only GitHub CI and source files. No physical Black import, file migration, A6 journal recovery, any of the six original live serving roles, existing relay or Claude/Qwen provider model was touched. Continue to distinguish local unsigned Q7 import/readback from genuine physically independent A6 update journal retention and original-client ACK.
