# Forgejo install dependency resolution plan

Status: Approved

## Spec reference

`specs/SPEC-forgejo-install-dependency-resolution.md`

## Affected files

- `README.md`
- `.github/workflows/publish.yml`
- `scripts/publish_forgejo.py`
- `specs/SPEC-forgejo-install-dependency-resolution.md`
- `specs/PLAN-forgejo-install-dependency-resolution.md`

## Implementation performed

1. Added public PyPI as the documented extra dependency index while retaining
   Forgejo as the project package index.
2. Added a credential-free, no-cache dependency-resolving installation of the
   exact published version to the publisher's post-upload checks.
3. Required the dependency-resolving installation to contain package metadata
   for the exact requested version.
4. Preserved the existing dependency-free ARMv7 and AArch64 wheel checks and
   bundled-native-library validation.
5. Exposed the dependency index as an optional publisher CLI setting with the
   public PyPI simple index as its default.
6. Configured that dependency index explicitly in the publishing workflow.
7. Recorded the delivered behavior in this approved spec and plan.

## Validation run

- Bytecode-free Python compilation of `scripts/publish_forgejo.py`.
- YAML parsing of `.github/workflows/publish.yml`.
- Static inspection of workflow invocation and pip command options.
- `git diff --check`.

## Validation skipped

- Live Forgejo/PyPI installation, hosted Actions, publication, and ARM hardware
  runtime behavior.
- Ruff because it is not installed in the current environment.
- Automated tests because publishing code is outside the repository's allowed
  domain-only test scope.

## QA and code review

QA and code review were skipped as required by `$super-agent`.

## Documentation updates

The README's stable and beta install examples and post-publish verification
description now explain the dependency-index behavior.

## Staging and delivery status

All accepted in-scope paths are included in the delivery commit and pushed to
`origin/main` as subsequently requested by the user.

## Residual risk

Live index availability, source-distribution installation, dependency
compatibility, hosted workflow behavior, and native ARM runtime behavior remain
unverified until the release path runs against Forgejo and public PyPI.
