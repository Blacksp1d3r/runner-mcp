"""Release version gate: fail if shipping changes retain their numeric version."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_RELEASE_FILES = frozenset({"install.sh", "install-operator.sh", "pyproject.toml", "server.json", "glama.json"})
_RELEASE_PREFIXES = ("src/runner_mcp/", "scripts/", ".github/workflows/", ".github/actions/")


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
    version = ".".join(map(str, current))
    runtime_text = Path("src/runner_mcp/__init__.py").read_text(encoding="utf-8")
    if not re.search(
        rf'(?m)^__version__ = "{re.escape(version)}"$',
        runtime_text,
    ):
        raise ValueError("runtime __version__ differs from pyproject")
    glama = json.loads(Path("glama.json").read_text(encoding="utf-8"))
    if not isinstance(glama, dict) or glama.get("version") != version:
        raise ValueError("discovery metadata version differs from pyproject")
    if base is None:
        return current, False
    original = check_metadata(
        git("show", f"{base}:pyproject.toml"),
        git("show", f"{base}:server.json"),
    )
    changed = [
        x.decode("utf-8") for x in git("diff", "--no-renames", "--name-only", "-z", base, "HEAD").split(b"\0")
        if x
    ]
    release = needs_bump(changed)
    if current < original:
        raise ValueError("release version decreased")
    if release and current == original:
        raise ValueError("shipping tools/code changed without a new version")
    if current > original and not {
        "pyproject.toml", "server.json", "src/runner_mcp/__init__.py", "glama.json"
    } <= set(changed):
        raise ValueError("version change must update all four metadata files")
    return current, release


def append_github_output(version: tuple[int, int, int], shipping: bool) -> None:
    """Emit release candidate classification using the same verified path rules."""

    destination = os.environ.get("GITHUB_OUTPUT")
    if not destination:
        raise ValueError("GITHUB_OUTPUT is not available")
    with open(destination, "a", encoding="utf-8") as stream:
        stream.write(f"release={str(shipping).lower()}\n")
        stream.write(f"version={'.'.join(map(str, version))}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git merge-base of this PR against main")
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()
    try:
        version, shipping = verify(args.base)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f"RELEASE_VERSION_GATE: FAIL ({exc})", file=sys.stderr)
        return 1
    if args.github_output:
        try:
            append_github_output(version, shipping)
        except (OSError, ValueError) as exc:
            print(f"RELEASE_VERSION_GATE: FAIL ({exc})", file=sys.stderr)
            return 1
    print(f"RELEASE_VERSION_GATE: PASS {'.'.join(map(str, version))} shipping={shipping}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
