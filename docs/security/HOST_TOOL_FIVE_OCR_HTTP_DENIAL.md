# #642 — authenticated HTTP denial of five production-declared OCR tools

This is **one disposable regression test**, not another host policy system.

The existing #654 oracle test verifies all five OCR qualification tool names
are actually declared and can be excluded from a synthetic primary-host
policy. The previously merged #1015/#1016 authenticated HTTP tests proved the
SDK interception with the safer `read_project_file` tool, but did **not** run
the five actual OCR `tools/call` names through the live SDK boundary.

This test extends the existing `test_host_tool_dispatch_http.py`:

- real TestClient MCP handshake, `tools/list`, and **all five actual**
  `bewind_ocr_qualification_*` / `bewind_ocr_runtime_image_prepare`
  `tools/call` requests;
- real SDK schema digest measured from the registered `build_mcp()` tools;
- one explicitly synthetic primary-host policy that does not grant OCR;
- each tool remains listed but is refused with the fixed
  `HOST_TOOL_NOT_PERMITTED` code;
- all five original OCR implementation methods are instrumented to count
  unexpected entry, ensuring the handlers are **never reached**;
- five separate bounded `denied:tool_not_granted_on_host` records in the
  existing audit log.

This has **no physical host or real OCR action**, no model executor,
no second issuer/service, no A7/I7, no production credentials, no actual
loaded-wheel provenance or signed policy. It does not merge or update
[#669 draft #1004](https://github.com/Blacksp1d3r/runner-mcp/pull/1004),
which remains owner-gated. Runner-MCP #642 remains OPEN for original-host
provenance, independent signed permits, original-client ACK and controlled
manual deployment.
