# GitHub Actions Alignment Implementation Plan

Status: Approved

## Specification

- `docs/specs/SPEC-github-actions-alignment.md`

## Affected Files

- `.github/dependabot.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/publish.yml`
- `README.md`
- `docs/specs/SPEC-github-actions-alignment.md`
- `docs/plans/PLAN-github-actions-alignment.md`

## Implementation Performed

1. Standardized workflow names, concurrency, action pins, checkout handling,
   pip caching, step names, and formatting.
2. Added the missing beta-tag trigger already supported by the release parser.
3. Added grouped weekly Dependabot updates for GitHub Actions.
4. Updated README automation and secret guidance.
5. Added this completed-work spec and plan.

## Validation Run

- YAML parsing and shared structural assertions for all aligned repositories.
- `git diff --check`.

## Validation Skipped

- Full tests, hosted Actions, Forgejo publication/install, and hardware/runtime
  checks were skipped because they exceed the `super-agent` validation boundary
  or require external runtime state.

## Review And QA

- Formal QA: skipped as required by `super-agent`.
- Independent code review: skipped as required by `super-agent`.

## Documentation

- README and completed-work artifacts document the delivered conventions.

## Delivery State

- All accepted files are staged after final reconciliation, committed together,
  and pushed to `origin/main` as explicitly requested.
- The invoking checkout is used; no linked worktree or artifact cleanup applies.

## Residual Risk

- Hosted execution and live Forgejo behavior remain unverified.
