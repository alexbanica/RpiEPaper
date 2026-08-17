# Domain-Only Unit Tests Implementation Plan

Status: Approved

## Specification

- `docs/specs/SPEC-domain-only-unit-tests.md`

## Affected Files

- `AGENTS.md`
- `tests/test_command_line_controller.py` (deleted)
- `tests/test_github_workflows.py` (deleted)
- `tests/test_package_artifacts.py` (deleted)
- `tests/test_publish_forgejo.py` (deleted)
- `tests/test_release_version.py` (deleted)
- `tests/test_yaml_config_parser.py` (deleted)
- `docs/specs/SPEC-domain-only-unit-tests.md`
- `docs/plans/PLAN-domain-only-unit-tests.md`

## Implementation Performed

1. Inspected the clean invoking checkout, repository guidance, current tests,
   workflow files, and package scripts without creating a linked worktree.
2. Classified `tests/test_docker_status_entity.py` as the only domain-scoped
   test and all other test modules as non-domain tests.
3. Deleted the GitHub workflow, package/release/publish, presentation-controller,
   and infrastructure-parser test modules.
4. Updated `AGENTS.md` to permit unit tests only under `cluster_monitor/domain`
   and to direct non-domain changes to non-unit validation.
5. Added the completed-work spec and plan.

## Validation Run

- `python3 -m unittest discover -s tests`: passed, 1 test.
- `git diff --check`: passed.
- Structural search for remaining non-domain test imports and workflow/script
  references: no matches.

## Validation Skipped

- `ruff check tests`: skipped because Ruff is not installed in the checkout
  environment.
- Hosted GitHub Actions, package construction/publishing, deployment, and
  hardware/runtime checks: not applicable to this scoped change and not run.

## Review And QA

- Formal QA: skipped as required by the `super-agent` workflow.
- Independent code review: skipped as required by the `super-agent` workflow.

## Documentation

- `AGENTS.md` now defines the domain-only test boundary and validation guidance.
- This plan and its matching spec record the directly completed change.

## Delivery State

- Staging: all accepted in-scope changes are staged by the final reconciliation.
- Commit: not created; the user did not request a commit.
- Push: not performed; the user did not request a push.
- Worktree: the invoking checkout was used; no linked worktree was created or
  entered, so attachment and artifact cleanup are not applicable.

## Residual Risk

- Removed non-domain behavior no longer has automated unit-test regression
  coverage. Future validation depends on the static, syntax, structural, or
  operator checks selected for each non-domain change.
- Ruff validation remains unverified in this environment.
