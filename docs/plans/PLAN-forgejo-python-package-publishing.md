# Forgejo Python Package Publishing and GitHub CI Implementation Plan

Status: Approved

## Super-Agent Completed Iteration: Remove Python 3.9 GitHub Actions (2026-08-17)

- Requested outcome: remove Python 3.9 from GitHub Actions while preserving the
  package metadata declaration that Python 3.9 and newer are supported.
- Implemented changes: the CI and release test matrices contain only Python
  3.12, workflow contract tests require that Python 3.9 is absent, and the
  branch-protection documentation names only `lint` and `test (3.12)`.
- Test-first applicability: this is a workflow-configuration and documentation
  change; the deterministic workflow contract tests were updated before the
  workflow configuration.
- Validation run: focused workflow contract tests, YAML parsing for both
  workflows, and Git diff checks.
- Validation intentionally skipped by the `$super-agent` workflow: the full
  unit suite, Ruff, package builds, hosted GitHub Actions, formal QA, and
  independent code review.
- Staging status: all accepted iteration paths are staged in the invoking
  checkout. Commit and push were not requested and were not performed.
- Residual risk: Python 3.9 remains package-compatible but no longer receives
  hosted regression coverage; hosted check creation remains unverified until
  the staged change is committed, pushed, and GitHub Actions runs it.

## Approved Spec

`docs/specs/SPEC-forgejo-python-package-publishing.md`

The implementation must match the approved spec. Discovery, product research,
architecture research, and scope expansion are prohibited during `$implement`.
If implementation reveals a missing or conflicting behavior, stop and amend the
approved artifacts before continuing.

## Delivery Branch And Base

- Repository: `RpiEPaper`
- Expected base ref: `origin/main`
- Expected base commit: `f3eb7384e45091816321b8cc0af75585eca0f8e2`
- Delivery branch: `feature/forgejo-python-package-publishing`
- Task slug: `forgejo-python-package-publishing`
- Isolated implementation worktree:
  `~/.herdr/worktrees/RpiEPaper/forgejo-python-package-publishing`

Implementation must use the isolated worktree. The main agent must create
`~/.herdr/worktrees/RpiEPaper` when absent, verify that the repository name and
task slug produce the exact planned path, and create or reuse that worktree in
detached-HEAD state at the expected base before edits. A reused worktree must be
clean, detached, registered to this repository, and at the expected base. Any
base, identity, cleanliness, path, or branch-availability conflict is a stop
condition.

The approved spec and plan currently exist in the invoking checkout rather than
the expected base. After worktree verification, copy only these two approved
artifacts into their exact planned paths in the isolated worktree as accepted
implementation inputs. Do not enter or modify the invoking checkout for task
work.

Do not create the delivery branch until development reaches either DRAFT
delivery or the Definition of Done. At that point, create the exact branch from
the detached worktree, reconcile the complete accepted change set, commit it,
and push it to `origin`.

## Expected Files

- `.github/workflows/ci.yml` — pull-request and `main` lint/test checks.
- `.github/workflows/publish.yml` — numeric-tag release orchestration.
- `scripts/__init__.py` — import boundary for deterministic release tests.
- `scripts/release_version.py` — exact tag validation, PEP 440 mapping, and
  isolated release-tree version preparation.
- `scripts/package_artifacts.py` — sdist and ARMv7/AArch64 wheel construction,
  package-content, platform-tag, ELF, and byte-identity verification.
- `scripts/publish_forgejo.py` — lint/test gating, credential-scoped Twine
  upload, anonymous target-platform pip verification, and cleanup.
- `tests/test_release_version.py` — tag, mapping, isolation, and cleanup tests.
- `tests/test_package_artifacts.py` — sdist/wheel set, native package data,
  platform tags, ELF architecture, hashes, and rejection tests.
- `tests/test_publish_forgejo.py` — authentication, upload, anonymous ARMv7 and
  AArch64 installation verification, failure, and cleanup tests.
- `tests/test_github_workflows.py` — deterministic workflow structure tests.
- `requirements/dev.txt` — pinned CI, lint, build, version, and publishing tools.
- `pyproject.toml` — tracked `.so` package data and package metadata needed by
  the approved release contract.
- `setup.py` — build-only non-pure/platform-wheel tagging hook while
  `pyproject.toml` remains the metadata authority.
- `ruff.toml` — first-party lint scope and vendored-code exclusions.
- `.gitignore` — generated build, distribution, metadata, lint, and test output.
- `README.md` — CI, release, credential, public installation, branch-protection,
  PEP 440 beta mapping, platform-wheel/native-library contents, and hardware
  validation boundaries.
- `docs/specs/SPEC-forgejo-python-package-publishing.md` — approved behavior.
- `docs/plans/PLAN-forgejo-python-package-publishing.md` — approved execution
  contract.

No other production or documentation path is in scope unless an approved
artifact amendment explicitly adds it.

## Test-First Applicability

Tag parsing, version mapping, release-tree isolation, native package data,
platform-wheel construction, ELF/hash verification, publishing orchestration,
credential isolation, target-platform post-publish verification, and workflow
structure are deterministically testable and require test-first units.

Ruff configuration, requirements metadata, ignore rules, and prose documentation
are configuration or documentation changes. Separate test-first production code
is not applicable to those files; they are validated through the completed test
suites, lint, three-artifact package build, workflow-structure tests, and diff
checks.

## Dependency-Aware Work Graph

Every subagent starts in clean context with the approved spec, approved plan,
exact assignment, owned files, relevant existing command/file snippets, and the
instruction that other agents share the codebase. Workers must not revert other
changes and must not create or manage worktrees or branches, commit, push,
research, or expand scope. Each assignment is sized for no more than five
minutes of active work.

| ID | Type | Boundary and owned files | Dependencies | Acceptance criteria and validation | Subagent assignment |
|---|---|---|---|---|---|
| T1 | Test | Tag grammar, PEP 440 mapping, source-tree immutability, isolated release-tree preparation, cleanup. Owns `tests/test_release_version.py`. | None | New tests fail only because release-version production behavior is absent; covers stable, beta, leading `v`, leading zeroes, `beta0`, malformed forms, exact metadata/runtime alignment, unchanged source checkout, and cleanup. Run the owned test module. | `test-writer`, maximum 5 minutes. |
| T2 | Test | Native package data and artifact-set contract. Owns `tests/test_package_artifacts.py`. | None | Tests exactly one sdist plus `linux_armv7l` and `linux_aarch64` wheels, no universal wheel, all four `.so` files in every artifact, exact source-byte hashes, ELF32/ARM for `DEV_Config_32.so`, ELF64/AArch64 for the other three, non-pure wheel metadata, required Python packages, and mismatch rejection. Initially fails for missing behavior. Run the owned test module. | `test-writer`, maximum 5 minutes. |
| T3 | Test | Publish orchestration, safe subprocess environment, Twine upload, public target-platform pip verification, failures, and cleanup. Owns `tests/test_publish_forgejo.py`. | None | Uses temporary fixtures and fake executables; proves the token and Twine username reach only upload, accepts only the validated three-artifact set, rejects conflicts, performs credential-free exact-version ARMv7 and AArch64 installs, validates installed `.so` bytes and runtime version without loading incompatible libraries, and cleans temporary data on success/failure. Initially fails for missing behavior. Run the owned test module. | `test-writer`, maximum 5 minutes. |
| T4 | Test | CI and publishing workflow contract. Owns `tests/test_github_workflows.py`. | None | Tests PR-to-`main`, push-to-`main`, coarse numeric tag filter, stable check names, Python 3.12-only tests, absence of Python 3.9, Ruff gate, publish dependencies, least permissions, concurrency, public endpoints, secret/variable names, upload-only credential scope, and the required three-artifact release command. Initially fails because workflows are absent. Run the owned test module. | `test-writer`, maximum 5 minutes. |
| D1 | Development | Exact release-tag validation, canonical version mapping, temporary release-tree construction, strict version replacement, source immutability, and cleanup. Owns `scripts/__init__.py` and `scripts/release_version.py`. | T1 | T1 passes without weakening assertions; source `pyproject.toml` and `cluster_monitor/__init__.py` remain unchanged; temporary release copies contain aligned canonical versions and are removed reliably. Run T1 plus compile checks for owned files. | `developer`, maximum 5 minutes. |
| D2 | Development | Native package-data configuration and cross-platform artifact builder. Owns `scripts/package_artifacts.py`, `pyproject.toml`, and `setup.py`. | T2, D1 | T2 passes without weakening assertions; metadata includes all tracked `.so` files; build creates exactly one sdist and two non-pure platform wheels with all four byte-identical libraries; tags, WHEEL metadata, ELF headers, hashes, and required contents are checked; `pyproject.toml` remains metadata authority. Run T1/T2, compile checks, and a local three-artifact dry build. | `developer`, maximum 5 minutes. |
| D3 | Development | Release orchestration and Forgejo PyPI publisher. Owns `scripts/publish_forgejo.py`. | T3, D1, D2 | T3 passes; sanitized lint/test/build/check operations receive no credentials; only the validated sdist/ARMv7/AArch64 set is uploaded; only Twine receives username/token; immutable conflicts fail; credential-free platform-targeted installs validate both wheels and installed `.so` bytes/runtime version; errors do not leak credentials; temporary state is cleaned. Run T1-T3 plus compile checks. | `developer`, maximum 5 minutes. |
| D4 | Development | GitHub Actions workflows. Owns `.github/workflows/ci.yml` and `.github/workflows/publish.yml`. | T4 | T4 passes; workflows implement only approved events, checks, Python versions, permissions, concurrency, dependencies, endpoints, credential scope, and three-artifact publishing; tag publishing cannot run until lint/tests/build/content validation succeeds. Run T4 and YAML parsing/structure validation. | `developer`, maximum 5 minutes. |
| D5 | Development | Tooling integration and maintainer contract. Owns `requirements/dev.txt`, `ruff.toml`, `.gitignore`, and `README.md`. | D1, D2, D3, D4 | Pinned tools support the scripts/workflows; Ruff covers first-party code/tests/scripts and excludes vendored Waveshare code; generated artifacts are ignored; README documents exact stable/beta tags, PEP 440 mapping, public endpoints, credentials, required checks, both platform wheels, four included libraries, credential-free target installs, immutable versions, and hardware-runtime validation boundaries. Run lint, all tests, three-artifact build/check/install validation, and diff checks. | `developer`, maximum 5 minutes. |
| R1 | Review | Release versioning, native artifacts, and publisher correctness/security. Reviews D1-D3 and T1-T3 diffs only; changes no files. | D1, D2, D3 | Reports spec/plan mismatches, tag/version bugs, missing/changed `.so` files, incorrect wheel purity/platform tags, ELF/hash errors, credential leakage, command injection, unsafe cleanup, artifact-validation gaps, nondeterminism, and missing tests with file/line evidence. | `code-reviewer`, maximum 5 minutes. |
| R2 | Review | Workflows, tooling, docs, and regression contract. Reviews D4/D5 and T4 diffs plus approved-artifact alignment; changes no files. | D4, D5 | Reports trigger/check/permission/concurrency/dependency errors, secret-scope regressions, unpinned tooling, inaccurate platform/package docs, package-content overclaims, and missing validation with file/line evidence. | `code-reviewer`, maximum 5 minutes. |

## Concurrency And Integration

- Maximum concurrent test-focused subagents: 4 (`T1`, `T2`, `T3`, `T4`).
- Maximum concurrent implementation/developer subagents: 2.
- Maximum concurrent code-review subagents: 2 (`R1`, `R2`).
- `D1` may start immediately after `T1`, while T2-T4 remain active.
- `D2` is serialized after `D1` because artifact construction uses the isolated
  release tree and canonical version prepared by D1.
- `D3` is serialized after `D2` because publishing accepts and verifies D2's
  exact artifact set.
- `D4` may start immediately after `T4` and may run concurrently with D1-D3
  because its workflow ownership does not overlap.
- `D5` runs after D1-D4 so it can integrate final commands, artifact names,
  check names, and platform behavior without concurrent edits to shared
  configuration or documentation.
- The main agent owns copying approved artifacts into the isolated worktree,
  dependency supervision, timeout enforcement, shared integration, review-fix
  routing, QA, staging, commit, and push.

If any assignment reaches five minutes, the main agent must interrupt it,
record completed work, partial work, changed files, validation, blockers, and
remaining work, inspect and preserve usable changes, then split the remainder
into smaller non-overlapping work before assigning a new clean-context agent.
The same-sized timed-out assignment must not be retried.

## Review Finding Resolution

Reviewers do not implement fixes. Each accepted finding must be assigned to a
new clean-context `developer` subagent with the approved artifacts, exact
finding, minimal relevant diff context, and a non-overlapping ownership boundary
sized for no more than five minutes. The main agent reruns the affected focused
tests before final QA. A finding that requires changed behavior or expanded
scope is a stop condition for artifact amendment rather than an implementation
fix.

## Main-Agent QA

The main agent must perform and report final QA; it must not delegate QA.

1. Re-read the approved acceptance behavior against the final diff.
2. Confirm source and test ownership integrations contain no overwritten agent
   work or unrelated changes.
3. Run the pinned Ruff command over `cluster_monitor`, `scripts`, and `tests`.
4. Run `python -m unittest discover -s tests`.
5. Run `python -m compileall cluster_monitor scripts tests` with temporary/cache
   output prevented from polluting the worktree.
6. Run the deterministic workflow structure tests explicitly.
7. Build exactly one sdist, one `py3-none-linux_armv7l` wheel, and one
   `py3-none-linux_aarch64` wheel in a clean temporary-output context; reject a
   `py3-none-any` artifact.
8. Run Twine checks and deterministic archive inspection without credentials or
   publication. Require all four tracked `.so` files in every artifact, compare
   their hashes and bytes with the source files, verify ELF class/machine, and
   verify both wheels are marked non-pure with the expected platform tags.
9. Verify the source checkout remains unchanged after dry-run release tests.
10. Run `git diff --check`.
11. Inspect workflow YAML, permissions, trigger filters, job dependencies,
    concurrency, registry URLs, secret/variable scope, and commands manually.
12. Verify README commands and examples match the implemented interfaces.
13. Use pip's target-platform options and no credentials/dependencies to install
    the locally built ARMv7 and AArch64 wheels into separate temporary targets;
    verify installed native bytes and canonical runtime/package metadata without
    loading incompatible native libraries on the x86 QA host.
14. Confirm no token, credential value, temporary authentication file, build
    artifact, package metadata directory, cache, or virtual environment is
    tracked or left in the worktree.
15. Classify hosted GitHub checks, branch-protection configuration, a real tag
    publish, anonymous Forgejo platform-targeted installations, and native
    hardware runtime validation as unrun unless current evidence proves
    otherwise.

No real tag, GitHub-hosted workflow, Forgejo upload, package deletion, branch
protection mutation, deployment, or Raspberry Pi/ePaper runtime operation is
authorized by implementation validation.

## Documentation

Update `README.md` only for the approved operational contract. It must state:

- PR and `main` event behavior and exact check names to mark required.
- Stable `X.Y.Z` and beta `X.Y.Z-betaN` tag formats with no leading `v`.
- PEP 440 beta normalization and exact stable/beta install examples.
- Public Forgejo PyPI upload and simple-index URLs under owner `public`.
- GitHub variable `FORGEJO_PACKAGE_USERNAME` and secret
  `FORGEJO_PACKAGE_TOKEN` setup.
- Credential isolation, immutable versions, and both anonymous target-platform
  post-publish checks.
- The exact sdist plus ARMv7/AArch64 wheel set, absence of a universal wheel,
  and all four included tracked `.so` files.
- The boundary between static content/platform validation and hosted/live
  release plus native hardware validation.

Do not add HTTP/OpenAPI documentation; the project remains CLI-only.

## Commit And Push

Implementation delivery includes every accepted in-scope change, including the
approved spec and plan. Before committing, the main agent must inspect
`git status`, classify every modified, added, deleted, renamed, and untracked
path, preserve and identify unrelated user changes, and stage only the complete
accepted path set. Inspect both the staged path list and staged diff.

Use one repository-convention commit, defaulting to:

`feature: DRAFT add Forgejo Python package publishing`

Retain `DRAFT` unless hosted PR/`main` checks, branch protection, an actual tag
publication, anonymous Forgejo installation, and relevant package/runtime
validation have all been completed. Create
`feature/forgejo-python-package-publishing` only after reaching DRAFT or the
Definition of Done, commit the complete accepted set, push the branch to
`origin`, configure/verify its upstream, and confirm it is not ahead of the
upstream afterward.

After the commit, inspect `git status` again. Do not report completion while an
accepted in-scope change is unstaged, uncommitted, or unpushed. Report all
preserved unrelated changes explicitly.

## Delivery Classification

Deterministic implementation can reach DRAFT delivery without creating a real
release tag or mutating GitHub/Forgejo configuration. Final delivery requires
all applicable Definition of Done items plus current evidence that hosted
checks, required branch protection, a real stable or beta Forgejo publication,
credential-free installation, and relevant runtime/package behavior passed.

The completion report must state implementation summary, review and QA issues,
resolved findings, validation run/not run, remaining risks, documentation,
commit/push status, DRAFT or final classification, skipped/blocked requirements,
Definition of Done status, and final main-agent acceptance.
