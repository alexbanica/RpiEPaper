# Release tooling maintenance

Status: Approved

## Authority and identity

- Date: 2026-10-16; group G1; findings M001, M011, M012.
- Origin: the parent maintenance audit and the user's request to create SPEC/PLAN pairs for every group, excluding M002/M004 from SSH.
- Behavior decision: on 2026-10-16 the user said "use recommendations", selecting strict output preflight and replacement of only the three expected artifacts for the requested version.
- Research base: `main` at `a692adf875132074c70d69effe2693443da5ec5b`; invoking checkout `/home/alexbanica/workspace/RpiEPaper`.
- Planning only; no implementation, publication, commit, push, merge, or deployment authorization. No predecessor approved SPEC/PLAN exists in this checkout for this scope. PLAN authoring requires approval of this complete specification.

## Problem and evidence

- M001: `scripts/package_artifacts.py:318-327,354-357` deletes every regular output-directory file before building, and can delete files before rejecting a subdirectory.
- M011: release builds prepare an isolated version-patched tree (`package_artifacts.py:367-370`, `release_version.py:60-88`), but standalone `verify():395-408` reads the unpatched checkout version; CLI verification takes precedence over the supplied release tag at lines 420-427.
- M012: standalone publishing checks filenames and Twine metadata before upload, but checks runtime/resources/libraries afterward (`scripts/publish_forgejo.py:76-117,461-475`). The configured workflow's builder already performs deeper archive checks; this finding does not establish an invalid published release.

## Scope and preserved contracts

Boundaries: `scripts/package_artifacts.py`, `scripts/publish_forgejo.py`, and `scripts/release_version.py` only as needed to share release-version/archive validation. Update maintained README release instructions; change workflow invocation only if necessary to pass the same existing release context.

Preserve exact accepted stable/beta tags, PEP 440 beta normalization, project metadata authority, one sdist and two ARM wheels, absence of universal wheels, wheel RECORD validation, required resource bytes, all four tracked native library bytes and ELF checks, temporary source version preparation, and untouched checkout metadata. Preserve index/upload endpoints, post-upload anonymous installation verification, immutable release versions, and upload-only credential scope.

No actual build publication, index mutation, version overwrite, remote package cleanup, new release format, rollback service, or credential access is authorized by planning.

## Required behavior

### REL-1: Preflight before any output deletion (M001)

Compute the three exact expected filenames from the requested effective release version before clearing output. Resolve the output destination once for all build/validation operations, while rejecting a selected output directory that is itself a symlink. An absent destination may be created normally.

For an existing destination, inspect every entry before deleting any entry. An empty directory is valid. Any subset of the three expected names is valid only when every present entry is a regular nonsymlink file. Reject unrelated files, other-version artifacts, symlinks (including broken symlinks and symlinks with expected names), subdirectories, or special filesystem entries. Rejection preserves all existing entries and starts no build.

After successful preflight, replace only those expected artifacts. Do not promise restoration of prior expected artifacts if a subsequent build fails; report failure truthfully. This is a local operator-safety contract, not a guarantee against concurrent hostile modification of the destination.

### REL-2: Consistent expected version for verification (M011)

Keep ordinary `--verify <artifact>` behavior: the checkout metadata provides the expected version. When `--release-tag <tag>` accompanies `--verify`, validate/normalize that tag and use its canonical version for filename, distribution metadata, and packaged runtime-version checks. Do not build or upload when verifying.

Stable/beta verification must not rewrite source metadata. Invalid tags or mismatched artifact versions fail clearly. Build, standalone verification, and publisher-local validation must apply consistent expected-version rules rather than depending on a temporarily patched checkout.

### REL-3: Enforce package contracts before upload (M012)

Before any upload, validate the exact selected three artifacts against the requested canonical version: names/set, distribution metadata, required module/resource/native files, expected wheel tags/nonpure status, wheel RECORD integrity, required resource/native byte identity, native ELF contracts, and packaged `cluster_monitor.__version__`. Runtime version inspection must not import or execute packaged application/native code.

Use the requested release version independently of the source checkout's static version. Preserve existing publisher handling of unrelated nonpackage files; do not accidentally apply the builder's strict output-directory policy to publication inputs. Existing conflicting-package rejection remains.

Any local integrity failure prevents upload entirely. Twine checks remain pre-upload. Anonymous post-upload installation and resolution checks remain necessary and cannot be claimed from local archive checks. Do not extend source-byte comparison to all Python implementation files; the existing required bytes and version contract define this correction boundary.

## Acceptance and validation

1. Empty/new output destinations and subsets of expected files work. Unrelated entries, other versions, symlinks, subdirectories, and special files cause preflight rejection without partial deletion. A relative output path refers to the same resolved location throughout temporary-tree builds.
2. Verify valid stable and beta artifacts built for versions different from checkout `1.0.0`; reject wrong tags, metadata, filenames, and runtime versions. Verify-only operation does not build, publish, or modify the checkout.
3. In controlled credential-free operator/dry-run checks, malformed but otherwise Twine-valid payloads fail before the upload boundary: missing/changed resources or libraries, wrong runtime version, invalid RECORD or platform metadata. Valid payloads reach the normal upload boundary without executing an upload during these checks.
4. Preserve the three-artifact contract, source native/resource bytes, source metadata, credential isolation, and post-publication verification sequence.
5. No automated packaging/tooling/workflow tests may be created or maintained. Use static/syntax/structural, archive inspection, controlled temporary-directory checks, and build/dry-run validation. Live publication requires separate authority and is not established by these checks.

## Dependencies, risks, and documentation

This group is independent of G2-G5. M001, M011, and M012 share artifact identity/version helpers and must not develop competing validators. README must explain safe destination replacement, release-tag-aware verification, and local versus post-upload evidence. Normal operational publication still has external/network failure modes and remains outside this planning request.

## Approval

Approved by the user on 2026-10-16 in the parent conversation with "approve", responding to the presentation of all five complete Proposed specifications at Checkpoint 06. Approval covers this complete specification, including the previously accepted recommendations. It does not approve a PLAN or authorize implementation, commit, push, or deployment.
