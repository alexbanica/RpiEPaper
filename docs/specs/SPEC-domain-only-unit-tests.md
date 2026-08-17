# Domain-Only Unit Tests

Status: Approved

## Purpose

Keep the repository's unit-test suite focused exclusively on domain logic and
remove tests that treat delivery tooling or non-domain adapters as unit-test
subjects.

## Requested Behavior

- Remove tests for GitHub Actions workflows and Python package/release/publish
  scripts.
- Limit current and future unit tests to logic under `cluster_monitor/domain`.
- Record the test boundary in `AGENTS.md` so future work does not create test
  units or test-focused subagent assignments for non-domain changes.

## Scope

- Repository testing guidance in `AGENTS.md`.
- Tests for GitHub Actions, package scripts, application/presentation
  coordination, and infrastructure parsing.
- The remaining domain entity test.

## Out Of Scope

- Changes to production code, GitHub Actions workflows, package scripts, package
  metadata, or dependency files.
- Changes to the behavior of the remaining domain test.
- Hosted CI, package builds, publishing, deployment, or hardware/runtime checks.

## Definitions And Constraints

- Domain logic means code under `cluster_monitor/domain`.
- Tests for code outside that directory are non-domain tests, even when the code
  coordinates or mutates domain entities.
- Non-domain changes use suitable static, syntax, structural, or operator checks
  rather than unit-test modules.

## Delivered Behavior

- `tests/test_docker_status_entity.py` is the only remaining test module and
  exercises a domain entity.
- GitHub workflow and package-script tests were removed.
- Presentation-controller and infrastructure-parser tests were also removed so
  the suite consistently follows the domain-only rule.
- `AGENTS.md` prohibits new unit tests outside `cluster_monitor/domain` and
  limits test-first work units and test-focused subagents to testable domain
  changes.
- This spec supersedes prior requirements to unit-test GitHub Actions or package
  scripts, including those in `docs/specs/SPEC-forgejo-python-package-publishing.md`.

## Assumptions And Impact

- The instruction that unit tests should cover only domain logic applies to all
  existing and future tests, not only the four recently added release tests.
- CI may continue to run unit-test discovery; it now discovers only domain
  tests.
- GitHub Actions and packaging behavior no longer has unit-test regression
  coverage by explicit repository policy.

## Validation Performed

- `python3 -m unittest discover -s tests` passed: 1 test.
- `git diff --check` passed.
- A structural search found no remaining test imports from application,
  infrastructure, presentation, or `scripts`, and no workflow references.

## Validation Skipped

- Ruff was unavailable in the checkout environment.
- Hosted GitHub Actions, package builds, release/publish scripts, deployments,
  and hardware/runtime checks were outside this documentation-and-test-removal
  change.
- Formal QA and independent code review were skipped by the `super-agent`
  workflow.

## Documentation Changes

- Added the domain-only unit-test policy to `AGENTS.md`.
- Added this completed-work specification and its matching implementation plan.
