#!/usr/bin/env python3
"""Release version gate: fail if shipping changes retain their numeric version."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_RELEASE_FILES = frozenset({"install.sh", "pyproject.toml", "server.json"})
_RELEASE_PREFIXES = ("src/runner_mcp/", "scripts/", ".github/workflows/")


def version_tuple(value: object) -> tuple[int, int, int]:
    if not isinstance(value, str) or not _VERSION_RE.fullmatch(value):
        raise ValueError("release version must be numeric major.minor.patch")
    return tuple(int(x) for x in value.split("."))


def check_metadata(pyproject: bytes, server: bytes) -> tuple[int, int, int]:
    project = tomllib.loads(pyproject.decode("utf-8"))
    registry = json.loads(server)
    version = project["project"]["version"]
    result = version_tuple(version)
    if not isinstance(registry, dict) or registry.get("version") != version:
        raise ValueError("server.json top-level version differs from pyproject")
    packages = registry.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("server.json packages missing")
    if any(not isinstance(x, dict) or x.get("version") != version for x in packages):
        raise ValueError("server.json package version differs from pyproject")
    return result


def needs_bump(paths: list[str]) -> bool:
    return any(x in _RELEASE_FILES or x.startswith(_RELEASE_PREFIXES) for x in paths)


def git(*args: str) -> bytes:
    process = subprocess.run(
        ["git", *args], capture_output=True, check=False
    )
    if process.returncode:
        raise ValueError("Git base comparison is unavailable")
    return process.stdout


def verify(base: str | None) -> tuple[tuple[int, int, int], bool]:
    current = check_metadata(
        Path("pyproject.toml").read_bytes(), Path("server.json").read_bytes()
    )
    if base is None:
        return current, False
    original = check_metadata(
        git("show", f"{base}:pyproject.toml"),
        git("show", f"{base}:server.json"),
    )
    changed = [
        x.decode("utf-8") for x in git("diff", "--name-only", "-z", base, "HEAD").split(b"\0")
        if x
    ]
    release = needs_bump(changed)
    if current < original:
        raise ValueError("release version decreased")
    if release and current == original:
        raise ValueError("shipping tools/code changed without a new version")
    if current > original and not {"pyproject.toml", "server.json"} <= set(changed):
        raise ValueError("version change must update both metadata files")
    return current, release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git merge-base of this PR against main")
    args = parser.parse_args()
    try:
        version, shipping = verify(args.base)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f"RELEASE_VERSION_GATE: FAIL ({exc})", file=sys.stderr)
        return 1
    print(f"RELEASE_VERSION_GATE: PASS {'.'.join(map(str, version))} shipping={shipping}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
