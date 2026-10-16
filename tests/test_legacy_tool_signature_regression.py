"""Regression guard for specifically pinned currently registered tool signatures.

Source AST-only; this does not assert backwards compatibility with uninspected
historical wheels or generated runtime JSON schemas.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BASELINE = BASE / "tests/fixtures/legacy_tool_callable_signatures_v0123.json"
SOURCE = BASE / "src/runner_mcp/server.py"


def _mcp_tool_decorator(dec: ast.expr) -> bool:
    return (
        isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Attribute)
        and isinstance(dec.func.value, ast.Name)
        and dec.func.value.id == "mcp"
        and dec.func.attr == "tool"
    )


def _explicit_tool_registration(tree: ast.AST, name: str) -> bool:
    """Recognize existing mcp.tool()(function_name) syntax."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or len(node.args) != 1:
            continue
        if not isinstance(node.args[0], ast.Name) or node.args[0].id != name:
            continue
        if isinstance(node.func, ast.Call) and _mcp_tool_decorator(node.func):
            return True
    return False


def _tool_function(tree: ast.AST, name: str) -> ast.FunctionDef:
    found = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(found) == 1, f"missing or duplicate baseline tool: {name}"
    definition = found[0]
    assert any(_mcp_tool_decorator(dec) for dec in definition.decorator_list) or (
        _explicit_tool_registration(tree, name)
    ), f"baseline tool no longer explicitly registered: {name}"
    return definition


def _params(definition: ast.FunctionDef) -> list[dict[str, object]]:
    args = definition.args
    assert not args.posonlyargs and not args.vararg and not args.kwarg
    assert not args.kwonlyargs, "legacy keyword-only contract requires explicit baseline update"
    all_args = args.args
    first_optional = len(all_args) - len(args.defaults)
    out = []
    for i, arg in enumerate(all_args):
        assert arg.annotation is not None, f"{definition.name}.{arg.arg} missing type"
        row: dict[str, object] = {
            "name": arg.arg,
            "type": ast.unparse(arg.annotation),
            "required": i < first_optional,
        }
        if i >= first_optional:
            row["default"] = ast.literal_eval(args.defaults[i - first_optional])
        out.append(row)
    return out


def test_registered_legacy_tool_callable_signatures_do_not_drift():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["schema_version"] == "runner-mcp/legacy-signature-baseline/v1"
    assert len(baseline["tools"]) >= 10
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for expected in baseline["tools"]:
        fn = _tool_function(tree, expected["name"])
        assert _params(fn) == expected["params"], expected["name"]
        assert fn.returns is not None
        assert ast.unparse(fn.returns) == expected["return"], expected["name"]


def test_baseline_identifiers_and_signatures_are_unique():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    names = [tool["name"] for tool in baseline["tools"]]
    assert len(names) == len(set(names))
    assert all(isinstance(name, str) and name.isidentifier() for name in names)


def test_guard_rejects_default_and_required_argument_drift():
    source = SOURCE.read_text(encoding="utf-8")
    assert "limit: int = 100" in source
    modified = source.replace("limit: int = 100", "limit: int = 200", 1)
    assert modified != source
    tree = ast.parse(modified)
    fn = _tool_function(tree, "list_backups")
    assert _params(fn) != next(
        item["params"]
        for item in json.loads(BASELINE.read_text(encoding="utf-8"))["tools"]
        if item["name"] == "list_backups"
    )


def test_guard_rejects_unregistered_tool():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = _tool_function(tree, "runtime_status")
    fn.decorator_list.clear()
    # Other registrations must not silently grant this tool the same contract.
    import pytest

    with pytest.raises(AssertionError, match="no longer explicitly registered"):
        _tool_function(tree, "runtime_status")
