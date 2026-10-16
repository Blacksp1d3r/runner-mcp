"""Catch accidental removal/renaming of registered MCP tools from the current universal source.

Static source inventory, not a claim about old customer wheels or actually
enabled authenticated tool lists. Adding a new tool remains compatible.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/runner_mcp/server.py"
FIXTURE = ROOT / "tests/fixtures/source_tool_name_inventory_v0124.json"


def _tool_decorator(call: ast.expr) -> bool:
    return (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "mcp"
        and call.func.attr == "tool"
    )


def _registered_source_tool_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if any(_tool_decorator(d) for d in node.decorator_list):
                names.add(node.name)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Call)
            and _tool_decorator(node.func)
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            names.add(node.args[0].id)
    return names


def test_complete_existing_source_tool_names_remain_registered():
    frozen = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert frozen["schema_version"] == "runner-mcp/source-tool-name-inventory/v1"
    names = frozen["tool_names"]
    assert len(names) >= 90
    assert names == sorted(set(names))
    actual = _registered_source_tool_names(SOURCE.read_text(encoding="utf-8"))
    missing = set(names) - actual
    assert not missing, f"registered existing tools missing: {sorted(missing)}"


def test_removing_a_decorated_legacy_registration_is_detected():
    source = SOURCE.read_text(encoding="utf-8")
    candidate = source.replace(
        "@mcp.tool()\n    def runtime_status(",
        "    def runtime_status(",
        1,
    )
    assert candidate != source
    names = _registered_source_tool_names(candidate)
    assert "runtime_status" not in names


def test_removing_explicit_conditional_legacy_registration_is_detected():
    source = SOURCE.read_text(encoding="utf-8")
    candidate = source.replace(
        "mcp.tool()(build_identity)",
        "unused_local_identity_reference = build_identity",
        1,
    )
    assert candidate != source
    names = _registered_source_tool_names(candidate)
    assert "build_identity" not in names


def test_new_tool_names_are_allowed_without_replacing_old_names():
    actual = _registered_source_tool_names(SOURCE.read_text(encoding="utf-8"))
    actual.add("future_read_only_tool")
    frozen = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(frozen["tool_names"]).issubset(actual)
