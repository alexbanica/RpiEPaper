# Package Artifact Relative Output Path Implementation Plan

Status: Approved

## Specification

- `docs/specs/SPEC-package-artifact-relative-output.md`

## Affected Files

- `scripts/package_artifacts.py`
- `docs/specs/SPEC-package-artifact-relative-output.md`
- `docs/plans/PLAN-package-artifact-relative-output.md`

## Implementation Performed

1. Confirmed that build subprocesses run from a temporary source-tree copy
   while the default `dist` path remained relative.
2. Resolved the output path at the start of `_build` before any clearing,
   subprocess invocation, or artifact validation.
3. Ran the exact beta release command in an isolated temporary checkout.
4. Added this completed-work spec and plan.

## Validation Run

- `python3 -m scripts.package_artifacts --release-tag 1.0.0-beta1` in an
  isolated temporary checkout: passed in under 10 seconds and produced the
  expected sdist plus ARMv7 and AArch64 wheels at version `1.0.0b1`.
- `python3 -m py_compile scripts/package_artifacts.py`.
- `git diff --check`.

## Validation Skipped

- Hosted GitHub Actions, Forgejo publication, target-platform installation,
  deployment, and hardware/runtime validation were not run.
- Package-script unit tests were not created or run because the repository
  policy limits unit tests to domain logic.

## Review And QA

- Formal QA: skipped as required by the `super-agent` workflow.
- Independent code review: skipped as required by the `super-agent` workflow.

## Documentation

- Added the completed-work specification and plan for the fixed build-path
  behavior.

## Delivery State

- Staging: all accepted in-scope changes are staged by the final reconciliation.
- Commit: not created; the user did not request a commit.
- Push: not performed; the user did not request a push.
- Worktree: the invoking checkout was used; no linked worktree was created or
  entered, so attachment and artifact cleanup are not applicable.

## Residual Risk

- Hosted workflow execution and actual Forgejo publishing remain unverified.
- Setuptools deprecation warnings remain and are outside the relative-path fix.
