# Release-candidate hygiene dry run — 2026-09-22

This is a pre-release review only. It does not create a tag, release or externally published artifact.

Reviewed baseline: `main` at `69e604935bfe0fef0dd61b48dfdde76fed8f46ba`, after Tasks 6 and 7. At the start of this dry run there were no open pull requests.

## Baseline checks

- Package metadata is internally aligned for the intended first alpha: package version `0.1.0`, Python `>=3.12`, MIT license metadata, public repository/documentation URLs and the `runner-mcp` console entry point.
- The latest Task 7 PR validation was green across compile/Ruff/pytest/whitespace, built release artifact and clean five-minute demo. The exact final release commit still requires its own green public CI.
- README and the canonical bridge documentation now include the implemented bounded `runtime_doctor` action.
- The public bridge document names every current protocol-v1 `BridgeAction`.
- The audited public operator documentation contained no unknown top-level `runner-mcp` command examples.
- The stale pre-tag exact pytest count was removed from the release-notes draft; exact counts belong only in dated release evidence.
- A targeted hygiene scan of the highest-risk public docs, handover files and example configuration found no non-example IP literal, private-key marker, token-shaped credential or non-placeholder absolute host path.
- The built-artifact smoke test validates wheel/sdist contents and a clean wheel installation; the clean demo validates the documented local onboarding path.
- The self-update dependency/bootstrap boundary is now explicit in `docs/SELF_UPDATE_COMPATIBILITY.md` and linked from the release checklist.

## Blocking

No public-repository code/package blocker was identified in this dry run.

A newly discovered failing CI result, privacy leak or release-artifact failure on the exact candidate commit would immediately become blocking and must not be waived.

## Required before tag

1. Finalize `CHANGELOG.md` for `0.1.0`: move the release content out of `Unreleased` into a dated version section without losing the security and known-limitation notes.

2. Reconcile `docs/RELEASE_NOTES_0.1.0.md` with the current feature set. The draft predates the completed self-update hardening and should explicitly cover:
   - canonical-main-only self-update;
   - recoverable activation markers;
   - staged target/baseline wheels and durable install transactions;
   - local-only `self-update-recovery`;
   - bounded `runtime_status`/`runtime_doctor` visibility;
   - the dependency/bootstrap caveat from `docs/SELF_UPDATE_COMPATIBILITY.md`.

3. Validate the exact intended tag commit on `main`. Compile, Ruff, pytest, whitespace, built-artifact smoke and clean-demo smoke must all be green on that exact commit. `scripts/release-check.sh` is a useful local fail-fast check but does not replace GitHub CI.

4. Repeat public-repository hygiene review on the exact release diff/commit. The current targeted scan and artifact checks are clean, but the release checklist correctly requires the final review to be tied to the candidate being tagged.

5. Keep dependency changes out of the no-dependency self-update path. Any host whose installed baseline predates the current Python/build/runtime dependency contract must use the normal dependency-resolving bootstrap path before relying on `--no-deps` self-update.

6. Reconcile the remaining private-host self-update proof before making a release claim that the full live recovery path is proven. The roadmap still calls for bootstrap of the newest recovery-capable baseline and live proof of same-commit/no-op, forward update, activation retry and interrupted package-install recovery. This dry run did not re-probe the private runtime, so older degraded/recovery-attention observations remain historical rather than current evidence. If that live proof is not completed before the tag, the release notes must state that limitation rather than imply it has been proven.

## Optional follow-up

- Implement the fail-closed dependency compatibility marker/preflight proposed in `docs/SELF_UPDATE_COMPATIBILITY.md`. Until then, dependency/build/interpreter contract changes remain bootstrap events.
- Integrate the safe diagnostics contract into production watcher/supervisor logging when that can be done without widening output.
- Continue guided private-tunnel/TLS onboarding, stronger isolation for untrusted public-fork code, database restore/PITR work and automated retention pruning as separately scoped work.
- Repository description/topics, ecosystem submission and community posts remain broader-launch actions after the tagged alpha; they are not reasons to weaken the release gate.

## Release decision boundary

The repository is close to a taggable first alpha, but the tag should wait for the required-before-tag items above. No release action is authorized by this document.
