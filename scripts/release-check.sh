#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${RUNNER_MCP_RELEASE_PYTHON:-python}"
RUFF_BIN="${RUNNER_MCP_RELEASE_RUFF:-ruff}"
PYTEST_BIN="${RUNNER_MCP_RELEASE_PYTEST:-pytest}"
BASE_REF="${RUNNER_MCP_RELEASE_BASE:-origin/main}"

cd "$ROOT_DIR"

run_step() {
  local label="$1"
  shift
  printf '\n==> %s\n' "$label"
  "$@"
}

run_step "Compile Python" "$PYTHON_BIN" -m compileall -q src tests
run_step "Ruff" "$RUFF_BIN" check .
run_step "Pytest" "$PYTEST_BIN" -q

printf '\n==> Whitespace\n'
BASE_COMMIT="$(git merge-base HEAD "$BASE_REF")"
git diff --check "$BASE_COMMIT"..HEAD
git diff --check
git diff --cached --check

run_step "Built release artifact" bash scripts/release-artifact-smoke.sh
run_step "Clean five-minute demo" bash scripts/demo-smoke.sh

printf '\nLocal release checks passed. GitHub CI remains authoritative for release readiness.\n'
