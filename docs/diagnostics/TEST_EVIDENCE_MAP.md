# Runner-MCP test/evidence map

| Component | Primary current test surfaces |
|---|---|
| runtime/self-update | `tests/security/test_self_update*.py`, `tests/security/test_runtime_smoke.py`, install/release integration tests |
| project/source | `tests/security/test_source_control.py`, `tests/unit/test_known_project_catalog.py`, private-config tests |
| test execution | `tests/security/test_test_runner.py`, adapter unit tests |
| mailbox/watchers | bridge/mailbox/watcher/runtime unit tests + control-path compatibility integration |
| Fabric bridge | `tests/unit/test_fabric_bridge.py`, continuity/live overview/coding availability tests |
| qualification/bootstrap | Fabric qualification/disposable/bootstrap unit + integration tests |
| deploy/migrate/backup | deployment/migration/database security tests |
| safety/approval | operational safety, approval manager, release lock, retention tests |
| CI runner | `tests/unit/test_ci_runner_*.py`, `tests/integration/test_ci_guest_mcp.py` |
| service lifecycle | service manager/journal, autostart/cron tests |
| tunnel/connectivity | tunnel config/health/readiness/runtime/topology tests |
| diagnostics/audit | safe diagnostics, audit, build identity, text redaction, host integrity tests |
| artifact/mirror custody | artifact custody + repository mirror + independent release-archive readiness integration/unit tests |
| MCP server/interface | `tests/integration/test_mcp_http.py`, `tests/integration/test_ci_guest_mcp.py`, `tests/security/test_http_security.py`, plugin-package tests |

Use the narrowest invariant test first. Broad MCP/clean-demo tests are final integration evidence, not the first debugging layer.
