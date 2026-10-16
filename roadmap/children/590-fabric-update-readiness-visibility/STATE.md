# Fabric update readiness visibility — state

status: SOURCE_CANDIDATE_WAITING_CI
source_candidate_version: 0.1.26
branch: `chatgpt/590-bounded-fabric-update-readiness-v0126`
parent: Runner-MCP #590; Runner-Fabric #924

Read-only GitHub-archive and local-custody preflight failures now have a fixed blocked status for recognized categories and a static generic unavailable code otherwise. No secrets or release approval in the response. The normal success response and all mutating update methods remain unchanged.

Next: create PR, qualify its exact head with lint/pytest/build/demo/installer/attribution, merge only after green CI and enforced rules. No live installation or rollback bypass.
