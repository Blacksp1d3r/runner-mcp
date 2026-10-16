# Optional Fabric CI guest status — state

status: COMPLETE_SOURCE_ONLY
parent_issue: Runner-MCP #590
merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/706
merged_commit: 262fd4e25a9a0ad63a02c5ad825f288998775656
exact_head: f40b8421dca8188a0467a1c2c195f20889ee01fe
source_candidate_version: 0.1.25
validation_ci: 38927006209 SUCCESS
ubuntu_install_ci: 38927006272 SUCCESS
attribution_ci: 38927006246 SUCCESS
live_installed: false
mutation_authorized: false

Scope: only a bounded error result for the optional read-only CI guest status; unknown worker state stays unknown. Live original-client runtime still reported 0.1.9 with unverified artifact identity; missing guest capability and A6/A7 first-node qualification remain open.
