# Runner-MCP implementation map

| Component | Primary implementation paths |
|---|---|
| runtime/self-update | `self_update.py`, `self_update_install.py`, `runtime_smoke.py`, `build_identity.py` |
| project/source | `config.py`, `known_project_catalog.py`, `known_project_local_source.py`, `source_control.py` |
| test execution | `test_runner.py`, `adapters/*` |
| mailbox/watchers | `github_mailbox.py`, `github_watcher.py`, `github_runtime.py`, `completion_delivery.py`, `completion_feedback.py`, `bridge_*.py` |
| Fabric bridge | `fabric_bridge.py`, `bridge_mcp_executor.py`, `fabric_live_overview.py`, `fabric_continuity_status.py` |
| qualification/bootstrap | `fabric_agent_qualification.py`, `fabric_agent_runtime.py`, `fabric_worker_qualification_provisioning.py`, `fabric_disposable_target.py`, `fabric_bootstrap.py`, `fabric_a6_binding_repair.py` |
| deploy/migrate/backup | `deployment_manager.py`, `deployment_jobs.py`, `migration_jobs.py`, `migration_planning.py`, `database_manager.py` |
| safety/approval/retention | `operational_safety.py`, `approval_manager.py`, `release_operation_lock.py`, `retention_preview.py`, `retention_pruning.py` |
| CI runner | `ci_runner_*.py` |
| service lifecycle | `service_manager.py`, `service_journal.py`, `autostart.py`, `cron_autostart.py`, `autostart_activation.py` |
| tunnel/connectivity | `tunnel_*.py`, `aifordable_relay.py` |
| diagnostics/audit | `safe_diagnostics.py`, `audit.py`, `text_redaction.py`, `host_integrity*.py`, `build_identity.py` |
| artifact/mirror custody | `artifact_custody.py`, `fabric_repository_mirrors.py`, `fabric_repository_mirror_activation.py`, `fabric_update.py` |
| MCP server/interface | `server.py`, `http_middleware.py`, `plugin_package.py`, public MCP/HTTP integration tests |

Project-specific fixed adapters such as current Bewind qualification modules remain children of qualification/artifact components, not separate generic authority.
