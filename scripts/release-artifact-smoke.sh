#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
TMP_ROOT="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

cd "$ROOT_DIR"
rm -rf "$DIST_DIR"

python -m pip install --disable-pip-version-check 'build>=1,<2'
python -m build --sdist --wheel

python - <<'PY'
from __future__ import annotations

import re
import tarfile
import tomllib
import zipfile
from pathlib import Path

root = Path.cwd()
dist = root / "dist"
with (root / "pyproject.toml").open("rb") as handle:
    version = tomllib.load(handle)["project"]["version"]

wheel = dist / f"runner_mcp-{version}-py3-none-any.whl"
sdist = dist / f"runner_mcp-{version}.tar.gz"
if not wheel.is_file() or not sdist.is_file():
    raise SystemExit("expected wheel/sdist names were not produced")

blocked_patterns = [
    re.compile(r"(^|/)\.env($|[./])", re.IGNORECASE),
    re.compile(r"(^|/)(?:id_rsa|id_ed25519)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(^|/).+\.(?:pem|key|p12|pfx)$", re.IGNORECASE),
    re.compile(r"github-mailbox-(?:cursor|replay)\.json$", re.IGNORECASE),
    re.compile(r"completion-notifier-(?:bootstrap|deliveries)\.json$", re.IGNORECASE),
    re.compile(r"(^|/)(?:database-backups|deployment-jobs|test-jobs)(/|$)", re.IGNORECASE),
]
blocked_roots = {
    ".git",
    ".github-runner",
    ".ssh",
}


def validate_members(label: str, members: list[str]) -> None:
    if not members:
        raise SystemExit(f"{label} is empty")
    for raw in members:
        name = raw.replace("\\", "/")
        parts = [part for part in name.split("/") if part]
        if any(part in blocked_roots for part in parts):
            raise SystemExit(f"{label} contains forbidden private/runtime path shape")
        if any(pattern.search(name) for pattern in blocked_patterns):
            raise SystemExit(f"{label} contains forbidden private/runtime artifact")

    if not any("runner_mcp/" in name.replace("\\", "/") for name in members):
        raise SystemExit(f"{label} does not contain the runner_mcp package")


with zipfile.ZipFile(wheel) as archive:
    wheel_members = archive.namelist()
validate_members("wheel", wheel_members)

with tarfile.open(sdist, "r:gz") as archive:
    sdist_members = archive.getnames()
validate_members("sdist", sdist_members)

print(f"release artifacts validated for runner-mcp {version}")
PY

python -m venv "$TMP_ROOT/venv"
"$TMP_ROOT/venv/bin/python" -m pip install --disable-pip-version-check "$DIST_DIR"/runner_mcp-*.whl
VERSION_OUTPUT="$("$TMP_ROOT/venv/bin/runner-mcp" --version)"
HELP_OUTPUT="$("$TMP_ROOT/venv/bin/runner-mcp" --help)"

case "$VERSION_OUTPUT" in
  "runner-mcp "*) ;;
  *)
    echo "installed wheel returned unexpected version output" >&2
    exit 1
    ;;
esac

grep -q "github-watcher" <<<"$HELP_OUTPUT"
grep -q "completion-watcher" <<<"$HELP_OUTPUT"
grep -q "autostart" <<<"$HELP_OUTPUT"
grep -q "emergency-stop" <<<"$HELP_OUTPUT"

echo "Runner MCP built-artifact install smoke test passed."
