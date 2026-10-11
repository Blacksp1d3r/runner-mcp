"""Trusted local-branch release version allocator (no deploy, credentials or network)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_SHA = re.compile(r"^[0-9a-f]{40}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_VERSION_FILES = (
    Path("pyproject.toml"),
    Path("server.json"),
    Path("src/runner_mcp/__init__.py"),
    Path("glama.json"),
)


class VersionAllocationError(ValueError):
    """Stale local branch or incomplete metadata; no release is authorized."""


def version_parts(text: str) -> tuple[int, int, int]:
    if not isinstance(text, str) or not _VERSION.fullmatch(text):
        raise VersionAllocationError("expected a numeric version major.minor.patch")
    return tuple(map(int, text.split(".")))


def next_version(current: str, kind: str) -> str:
    major, minor, patch = version_parts(current)
    if kind == "patch":
        patch += 1
    elif kind == "minor":
        minor += 1
        patch = 0
    elif kind == "major":
        major += 1
        minor = patch = 0
    else:
        raise VersionAllocationError("unknown release increment kind")
    return f"{major}.{minor}.{patch}"


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], capture_output=True, text=True, check=False
    )
    if process.returncode:
        raise VersionAllocationError("local repository state is unavailable")
    return process.stdout.strip()


def plan(
    *,
    root: Path,
    kind: str,
    expected_version: str,
    expected_head: str,
) -> tuple[str, dict[Path, bytes]]:
    """Validate complete local state *before* returning any planned mutations."""

    if not _SHA.fullmatch(expected_head):
        raise VersionAllocationError("expected HEAD SHA is not immutable")
    if _git("-C", str(root), "rev-parse", "HEAD") != expected_head:
        raise VersionAllocationError("branch HEAD changed: rebase and revalidate")
    if _git("-C", str(root), "status", "--porcelain", "--untracked-files=no"):
        raise VersionAllocationError("working tree has uncommitted tracked changes")
    if not root.is_dir() or root.is_symlink():
        raise VersionAllocationError("repository root is missing or unsafe")
    root_real = root.resolve()
    for relative_path in _VERSION_FILES:
        candidate = root / relative_path
        if candidate.is_symlink() or not candidate.is_file():
            raise VersionAllocationError("release metadata path is missing or unsafe")
        if not candidate.resolve().is_relative_to(root_real):
            raise VersionAllocationError("release metadata path escapes repository")
    current = tomllib.loads((root / _VERSION_FILES[0]).read_text())["project"]["version"]
    if current != expected_version:
        raise VersionAllocationError("source version has changed; do not reuse claim")
    version_parts(current)
    server = json.loads((root / _VERSION_FILES[1]).read_text())
    module = (root / _VERSION_FILES[2]).read_text()
    glama = json.loads((root / _VERSION_FILES[3]).read_text())
    if (
        not isinstance(server, dict)
        or server.get("version") != current
        or not isinstance(server.get("packages"), list)
        or not server["packages"]
        or any(
            not isinstance(pkg, dict) or pkg.get("version") != current
            for pkg in server["packages"]
        )
        or not isinstance(glama, dict) or glama.get("version") != current
        or module.count(f'__version__ = "{current}"') != 1
    ):
        raise VersionAllocationError("release metadata is inconsistent")
    proposed = next_version(current, kind)
    pkg = (root / _VERSION_FILES[0]).read_text()
    before = f'version = "{current}"'
    after = f'version = "{proposed}"'
    if pkg.count(before) != 1:
        raise VersionAllocationError("project version is ambiguous")
    server["version"] = proposed
    for package in server["packages"]:
        package["version"] = proposed
    glama["version"] = proposed
    result = {
        _VERSION_FILES[0]: pkg.replace(before, after, 1).encode(),
        _VERSION_FILES[1]: (json.dumps(server, indent=2) + "\n").encode(),
        _VERSION_FILES[2]: module.replace(
            f'__version__ = "{current}"',
            f'__version__ = "{proposed}"', 1
        ).encode(),
        _VERSION_FILES[3]: (json.dumps(glama, indent=2) + "\n").encode(),
    }
    return proposed, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["patch", "minor", "major"], required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        proposed, updates = plan(
            root=Path.cwd(),
            kind=args.kind,
            expected_version=args.expected_version,
            expected_head=args.expected_head,
        )
        if args.apply:
            # All files are validated and rendered before the first write.
            # A crash during the four replace operations must be rejected
            # by the separate CI sync gate; never report it as a release.
            for path, content in updates.items():
                path.write_bytes(content)
        print(
            f"RELEASE_VERSION_ALLOCATION: {'APPLIED' if args.apply else 'DRY_RUN'} "
            f"{args.expected_version} -> {proposed}"
        )
        return 0
    except (VersionAllocationError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"RELEASE_VERSION_ALLOCATION: REFUSED ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
