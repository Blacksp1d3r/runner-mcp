"""Statically attest the exact registered tool catalogue in source and wheel.

This proof checks declarations only. Actual client exposure/route/ACK is separate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import zipfile
from pathlib import Path

BASELINE = Path("docs/operations/TOOL_CATALOGUE_BASELINE.json")
SOURCE = Path("src/runner_mcp/server.py")
WHEEL_MEMBER = "runner_mcp/server.py"


class CatalogueError(ValueError):
    """Catalogue is missing, ambiguous or does not match the approved source."""


def _is_mcp_tool_factory(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tool"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mcp"
    )


def registered_tool_names(content: bytes) -> list[str]:
    """Count both @mcp.tool() and mcp.tool()(function) registrations.

    Only static local function names are accepted; no source is executed.
    """
    tree = ast.parse(content.decode("utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if not _is_mcp_tool_factory(decorator):
                    continue
                if decorator.args or decorator.keywords:
                    raise CatalogueError("nonliteral MCP decorator requires review")
                names.append(node.name)
        if isinstance(node, ast.Call) and _is_mcp_tool_factory(node.func):
            if (
                node.func.args
                or node.func.keywords
                or len(node.args) != 1
                or node.keywords
                or not isinstance(node.args[0], ast.Name)
            ):
                raise CatalogueError("nonliteral MCP manual registration requires review")
            target = node.args[0].id
            if target not in defined:
                raise CatalogueError("manual registration target is not defined locally")
            names.append(target)
    if len(names) != len(set(names)):
        raise CatalogueError("duplicate MCP tool name")
    if not names:
        raise CatalogueError("no MCP tools registered")
    return sorted(names)


def verify_baseline(names: list[str], baseline: dict) -> None:
    if baseline.get("schemaVersion") != "runner-mcp/tool-catalogue-baseline/v1":
        raise CatalogueError("unknown baseline schema")
    if baseline.get("sourceFile") != str(SOURCE):
        raise CatalogueError("wrong source reference")
    expected = baseline.get("tools")
    minimum = baseline.get("minimumToolCount")
    if (
        not isinstance(expected, list)
        or not all(isinstance(x, str) for x in expected)
        or len(set(expected)) != len(expected)
        or expected != sorted(expected)
        or not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or minimum < 95
    ):
        raise CatalogueError("invalid baseline")
    if len(names) < minimum or names != expected:
        raise CatalogueError("source tool catalogue diverges from approved baseline")


def tool_receipt(
    *,
    source: bytes,
    manifest: dict,
    wheel_file: Path | None,
) -> dict:
    names = registered_tool_names(source)
    verify_baseline(names, manifest)
    digest = hashlib.sha256(("\n".join(names) + "\n").encode("utf-8")).hexdigest()
    receipt = {
        "schemaVersion": "runner-mcp/tool-catalogue-attestation/v1",
        "toolCount": len(names),
        "toolNamesSha256": digest,
        "toolNames": names,
        "sourceServerPySha256": hashlib.sha256(source).hexdigest(),
        "registeredInSource": True,
        "verifiedInBuiltWheel": wheel_file is not None,
        "clientToolExposureVerified": False,
        "liveServerUpdated": False,
    }
    if wheel_file is not None:
        if wheel_file.is_symlink() or not wheel_file.is_file():
            raise CatalogueError("wheel does not exist or is a symlink")
        with zipfile.ZipFile(wheel_file) as archive:
            members = [member for member in archive.namelist() if member == WHEEL_MEMBER]
            if len(members) != 1:
                raise CatalogueError("wheel server.py member missing or ambiguous")
            wheel_source = archive.read(WHEEL_MEMBER)
        if registered_tool_names(wheel_source) != names:
            raise CatalogueError("built wheel catalogue does not match source")
        if wheel_source != source:
            raise CatalogueError("built wheel server.py is not identical to source")
        receipt["wheelSha256"] = hashlib.sha256(wheel_file.read_bytes()).hexdigest()
        receipt["wheelName"] = wheel_file.name
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(BASELINE.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise CatalogueError("baseline must be an object")
        receipt = tool_receipt(
            source=SOURCE.read_bytes(), manifest=manifest, wheel_file=args.wheel
        )
        if args.output is not None:
            args.output.write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
    except (CatalogueError, OSError, UnicodeError, SyntaxError, ValueError, zipfile.BadZipFile) as exc:
        print(f"TOOL_CATALOGUE_ATTESTATION: FAIL ({type(exc).__name__})", file=sys.stderr)
        return 1
    print(f"TOOL_CATALOGUE_ATTESTATION: PASS registered={receipt['toolCount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
