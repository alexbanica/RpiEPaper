# Package Artifact Relative Output Path

Status: Approved

## Purpose

Ensure the release artifact builder writes and validates artifacts in the same
directory when invoked with its default relative `dist` output path.

## Requested Behavior

- Fix the GitHub Actions release build that reports an empty artifact set after
  successfully invoking the package build commands.
- Preserve accepted stable and beta release tags, including `1.0.0-beta1`.

## Scope

- `scripts/package_artifacts.py` output-directory handling.
- Completed-work specification and implementation-plan records.

## Out Of Scope

- GitHub Actions workflow changes.
- Package metadata, artifact names, platform targets, release-tag grammar, or
  publishing behavior.
- Unit tests for package scripts, which are prohibited by `AGENTS.md`.

## Definitions And Constraints

- The builder creates a temporary source-tree copy and executes `setup.py` from
  that copy.
- A relative output path is interpreted relative to the subprocess working
  directory; validation must instead inspect that same physical directory.
- The default `dist` path must remain supported.

## Delivered Behavior

- `_build` resolves `output_dir` to an absolute path before clearing it,
  invoking temporary-source build subprocesses, and validating artifacts.
- The default relative `dist` output now points to one directory throughout the
  build lifecycle.
- `1.0.0-beta1` builds the expected sdist and ARMv7/AArch64 wheels with the
  canonical package version `1.0.0b1`.

## Assumptions And Impact

- Absolute output paths retain their existing behavior.
- The existing Setuptools `setup.py install` deprecation warnings do not change
  the build result and are outside this fix.

## Validation Performed

- In an isolated temporary checkout, completed within 10 seconds:
  `python3 -m scripts.package_artifacts --release-tag 1.0.0-beta1`.
- The command produced exactly:
  `cluster_monitor-1.0.0b1.tar.gz`,
  `cluster_monitor-1.0.0b1-py3-none-linux_armv7l.whl`, and
  `cluster_monitor-1.0.0b1-py3-none-linux_aarch64.whl`.
- Python syntax compilation and `git diff --check` were run after the change.

## Validation Skipped

- Hosted GitHub Actions, Forgejo publication, package installation on target
  platforms, deployment, and hardware/runtime checks were not run.
- Formal QA and independent code review were skipped by the `super-agent`
  workflow.

## Documentation Changes

- Added this completed-work specification and its matching implementation plan.
