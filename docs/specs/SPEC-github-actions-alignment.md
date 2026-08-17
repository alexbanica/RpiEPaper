# GitHub Actions Alignment

Status: Approved

## Purpose

Align this Python project's automation with the shared workspace conventions
without changing its package contents or Forgejo release implementation.

## Requested Behavior

- Use `.github/workflows/ci.yml` and `.github/workflows/publish.yml`.
- Use the common `CI` and `Publish` workflow names.
- Apply least-privilege permissions, immutable external-action pins,
  non-persisted checkout credentials, dependency caching, and per-workflow/per-ref
  concurrency.
- Keep stable and beta Python release tags supported by the release parser.
- Enable grouped weekly Dependabot updates for GitHub Actions.

## Scope

- GitHub Actions and Dependabot configuration.
- Release-trigger alignment with the existing stable/beta tag contract.
- README automation and credential documentation.
- Completed-work spec and plan artifacts.

## Out Of Scope

- Python application, package artifact, dependency, and runtime behavior.
- Forgejo endpoints, credentials, package contents, target platforms, and
  publisher implementation.
- Central cross-repository reusable workflows.
- Repositories without both Python project metadata and pre-existing GitHub
  Actions workflows.

## Deterministic Behavior Delivered

- CI retains Python 3.12 lint and unit-test jobs for `main` pull requests and
  pushes, and cancels superseded runs for the same workflow/ref.
- Publication retains lint, test, packaging, upload, and anonymous verification
  behavior, runs for supported stable and beta tags, and never cancels a release
  already in progress.
- Checkout is pinned to `v7.0.1`, setup-python to `v7.0.0`, and checkout
  credentials are not persisted.
- Pip cache keys include the dependency files used by the jobs.
- The workflow token has read-only contents permission.
- Dependabot groups GitHub Actions updates on a weekly schedule.

## Assumptions And Impact

- GitHub-hosted runners satisfy the Node 24 runner requirement of the selected
  action releases.
- Exact release-tag validation remains owned by the existing Python release
  helpers; workflow globs are only coarse trigger filters.

## Validation Performed

- Parsed both workflows and Dependabot configuration as YAML.
- Structurally verified triggers, names, permissions, concurrency, immutable
  action pins, checkout credential handling, and pip caching.
- Ran `git diff --check`.

## Validation Skipped

- Hosted GitHub Actions, live Forgejo publication/install, target hardware, and
  the full product test suite were not run.
- Formal QA and independent review were skipped by the `super-agent` workflow.

## Documentation Changes

- Updated README release-trigger, workflow-standard, and secret configuration
  guidance.
