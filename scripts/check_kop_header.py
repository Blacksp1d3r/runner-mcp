#!/usr/bin/env python3
# KOP | Eigenaar: Blacksp1d3r | Project: runner-mcp | Programma: kop-header-checker | Aangemaakt in versie: 1.2 | Datum: 2026-11-22 | Doel: Nieuwe geschikte bronbestanden controleren op eigenaarskop
"""Opt-in, dependency-free KOP check. It never edits files or runs host commands."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

COMMENTS = {
    ".py": "# ", ".sh": "# ", ".bash": "# ", ".ps1": "# ",
    ".yml": "# ", ".yaml": "# ", ".toml": "# ",
    ".js": "// ", ".jsx": "// ", ".ts": "// ", ".tsx": "// ",
    ".md": "<!-- ", ".css": "/* ", ".scss": "/* ",
}
SKIP_DIRS = frozenset({
    "node_modules", "vendor", "vendored", "third_party", ".git", "dist",
    "build", "generated", "__generated__", ".venv", "venv", "coverage",
    "archives", "archive", "snapshots", "fixtures",
})
REQUIRED = ("Eigenaar:", "Project:", "Programma:", "Aangemaakt in versie:", "Datum:", "Doel:")
DATE_RE = re.compile(r"\bDatum:\s*\d{4}-\d{2}-\d{2}(?:\b|\s|\|)")
ENCODING_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+")


def relevant(path: str) -> bool:
    parts = Path(path).parts
    return bool(
        parts and not any(part in SKIP_DIRS for part in parts[:-1])
        and parts[-1] != "CHANGELOG.md"
        and Path(path).suffix.lower() in COMMENTS
    )


def first_comment(path: str, source: bytes) -> str | None:
    if not relevant(path) or not source or b"\x00" in source:
        return None
    try:
        lines = source.decode("utf-8-sig").splitlines()
    except UnicodeError:
        return None
    if not lines:
        return None
    index = 1 if lines[0].startswith("#!") else 0
    if path.endswith(".py") and index < len(lines) and ENCODING_RE.match(lines[index]):
        index += 1
    if path.endswith(".md") and index < len(lines) and lines[index].strip() == "---":
        try:
            index = next(i + 1 for i in range(index + 1, len(lines)) if lines[i].strip() == "---")
        except StopIteration:
            return None
    while index < len(lines) and (
        not lines[index].strip()
        or lines[index].lstrip().startswith(("# SPDX-", "// SPDX-"))
    ):
        index += 1
    if index >= len(lines):
        return None
    line = lines[index].lstrip()
    return line if line.startswith(COMMENTS[Path(path).suffix.lower()]) else ""


def validate(path: str, source: bytes) -> str | None:
    line = first_comment(path, source)
    if line is None:
        return None  # intentionally unsupported/empty/binary
    prefix = COMMENTS[Path(path).suffix.lower()] + "KOP | "
    if not line.startswith(prefix):
        return "KOP ontbreekt op eerste toegelaten commentaarregel"
    for field in REQUIRED:
        found = re.search(re.escape(field) + r"\s*([^|]+)", line)
        if not found or found.group(1).strip() in ("", "?", "TODO", "<...>"):
            return "ongeldig of ontbrekend veld " + field
    if DATE_RE.search(line) is None:
        return "Datum mist ISO-formaat YYYY-MM-DD"
    return None


def staged_new() -> list[tuple[str, bytes]]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A", "-z"],
        capture_output=True, check=True,
    )
    found = []
    for raw in result.stdout.split(b"\x00"):
        if not raw:
            continue
        path = raw.decode("utf-8", errors="surrogateescape")
        if relevant(path):
            data = subprocess.run(
                ["git", "show", ":" + path], capture_output=True, check=True,
            ).stdout
            found.append((path, data))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="KOP owner header checker")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--advisory", action="store_true")
    ap.add_argument("files", nargs="*")
    opts = ap.parse_args()
    if not opts.staged and not opts.files:
        ap.error("choose --staged or file paths")
    try:
        items = staged_new() if opts.staged else [
            (p, Path(p).read_bytes()) for p in opts.files
        ]
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"KOP unavailable: {exc}", file=sys.stderr)
        return 2
    failed = [(p, msg) for p, data in items if (msg := validate(p, data))]
    for path, message in failed:
        print(f"KOP {path}: {message}")
    if failed:
        print(f"KOP: {len(failed)} nieuwe bestanden verdienen een header")
        return 1 if opts.strict and not opts.advisory else 0
    print("KOP: PASS (alle nieuwe ondersteunde bestanden)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
