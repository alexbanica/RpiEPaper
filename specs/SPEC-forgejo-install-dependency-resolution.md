# Forgejo install dependency resolution

Status: Approved

## Purpose

Ensure the published `cluster-monitor` package can be installed anonymously
from Forgejo together with its public Python dependencies.

## Requested behavior

The public installation command must retrieve `cluster-monitor` from the
Forgejo package index and allow pip to retrieve third-party dependencies absent
from Forgejo from public PyPI. Release verification must exercise that
dependency-resolving path while retaining the existing ARMv7 and AArch64 wheel
checks.

## Scope

- Correct the public Forgejo installation commands in `README.md`.
- Add dependency-resolving post-publication verification to
  `scripts/publish_forgejo.py`.
- Configure the public dependency index explicitly in
  `.github/workflows/publish.yml`.
- Preserve existing platform-wheel installation and packaged-native-library
  verification.

## Out of scope

- Publishing third-party dependencies to Forgejo.
- Changing package dependencies or versions.
- Changing Forgejo credentials, visibility, or upload behavior.
- Changing package artifacts or supported hardware platforms.
- Adding automated tests for publishing code, which the repository test policy
  forbids.

## Inputs and constraints

- Forgejo remains the primary index for `cluster-monitor`.
- Public PyPI is the additional index for dependencies absent from Forgejo.
- Anonymous verification must not receive Forgejo upload credentials or reuse
  pip's cache or local pip configuration.
- The dependency-resolving smoke install runs on the GitHub runner's native
  platform because the published package includes a source distribution but no
  x86 wheel.
- ARMv7 and AArch64 wheels continue to be selected explicitly and installed
  without dependencies so their package contents can be inspected on the x86
  runner.

## Deterministic behavior delivered

The documented stable and beta commands supply both the Forgejo package index
and public PyPI. After upload, the publisher performs a credential-free install
of the exact package version into an isolated target using those indexes and
requires matching installed package metadata. It then performs the unchanged
dependency-free ARMv7 and AArch64 wheel installations and validates their
metadata, runtime version, imports, and bundled Waveshare libraries.

## Assumptions

`cluster-monitor` is published in the configured Forgejo index, while its
third-party dependencies are available from public PyPI. The GitHub-hosted
runner can reach both indexes and can build the published source distribution
for its native dependency-resolution smoke check.

## Impact

Operators no longer receive dependency resolution failures solely because the
Forgejo-only install command replaces pip's public PyPI index. A release fails
post-publication verification when the exact project version or its declared
dependencies cannot be installed.

## Validation performed

- Compiled `scripts/publish_forgejo.py` without writing bytecode.
- Parsed `.github/workflows/publish.yml` as YAML.
- Inspected the publishing workflow invocation and pip option boundaries.
- Ran `git diff --check`.

## Validation skipped

- Live installation from Forgejo and public PyPI.
- Hosted GitHub Actions execution and package publication.
- ARM hardware runtime validation.
- Ruff, because it is not installed in the current environment.
- Automated tests, code review, and QA.

## Documentation changes

`README.md` now documents the Forgejo primary index, public PyPI dependency
index, and the two-stage anonymous verification boundary.
