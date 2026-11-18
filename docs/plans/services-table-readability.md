# Services table readability implementation plan

Status: Approved
Date: 2026-11-18
SPEC: docs/specs/services-table-readability.md (Approved 2026-11-18)

## Outcome and authority

Deliver the approved fixed Name / Ver / R table, compact image releases, measured
text fitting, five visible rows, and existing scrolling. The user additionally
requested cleanup of unused code and code debt: remove obsolete display formatting
and imports within the affected path after checking consumers. This does not
authorize a repository-wide refactor or deletion of retained source data.

This PLAN is planning-only until separately approved and invoked through implement
in a fresh assistant session. No source implementation, Git delivery, deployment,
or cluster changes occur in this planning session.

## Workspace, base and delivery

- Planning origin: /home/alexbanica/workspace/RpiEPaper on main, research HEAD
  7ea5e1b7e02f58ffb5572333350d744e3efe8f33. Only new planning documents are dirty.
- Delivery branch: feat/services-table-readability.
- Isolated implementation path:
  /tmp/agent-worktrees/RpiEPaper/services-table-readability.
- Implementation refreshes origin/feat/services-table-readability if it already
  exists, otherwise origin/main (origin/master only if origin/main is unavailable).
  Resolve and record the actual remote SHA before source edits. The research SHA
  is provenance, not a pinned implementation base. Compare relevant source changes
  with the approved behavior; incompatible drift stops for required amendment.
- Parent alone prepares the isolated workspace and byte-verifies transferred
  approved SPEC/PLAN, retaining original content/index/HEAD recovery state. Preserve
  unrelated changes and the invoking main checkout. An unexpected branch/path
  collision or dirty/conflicting state stops; no reset or forced cleanup.
- For a genuinely new delivery branch, use detached verified upstream HEAD and
  verify the exact branch is absent locally and unattached immediately before the
  first authorized commit, then create it there. If remote delivery exists, use
  implement's verified resume path; do not reset an existing delivery to main.
- Parent stages only accepted paths, commits, and non-force pushes to
  origin/feat/services-table-readability; verify remote SHA and configured upstream.
  No merge, tag, publication, deployment, or restart is authorized.

## Architecture and assurance

One business capability is affected: displaying a Swarm service overview. Version
interpretation and the table are cooperating parts of that capability, not
multiple interacting business domains. Architect PLAN assurance is not triggered.
Independent plan-readiness review is mandatory.

Assurance profile: full. The entity's display projection feeds both application
orchestration and renderer consumers; this shared producer/consumer behavior makes
routine eligibility uncertain. Use a bounded developer, one independent integrated
code-review wave, consolidated corrections and affected validation, one final QA
pass, then a documentation-writer. Main retains integration and acceptance.

No API operations or events are added/changed/deleted, and no explicit contract
review was requested: contract reviewer is not triggered. No security review was
requested: security reviewer is not triggered. Reviewers still report supported
compatibility/security findings within the assigned diff.

All specialists receive fresh bounded manifests with unit_id, ownership,
prerequisites, artifact paths/hashes, commands/effects, acceptance and JSON handoff
contract. Aim three minutes per assignment; main interrupts at five minutes,
retains partial evidence and resplits remaining work without overlapping owners.
Workers never branch, commit, push, deploy, or create worktrees. Serialize source
mutations and shared checks. Stage completion is not a user continuation gate.

## Source boundary and implementation choices

Use only the approved artifacts and named source patterns below; no renewed
product research, live inventory, or external documentation is needed.

- Domain: DockerStatusEntity and deterministic domain tests. Keep original image,
  placement, ports, mode, timestamps and identity data available. Keep image_short
  and image_tag semantics as raw-reference/tag access. Add one clearly named
  compact release property implementing the SPEC's exact parsing rules, with
  no dependency on presentation, fonts or filesystem.
- Replace the table's pre-truncated name input with namespace-normalized but
  otherwise full text; keep existing namespace-removal semantics. The table
  projection supplies full name, compact release and replicas. Do not impose
  ePaper character limits on console output.
- Remove name_short/image_tag_short only if the complete refreshed-base consumer
  search confirms they are obsolete after migration. Remove obsolete display-only
  port-list construction and unused projection fields only where that same search
  establishes there is no retained consumer; preserve raw fields and helpers used
  by get_open_ports or other screens. Update domain tests to verify approved
  behavior rather than retaining obsolete truncation solely for old assertions.
- Application: page-2 headers become Name / Ver / R; preserve service ordering,
  title, count, slicing, and button/controller behavior.
- ePaper: fixed widths 168 / 56 / 30 px, 5 px outer margins, 2 px cell side
  padding, bundled 10 px font, 3 px table vertical padding. Keep boundaries fixed
  across all batches/refreshes; measure whole strings and fit with an ellipsis.
  Reuse a single small fitting helper, with no dynamic column sizing, new layout
  framework, optional knobs, or duplicated name/version truncation.
- Keep renderer method contracts unchanged. Apply the fixed service-table layout
  to its known header keys; retain existing behavior for other table shapes.
  Console keeps its existing width calculation and renders full service names
  with compact release values; it receives no ePaper pixel constraints.
- No controller, Docker adapter, dependency, CI, packaging, or configuration
  changes are expected. A newly required change beyond these boundaries is an
  amendment trigger, not permission to broaden the work silently.

## Units and sequencing

| Unit | Owner and exact paths | Prerequisites | Completion |
| --- | --- | --- | --- |
| U1 release projection and cleanup | developer: cluster_monitor/domain/entities/docker_status_entity.py; tests/test_docker_status_entity.py | Verified workspace and artifact hashes | Domain tests written first for parsing and preserved replica behavior; full name projection and raw-data preservation; obsolete domain display code removed after consumer checks |
| U2 fixed services rendering | developer: cluster_monitor/application/services/cluster_monitor_service.py; cluster_monitor/presentation/renderers/epapers/epaper_renderer.py | U1 integrated | Three columns with fixed geometry, measured ellipsis, five rows inside panel; obsolete affected imports/display paths removed; console smoke and actual-size preview |
| U3 integrated assurance | code-reviewer then developer correction, qa-agent; source correction ownership remains U1/U2 paths | U1/U2 complete and diff frozen | Entire integrated diff reviewed; supported findings disposed, one correction batch and affected checks; final QA independently checks SPEC and cleanup |
| U4 documentation and delivery cleanup | documentation-writer: README.md; parent: SPEC/PLAN lifecycle, staging/Git/workspace reconciliation | U3 evidence; full behavior agreed | Maintained documentation complete, all still-required acceptance assessed, accepted branch commit/push verified, temporary/transfer state safely reconciled |

The developer may execute U1 and U2 serially within bounded assignments. A partial
handoff queues remaining work; it does not end the lifecycle. Main supplies the
complete integrated diff, artifact hashes, exact check evidence, source baseline
and unresolved findings to reviewers. Main independently verifies handoffs.

## Validation

Use an available compatible Python environment; research used
/home/alexbanica/.pyenv/versions/3.10.14/bin/python with Pillow 10.4.0. Choose an
existing environment or a temporary implementation environment without changing
global interpreter settings. Missing dependencies are a concrete check blocker;
never claim an unrun check passed.

1. Domain-only test-first coverage in tests/test_docker_status_entity.py for every
   SPEC release example; registry ports/digests; whole-token prerelease matching;
   unknown tags; full normalized names; replicated/global/zero replica strings;
   retained raw image, ports and placement. Run `python -m unittest discover -s tests`.
2. Run `python -m ruff check cluster_monitor scripts tests`, syntax compilation of
   changed Python files with temporary bytecode output, and parent `git diff --check`.
3. Produce a manual Pillow preview from the actual renderer path and bundled font,
   using a minimal hardware stub if necessary, without importing real GPIO or
   Waveshare integrations. Cover 264x176 dimensions, surrounding frame/title/count,
   five rows, empty/partial batches, long names/versions/replica strings, global and
   zero replicas. Inspect at actual size and enlarged. Confirm fixed boundaries
   5, 173, 229, 259; 3 px vertical table padding yields a table bottom near y=156.
   Verify full `2.0.0-beta5` and `20/20` fit. No renderer or orchestration automated
   tests or permanent validation scripts may be added.
4. Manual/static smoke checks confirm console receives full names and compact
   versions, other pages/table shapes retain behavior, and button handlers and
   five-row step remain unchanged. Avoid full runtime startup and cluster effects.
5. Bounded reference searches and diff inspection establish no dead replaced
   helpers/imports, duplicated clipping, obsolete Nodes/Ports/Img headers, or
   tests maintaining removed truncation within the changed source path. Preserve
   live consumers and raw data; an unused-looking public value is not by itself
   evidence that deleting it is safe.
6. Physical panel legibility and button scrolling are still required operator
   acceptance under the approved SPEC. No hardware mutation or deployment is
   authorized here. Obtain already available operator evidence or report these
   exact criteria unmet as blocked DRAFT; source/preview evidence cannot replace
   physical evidence. An explicit later user deferral changes that scope and must
   be recorded without claiming the checks passed.

No new hosted CI requirement is introduced. Inspect/report checks triggered by
authorized push; do not equate local success with hosted or hardware evidence.

## Documentation, cleanup and delivery completion

README documents the three columns, fixed geometry, pixel fitting, image release
and prerelease rules, unknown-version marker, unchanged replica semantics, and
that removed Nodes/Ports data remains collected. Remove obsolete descriptions
within that maintained documentation.

Unused-code cleanup is part of U1/U2 and independent review, not an afterthought.
No repository-wide dead-code scan or speculative cleanup, no removal of other
branches/worktrees, no secrets or unrelated files touched.

Preserve SPEC/PLAN until acceptance is complete. Once behavior is consolidated
into maintained documentation and all in-scope criteria pass, remove this SPEC
and its matching PLAN together in the final accepted delivery. If physical or
other required evidence is blocked, retain both with truthful DRAFT reporting.
Keep review/check/cleanup evidence in the handoff and commit history; no sidecar
approval workspace. Remove task-created temporary scripts/previews after needed
evidence is retained; do not delete unrelated /tmp artifacts. Restore only
unchanged transferred planning content/index in the invoking checkout, verifying
that recovery does not overwrite user edits. Ordinary branch push detaches the
clean implementation worktree under implement; do not force-remove it or prune
unrelated registrations. Release any task-created temporary environment safely.

Definition of Done: approved behavior delivered; domain/static/manual checks pass;
independent review/corrections/final QA/documentation complete; physical operator
evidence obtained or explicitly deferred; obsolete affected code removed; artifact
pair cleanup completed only when eligible; accepted staging inspected; commit,
remote branch SHA/upstream and transfer cleanup verified. Source changes alone
are not terminal acceptance. A genuine blocker allows a verified DRAFT branch
checkpoint with exact remaining obligations, not a claim of completion.

Failed fetches, incompatible base drift, unsafe workspace/path states, missing
authority, source/behavior mismatch, unsupported required checks, unresolved
findings or missing operator evidence stop affected work as DRAFT after safe
independent work and authorized checkpoint delivery. Amend artifacts within valid
implement using its same-session automatic amendment procedure where applicable.

## Requirement-to-delivery trace

| SPEC anchor | Units / owned paths or preserved outcome | Evidence |
| --- | --- | --- |
| Scope and exclusions; Definitions | U1/U2 named source; adapter/controller unchanged | Diff and reference checks; code review; final QA |
| Image release extraction 1–5 and examples | U1 domain entity/tests | Domain tests including raw-data preservation |
| Structured rendering: three columns/full names/fixed widths/no overlap | U1/U2 domain projection, service headers, ePaper renderer | Measured actual-renderer preview and domain projection checks |
| Structured rendering: title/count/five rows/order/scroll/other tables/console | U2 source; unchanged controller/console contract | Frame preview; manual console and structural checks |
| Regression boundaries | U1/U2 cleanup boundary; unchanged adapters/controllers/data | Domain regression checks; integrated diff/review |
| Acceptance 1–2, 4 | U1–U3 | Domain suite, Ruff, syntax, main diff check; smoke evidence |
| Acceptance 3 | U2/U3 | Actual-size preview and independent QA inspection |
| Acceptance 5 | U3/operator evidence, no deployment | Physical evidence or explicitly disclosed unmet/deferred criterion |
| Documentation and approval; user unused-code cleanup | U1/U2 cleanup; U4 README and parent artifact lifecycle | Reference audit, review disposition, maintained docs, paired removal when eligible |
| Delivery lifecycle | Parent U4 | Verified accepted commit/remote branch, clean preserved origin and transfer recovery, or blocked DRAFT evidence |

## Plan assurance and approval

Independent readiness review: completed 2026-11-18 by plan-readiness-reviewer,
unit services-plan-readiness. Reviewed complete PLAN content SHA-256
b7f4a87ef1f3e847504084bb59682d00a8eed402dba4cb6a9d396ff386baed41
against approved SPEC SHA-256
ff6bd188e24cce94bc2be81f304c02d4e77436ae80c0a16d7817089451804976
and targeted source consumers. No findings. Coverage included handoff, fixed
geometry, parsing, cleanup consumer safety, preserved port helpers, domain-only
tests, manual rendering, physical acceptance, full assurance, Git delivery and
paired artifact cleanup. This entry records assurance only; it changes no planned
behavior or execution decisions. Remote and physical state were not validated.
Architect trigger absent as recorded above.

Approval: Explicit user approval on 2026-11-18: “approve”, in response to the
complete PLAN approval presentation at Checkpoint 06. Covers the full planned
implementation, related unused-code cleanup, assurance, validation, documentation,
and verified branch delivery, subject to fresh-session implement entry.
