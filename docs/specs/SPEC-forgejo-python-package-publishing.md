# Forgejo Python Package Publishing and GitHub CI

Status: Approved

## Purpose

Provide deterministic GitHub Actions checks for pull requests and changes merged
to `main`, and publish tagged Python package releases to the public Forgejo PyPI
registry.

## Problem

The repository has no hosted CI or release workflow. Its unit tests are only
documented as a local command, no lint contract is configured, and the existing
static package version is not connected to Git release tags. A release workflow
also needs to adapt the repository owner's existing Forgejo npm publishing
contract to Forgejo's PyPI authentication and version rules.

## Scope

- GitHub Actions CI for pull requests targeting `main` and pushes to `main`.
- Deterministic Python lint and unit-test checks.
- GitHub Actions publishing for accepted numeric release tags.
- Release-tag validation and temporary release-version selection.
- Python source and wheel distribution building and validation.
- Packaging the tracked Waveshare runtime shared libraries in every published
  distribution.
- Platform-specific Linux wheels for 32-bit ARM and AArch64 targets.
- Authenticated publication to the public Forgejo PyPI namespace.
- Anonymous post-publication verification.
- Deterministic tests for the workflow and release behavior.
- Maintainer documentation for CI, tagging, credentials, and installation.

## Out Of Scope

- Creating, moving, or deleting Git tags.
- Publishing a package during planning or implementation.
- Creating or changing Forgejo users, organizations, tokens, or instance-wide
  anonymous-access settings.
- Configuring GitHub branch-protection rules through an API.
- Publishing to pypi.org or GitHub Packages.
- Changing application, CLI, monitoring, rendering, or hardware behavior.
- Recompiling, replacing, or changing the behavior of the tracked Waveshare
  shared libraries.
- Publishing an x86, macOS, Windows, or universal wheel.
- Supporting alpha, release-candidate, post-release, development, local, or
  arbitrary prerelease tag forms.

## Definitions

- **Stable release tag:** `MAJOR.MINOR.PATCH`, where every component is zero or
  a positive integer without leading zeroes.
- **Beta release tag:** `MAJOR.MINOR.PATCH-betaN`, where `N` is a positive
  integer without leading zeroes.
- **Tag version:** The exact accepted Git tag, such as `1.2.3-beta4`.
- **Canonical Python version:** The PEP 440 release version placed in package
  metadata. A stable tag is unchanged; `MAJOR.MINOR.PATCH-betaN` becomes
  `MAJOR.MINOR.PATCHbN`.
- **Public Forgejo PyPI repository:**
  `https://forgejo.alexlab.nl/api/packages/public/pypi`.
- **Public Forgejo simple index:**
  `https://forgejo.alexlab.nl/api/packages/public/pypi/simple`.
- **Package identity:** The `pyproject.toml` project name `cluster_monitor`,
  normalized by Python packaging tools to the distribution name
  `cluster-monitor` and artifact prefix `cluster_monitor`.
- **Required Waveshare shared libraries:** The four tracked runtime files
  `waveshare_epd/DEV_Config_32.so`, `waveshare_epd/DEV_Config_64.so`,
  `waveshare_epd/sysfs_gpio.so`, and
  `waveshare_epd/sysfs_software_spi.so` as installed under the packaged
  `waveshare_epd` directory.
- **ARMv7 wheel:** The platform wheel tagged `py3-none-linux_armv7l`.
- **AArch64 wheel:** The platform wheel tagged `py3-none-linux_aarch64`.

## Inputs And Constraints

- The protected integration branch is `main`; this repository has no `master`
  branch.
- Pull-request CI applies to pull requests whose base branch is `main`.
- Merge CI applies to the resulting push to `main`.
- The publish workflow uses the coarse GitHub tag filter
  `[0-9]*.[0-9]*.[0-9]*`; exact validation is mandatory before release work.
- Leading `v`, whitespace, leading zeroes, `beta0`, missing beta numbers,
  dotted prereleases, arbitrary suffixes, and build metadata are rejected.
- The release checkout receives the tag unchanged from `github.ref_name`.
- Release version changes exist only in the checked-out release workspace and
  are not committed back to the repository.
- `pyproject.toml` remains the package metadata authority. The runtime
  `cluster_monitor.__version__` value must match the canonical version embedded
  in the built distribution.
- The Forgejo upload username is supplied by the non-secret GitHub repository
  variable `FORGEJO_PACKAGE_USERNAME`.
- The existing GitHub Actions secret `FORGEJO_PACKAGE_TOKEN` supplies the
  Forgejo password or personal access token.
- Credentials and Twine authentication variables are absent from dependency
  installation, lint, tests, package building, artifact checks, and anonymous
  verification. They are exposed only to the Twine upload process.
- Public dependencies and CI tools are installed from the standard Python
  package index without Forgejo credentials.
- CI tooling versions are reproducibly pinned in the repository's requirements
  flow.
- Ruff checks first-party Python code, tests, and release automation. Vendored
  Waveshare sources under `lib/waveshare_epd` are excluded from the new lint
  contract.
- Unit tests use the repository's established command:
  `python -m unittest discover -s tests`.
- Package metadata must treat the tracked `.so` files as runtime package data.
- The source distribution and both platform wheels contain all four required
  shared libraries. Carrying both architectures in each wheel is intentional:
  the runtime loader selects the compatible library for the active board.
- The ARMv7 and AArch64 wheels must not be labeled as pure or universal.
- Existing tracked shared-library bytes are preserved exactly; packaging must
  not rebuild or transform them.

## Deterministic Behavior

### Pull Requests And Main

1. Every pull request targeting `main` runs named lint and unit-test checks.
2. Every push to `main`, including a pull-request merge commit, runs the same
   named checks.
3. The lint check fails on any Ruff error in its defined first-party scope.
4. The test check runs on Python 3.9 and Python 3.12 and fails if test discovery,
   dependency installation, or any test fails.
5. The workflow exposes stable check names that maintainers can mark as required
   in GitHub branch protection. The workflow does not claim that branch
   protection is configured merely because the checks exist.

### Release Tags

1. A pushed numeric-looking tag starts the publish workflow.
2. Exact validation accepts only stable and beta tags defined by this spec and
   fails before build or authentication for every other form.
3. Stable tags map to the same canonical Python version. Beta tags map from
   `MAJOR.MINOR.PATCH-betaN` to `MAJOR.MINOR.PATCHbN`.
4. Release preparation updates both authoritative build metadata and runtime
   version reporting in the release checkout to the canonical Python version.
5. Lint and the complete unit-test suite must pass in the tag checkout before
   package distributions are built or credentials are exposed.
6. Release outputs are built from a clean artifact directory and contain
   exactly one source distribution, one ARMv7 wheel, and one AArch64 wheel for
   `cluster-monitor` at the canonical version. No universal wheel is produced.
7. All three distributions pass Twine metadata and README validation before
   upload.
8. Artifact inspection verifies the expected name, version, archive filenames,
   wheel platform tags, required first-party Python packages, and all four
   required Waveshare shared libraries before upload.
9. Shared-library inspection requires each archived file's bytes to match the
   corresponding tracked source file. It also verifies that
   `DEV_Config_32.so` is a 32-bit ARM ELF object and the other three files are
   64-bit AArch64 ELF objects.
10. Twine uploads all three validated distributions to the public Forgejo PyPI
   repository using `FORGEJO_PACKAGE_USERNAME` and
   `FORGEJO_PACKAGE_TOKEN` non-interactively.
11. The workflow never deletes or overwrites an existing Forgejo package
    version. An immutable-version conflict fails the release.
12. Concurrent runs for the same Git ref are serialized and are not cancelled
    in progress.
13. After upload, credential-free target-platform installations into temporary
    directories from the public Forgejo simple index must independently resolve
    the ARMv7 and AArch64 wheels at the exact canonical version with dependencies
    disabled.
14. Post-publication verification requires each target-platform installation to
    contain all four byte-identical shared libraries and package metadata at the
    canonical Python version. It imports `cluster_monitor` without loading an
    incompatible native library and requires its runtime version to equal the
    canonical Python version.
15. A publication is successful only after authenticated upload and both
    anonymous target-platform installation verifications succeed.

## Assumptions

- `FORGEJO_PACKAGE_USERNAME` identifies the Forgejo user that owns the supplied
  package-write token; the registry owner remains the `public` namespace.
- The `public` Forgejo owner and instance settings allow anonymous package read
  access. The workflow verifies this rather than attempting to configure it.
- `betaN` starts at `beta1`.
- Python's required normalization of `1.2.3-beta4` to `1.2.3b4` is acceptable
  for published metadata and installation commands.
- Git tag creation is restricted to trusted repository writers.
- `linux_armv7l` and `linux_aarch64` match the supported deployment platforms
  represented by the tracked binary artifacts.
- Static ELF and archive checks plus cross-platform pip installation validate
  package completeness on GitHub's x86 runner. They do not prove that native
  hardware calls succeed on Raspberry Pi, Jetson, or Sunrise X3 devices.

## Regression Impact

- Application behavior and public CLI behavior remain unchanged.
- Existing local unit-test invocation remains valid.
- Pull requests and `main` pushes gain mandatory failing status checks when lint
  or tests do not pass.
- Tag pushes outside the accepted release formats do not publish.
- Beta users install the canonical Python version (for example `1.2.3b4`) even
  though maintainers create the friendlier tag `1.2.3-beta4`.
- Installed ARMv7 and AArch64 packages contain the tracked native files required
  by the Waveshare loader instead of publishing an incomplete universal wheel.
- A package version cannot be republished without deleting it manually in
  Forgejo, which remains outside this workflow.

## Validation Plan

- Deterministic tests for accepted stable and beta tags and all rejected forms.
- Tests for stable and beta tag-to-PEP-440 version mapping.
- Tests proving release-version changes affect only a temporary release
  checkout and keep build/runtime versions aligned.
- Tests for workflow event filters, stable check names, Python versions,
  job dependencies, concurrency, permissions, registry URLs, and credential
  scoping.
- Tests with fake build, Twine, and pip subprocesses covering success, failure,
  artifact mismatch, upload conflict, cleanup, and anonymous verification.
- Tests proving the source distribution and both platform wheels contain all
  four required shared libraries with byte-identical contents.
- Tests for exact ARMv7/AArch64 wheel tags, absence of a universal wheel, and
  expected ELF class/machine headers.
- `python -m unittest discover -s tests`.
- Ruff over its configured first-party scope.
- `python -m compileall cluster_monitor scripts tests`.
- A local clean build of the source distribution and both platform wheels,
  followed by Twine checks, archive inspection, hashes, and target-platform pip
  installation into temporary directories, without publishing.
- `git diff --check`.
- Hosted pull-request and `main` workflow runs.
- A real tag-triggered Forgejo publication and anonymous installation remain
  runtime validation and must not be claimed until an actual release tag passes.

## Documentation Needs

- Document the CI events and exact checks to require in GitHub branch
  protection.
- Document stable and beta tag formats, rejected `v` tags, and beta PEP 440
  normalization.
- Document the fixed public Forgejo PyPI upload and simple-index URLs.
- Document `FORGEJO_PACKAGE_USERNAME` and `FORGEJO_PACKAGE_TOKEN` setup without
  exposing credential values.
- Document authenticated release behavior and credential-free exact-version
  installation examples for stable and beta packages.
- Document the ARMv7 and AArch64 wheel targets and the four included shared
  libraries.
- State that package-content validation does not replace Raspberry Pi/ePaper,
  Jetson, or Sunrise X3 hardware runtime validation.
