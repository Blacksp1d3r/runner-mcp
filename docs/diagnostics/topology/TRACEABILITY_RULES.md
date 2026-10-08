# Runner-MCP traceability rules

Every material action/result should be reconstructable from:

- tool/capability name;
- request/correlation identity where the public contract permits it;
- project semantic ID when applicable;
- exact source/revision identity;
- actor/approval/safety decision;
- build identity;
- job/state revision;
- peer protocol/interface/build evidence when crossing Fabric/MCP;
- external source or provider result category;
- sanitized audit/result evidence;
- replacement/recovery/replay relationship where applicable.

Rules:
1. caller text is intent, never authority;
2. arbitrary shell/path/endpoint/service/env input is not introduced to improve diagnosability;
3. missing evidence remains unknown/not-configured, never inferred healthy;
4. stale/replayed/copied state is distinguished from current trusted state;
5. a downstream failure is not repaired until the earliest divergent upstream edge is identified;
6. private deployment facts stay in private configuration/upstream infrastructure authority;
7. every closed reusable failure links a regression or qualification guard.
