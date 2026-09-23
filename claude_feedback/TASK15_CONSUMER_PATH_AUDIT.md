# Task 15 — v0.1.0 consumer/package path audit

Status: review complete; no tag, release or publication performed.

Only demonstrated defects or ambiguities are recorded below.

## 1. Built-artifact smoke is not offline/no-index

Demonstrated in `scripts/release-artifact-smoke.sh`:

- the script first runs `python -m pip install 'build>=1,<2'`;
- it then creates a fresh venv and installs the built Runner MCP wheel with ordinary `pip install "$DIST_DIR"/runner_mcp-*.whl`;
- that fresh install is allowed to resolve/download Runner MCP runtime dependencies from the configured package index.

Therefore the current CI label/expectation “built release artifact” proves that the wheel can be installed in a network-capable clean venv, but it does **not** prove an offline or `--no-index` consumer install. The release notes currently require a “clean install from the built wheel with CLI smoke checks”, which the script does prove; any stronger claim that the artifact smoke is offline/no-index would be inaccurate.

Recommended correction: either (a) keep the release claim explicitly network-capable and stop calling this an offline/no-index proof, or (b) add a separate wheelhouse/bootstrap fixture containing the exact runtime dependencies and run the install with `--no-index --find-links ...`. Do not make the public package appear self-contained when it is not.

## 2. Quickstart's install path is source-tree installation, not package-consumer installation

README and `QUICKSTART.md` tell a new user to clone the repository and run `./install.sh`. `install.sh` creates a venv and executes:

`pip install "$ROOT_DIR"`

That is coherent for the GitHub/source distribution path, but it means the primary “I just want to use it” journey is not a registry/wheel consumer journey. This is not a functional defect for v0.1.0 while publication is intentionally separate, but the distinction should remain explicit in launch/release wording: the documented install method requires a Git clone and local source tree.

Do not add a `pip install runner-mcp` instruction until an actual registry publication exists and has been explicitly authorized.

## 3. README wording overstates current self-update gating after Task 11

README currently describes:

“commit-pinned self-update for the canonical Runner MCP project, gated by fixed lint/unit validation and internal self-reexec”

Task 11 added an earlier exact compatibility-contract preflight. This is not unsafe wording, but it is now incomplete in a security-relevant way: dependency/build/interpreter drift is refused before normal validation/package mutation.

Recommended documentation-only correction before release: mention that self-update is also gated by an unchanged compatibility contract and dependency-contract changes require local bootstrap/manual upgrade. Keep the detailed explanation in `docs/SELF_UPDATE_COMPATIBILITY.md`.

## 4. Compatibility design document still calls its preflight a recommendation

`docs/SELF_UPDATE_COMPATIBILITY.md` says “Recommended fail-closed preflight” and describes adding the compatibility record in future tense. Task 11 has now implemented that exact conservative preflight.

This is demonstrated documentation drift. Before release, update the document to distinguish:
- implemented v0.1.0 behavior: exact canonical contract comparison and bounded refusal;
- possible future relaxation: trusted local installed-distribution checks for changed-but-satisfied constraints.

Leaving it as future design makes operators unsure whether dependency-changing self-updates are actually blocked.

## 5. First-install/bootstrap provenance remains source-dependent

`install.sh` resolves dependencies normally from pip while installing the local source tree. That is expected for the bootstrap/manual path and consistent with the compatibility boundary. The self-update path's `--no-index --no-deps` behavior must not be generalized to first install.

The release notes already say dependency/build/interpreter contract changes require local bootstrap/manual upgrade. Preserve that distinction. A future “offline installation” claim would require a separately supplied/verifiable dependency wheelhouse; it is not established by the current package.

## No demonstrated defect in these checked areas

- `pyproject.toml` consistently requires Python >=3.12 and declares the `runner-mcp` entry point.
- README and Quickstart both state Linux/self-hosted expectations consistently with the package classifier.
- `install.sh` explicitly verifies Python >=3.12 before creating the install venv.
- the five-minute demo uses `venv --copies` consistently with Runner MCP's deliberate rejection of symlink executables for predefined project-local profiles.
- release notes correctly retain the private-host live-recovery limitation and do not claim the current candidate has completed that proof.
- no publication instruction was added and no tag/release is warranted by this review alone.

## Smallest follow-up

One documentation/script-evidence task should:
1. update `docs/SELF_UPDATE_COMPATIBILITY.md` from future recommendation to implemented-state wording;
2. add one concise README compatibility-gate sentence/link;
3. explicitly describe the current release-artifact smoke as a clean network-capable dependency-resolving wheel install, unless a true offline wheelhouse test is deliberately added.

Do not publish, tag, change dependencies or broaden self-update behavior as part of that follow-up.
