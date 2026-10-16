# PLAN: Exclusive panel frame lifecycle and unconditional resilient teardown

Status: Approved

## Approved input and authority

- Date: 2026-10-16; group G3; findings M003, M009.
- Approved SPEC: `../specs/SPEC-maintenance-display-lifecycle.md`; SHA-256 `f50ac3b3fc7fb9fb83ecaef2af279b3685a4629b0bb92339dab80e49842a006f`. User approved all five complete specifications with "approve" after Checkpoint 06 on 2026-10-16.
- Origin: planning-only request for every audit group; M002/M004 expressly excluded. No batch-authorized status or implementation consent is inferred.
- Research base: `a692adf875132074c70d69effe2693443da5ec5b` on main in `/home/alexbanica/workspace/RpiEPaper`.
- No implementation, branch/worktree creation, commit, push, publication or deployment occurs during this planning request. PLAN approval and valid clean-context implement entry remain separate gates.

## Final state and boundaries

Deliver the approved SPEC unchanged through the deterministic units below. No new discovery/audit is planned: inspect only named patterns, direct dependencies, credible regressions and deterministic outputs. If new behavior is needed, stop affected units for the applicable amendment procedure; do not edit an approved predecessor SPEC/PLAN as part of new-group work.

Integrate G2 SSH lifecycle first and G4 local-command/alert semantics before final G3 cleanup verification. G5 follows G3.

M002 SSH execution/output/cancellation bounds and M004 SSH host-key trust remain excluded from every unit, refactor, review and validation outcome. No claimed bounded overall shutdown or trusted SSH identity may be inferred from these plans.

## Implementation workspace and delivery proposal

All five proposed plans are parts of one coordinated future maintenance delivery. Use branch `maintenance/selected-2026-10-16` at remote `origin` (`git@github.com:alexbanica/RpiEPaper.git`) and one parent-managed isolated workspace `/tmp/agent-worktrees/RpiEPaper/maintenance-selected-2026-10-16`. No main merge, PR merge, tag, upload or deployment is planned. Do not create separate group branches or worktrees.

The explicit research/execution base is pinned to `a692adf875132074c70d69effe2693443da5ec5b`. Future implement entry fetches origin, resolves remote main and records its SHA; a changed remote main or unexpected delivery branch requires reconciliation/amendment before source edits, never silently rebase. An expected verified delivery checkpoint may resume only its same branch and ancestry, not fresh main.

Planning verification on 2026-10-16 found this branch absent locally and on origin; execution must recheck. For initial execution, verify the delivery branch absent locally/remotely and unattached and the exact worktree destination safe. Create/reuse a detached clean worktree at the pinned commit. Preserve invoking main and all unrelated work. Transfer all five approved SPEC/PLAN pairs byte-for-byte, retaining their original content/index/HEAD recovery state and checking digests. Do not transfer unrelated untracked files. For an exact registered-but-absent temporary path, non-forced removal of only that registration followed by verification/recreation is allowed; dirty, present-conflicting, unknown or unsafe state stops as DRAFT without reset/stash/force cleanup.

Immediately before the first authorized commit, recheck exact branch absence and no attachment, create it at verified detached HEAD, stage only accepted coordinated paths, and use explicit push destination `origin HEAD:refs/heads/maintenance/selected-2026-10-16`. Confirm upstream equals that delivery ref and independently fetch/compare remote SHA. A later authorized implement request is required for these effects; this PLAN only proposes them.

After verified push, detach the worktree and restore only byte-unchanged transferred invoking content/index under the implement transfer rules. Retain the clean detached worktree for checkpoint continuation; no forced cleanup. Commit/push/transfer verification failure is DRAFT, never successful delivery.

## Units and exclusive ownership

Parent owns requirements, scheduling, integration, Git and acceptance. At most one active explorer and one architect; use lower native/client capacity, at most three per other specialist category. Record ephemeral ownership/prerequisites/digests before every fresh-context assignment. Independent groups may overlap only on disjoint source; serialize README, contracts, shared application files and all repository mutations/checks. Children are not alone and preserve others' work.

### G3-U1: Exclusive frames and periodic stop

- Owner: fresh native developer; immutable source boundary: `cluster_monitor/presentation/renderers/epapers/epaper_renderer.py; cluster_monitor/domain/services/renderer_interface.py; cluster_monitor/presentation/renderers/abstract_renderer.py and console_renderer.py minimal compatible frame hooks; cluster_monitor/application/services/cluster_monitor_service.py frame transaction boundaries`.
- Prerequisites: G2 application handoff; shared application file serialized.
- Work and completion: Use an explicit frame transaction with exception-safe release and exclusive hard refresh. Periodic worker uses an interruptible event, stops/join before final panel operations and hardware cleanup. A positive interval waits configured duration; nonpositive disables. No EPD calls after shutdown. Never self-join or join while retaining a lock the worker requires; wake a waiting worker immediately and await an active operation before cleanup. Existing vendor calls may delay completion without bound; do not abandon a live worker or introduce vendor/SSH deadlines.
- Validation/evidence: Nonhardware instrumented operator smoke observes frame/periodic/page-change ordering, close during wait/active refresh, draw exception, repeated/reentrant close and initialization failure. No Waveshare import or GPIO access in checks.
- Developer returns changed paths, checks, SPEC/PLAN digests, findings and remainder; never commits, pushes, deploys or manages worktrees. Aim three minutes, hard five-minute assignment limit. Parent splits oversized work into disjoint bounded assignments before dispatch; interrupted work is reconciled before reassignment.


### G3-U2: Owned resource teardown

- Owner: fresh native developer; immutable source boundary: `cluster_monitor/application/services/cluster_monitor_service.py close/signal handling; cluster_monitor/presentation/renderers/renderer_manager.py; epaper_renderer.py and controllers/epaper_controller.py only cleanup coordination`.
- Prerequisites: G3-U1; G2 integrated; G4 integrated for final timeout/failure smoke.
- Work and completion: Stop app work; attempt alert reset, renderer/controller/periodic cleanup, supervisor, Docker and remote unconditionally. Record failures, finish eligible teardown then raise first failure to caller; later failures remain logged. Signal handlers only request stopping; the owning execution path unwinds/releases any active frame and performs teardown from start() finally. A close request by the active frame owner is deferred until that frame unwinds; another thread waits for frame release before cleanup, without holding a worker-required lock. Further signals during teardown only retain the stop request. Guard repeated/reentrant/concurrent teardown and never resume drawing after completed cleanup; hardware cleanup is attempted despite a completed panel shutdown error, but never while an active worker still uses the panel. Never close shared gpiozero factory.
- Validation/evidence: One-shot nonhardware operator scenarios HAT on/off/status failure and each cleanup failure independently; each remaining resource is attempted, no duplicate successful cleanup, hardware release ordering visible, failure observable. Deliver SIGTERM/SIGINT-equivalent stop requests during a frame and again during teardown in inert smoke checks; prove frame unwind precedes cleanup and drawing never resumes afterward. Check close from the frame owner and another thread separately.
- Developer returns changed paths, checks, SPEC/PLAN digests, findings and remainder; never commits, pushes, deploys or manages worktrees. Aim three minutes, hard five-minute assignment limit. Parent splits oversized work into disjoint bounded assignments before dispatch; interrupted work is reconciled before reassignment.


## Requirement-to-delivery trace

| Approved SPEC anchor | Delivery units | Owned boundary / terminal evidence |
| --- | --- | --- |
| LIFE-1; Acceptance 1 | G3-U1 | frame contract/panel worker; periodic/page-change/frame ordering evidence |
| LIFE-1; Acceptance 2 | G3-U1, G3-U2 | wake/join/final panel/release ordering; no post-cleanup EPD operation |
| LIFE-1, LIFE-2; Acceptance 3 | G3-U1, G3-U2 | close guards, signal stop/unwind and initialization cleanup; repeated/concurrent/reentrant observations |
| LIFE-2; Acceptance 4 | G3-U2 | unconditional resilient owned teardown; HAT on/off/status and each-cleanup-failure observations |
| Acceptance 5 | G3-U1, G3-U2; G5-U3 downstream regression | console/import isolation, pages/buttons/config and process-lifetime GPIO factory preservation |
| Acceptance 6 | All units; final QA; authorized target operator | static/nonhardware lifecycle evidence; no non-domain tests; physical display/button result requires separately authorized target check or explicit user deferral |
| Scope and preserved behavior/contracts; constraints and exclusions | All units; integrated review | named path diffs preserve all declared invariants, no M002/M004 inclusion or non-domain tests |
| Dependencies, risks, and documentation | All units; DOC and FINAL | verified predecessor handoffs, serialized ownership, README and final lifecycle/delivery evidence |

## Validation commands and evidence

Use injected inert renderer/panel/service objects in a controlled manual smoke invocation without importing Waveshare or running subprocesses. Static inspection must show exception-safe frame ownership and cancellation/join order. Console import and monitor-client paths must remain hardware-free. Physical panel/button operation can only be claimed after separately authorized target evidence; these plans authorize no deployment or real hardware operations.

Common required development checks in the isolated execution environment:

- `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests` for existing and newly permitted domain tests only.
- AST syntax parsing of tracked first-party Python files, excluding vendored `lib`; no bytecode/artifacts in source.
- `python -m ruff check cluster_monitor scripts tests` using the repository dev dependency flow in an isolated environment. Ruff was unavailable in the audit environment; provision existing declared development requirements when implementation is authorized. If unavailable then, report exact failed prerequisite rather than treating lint as passed or silently omitting it.
- Parent runs `git diff --check`, inspects changed/staged paths and verifies all group criteria/dependencies/artifact digests. Documentation-only planning does not require rerunning source tests now.

Non-domain checks are controlled operator/static/build/smoke evidence, not new or maintained automated test files. Keep transient output outside the source/worktree, use inert services and harmless child processes, never credentials/live SSH/Docker/HAT. Local checks establish source behavior and specified nonhardware lifecycle contracts; they do not establish deployed permissions, physical output, actual node recovery, registry availability or publication success. If a later requested acceptance check needs live effects, obtain that effect authority or report the exact blocked criterion; never invent evidence.

## Assurance and corrections

Profile: **full** for this entire coordinated change, because cross-component sequencing, shared contracts, executable configuration/process handling and release integrity are involved. One combined independent review wave covers the complete integrated diff across all five approved groups, rather than repeating the same wave per PLAN. Every reviewer independently covers its entire applicable integrated boundary using the actual diff, approved artifacts/digests, trace and exact check evidence.

Required roles: bounded fresh developers, independent code-reviewer, applicable contract-reviewer and security-reviewer, final qa-agent, and one final documentation-writer. Contract review covers renderer frame protocol and lifecycle/cleanup sequencing; security review is inapplicable unless effects or permissions expand, which is a stop/amendment condition. Vendor hardware-call deadlines and SSH deadlines remain outside scope.

Wait for the entire required review wave. Parent disposes every finding, applies one consolidated accepted correction batch through bounded developers, then reruns affected checks. Full final QA independently checks acceptance using new observations where needed, not merely repetition of unchanged successful commands. Repeat the full cycle only for the qualifying confirmed failures/regressions/incompatibilities/security defects defined by implement; speculation does not create review loops. An out-of-scope correction or missing authority is a stop/amendment boundary.

DOC: after final QA and any qualifying corrections, one documentation-writer synchronizes README with final implementation and all five approved SPECs, without inventing behavior. Documentation ownership is parent-serialized across groups. Preserve AGENTS constraints. Because docs/specs and docs/plans contain active work only, remove each completed SPEC and matching PLAN together only after maintained documentation/configuration consolidates durable behavior. Keep any incomplete pair, never delete approved active predecessors to imply completion. Commit removal with final documentation if full delivery is accepted; Git retains reviewed artifacts/history as applicable. Parent verifies final source/docs, digests of any retained active artifacts, staged scope, and final DoD.

## Definition of Done, checkpoints, and recovery

All selected units, all acceptance criteria, preserved invariants, required development checks, independent review findings, qualifying correction cycles, final QA and maintained documentation are assessed. G3 physical display/button evidence remains a separate target-validation prerequisite: before claiming that criterion or terminal coordinated acceptance, obtain explicit authority for the exact operator-supplied target and collect its smoke evidence, or record an explicit user skip/defer. Missing target authority/evidence is a concrete unmet criterion, not implicit permission to deploy or a successful nonhardware substitute. Final coordinated delivery additionally requires verified authorized commit/push of all accepted paths to the exact branch, final remote SHA/upstream, and safe transfer/workspace disposition. No omitted original criterion is claimed met; only explicit user skip/defer can reduce acceptance scope.

A unit handoff or checkpoint is intermediate: parent reports `Checkpoint XX`, remaining obligations and next ready unit, and continues without routine continuation questions. Temporary agent capacity is queued scheduling, not a terminal blocker. Five-minute deadlines are enforced by interruption and evidence/ownership reconciliation, never duplicated overlapping assignments.

For an authorized incomplete checkpoint, reconcile and preserve source/artifacts/checks, commit/push truthful DRAFT to the same branch if safe/authorized, verify remote and detach; retain exact remaining criteria. Resume fetches the same delivery ref, verifies ancestry/no other attachment, fast-forwards only and reattaches the clean registered worktree. Unexpected branch/worktree/base, credentials/effects, unresolved behavior, unsafe unrelated state or unavailable required validation stops affected delivery as evidenced DRAFT after safe independent work; never reset, stash, force-push or silently weaken checks.

## Plan assurance

Required plan assurance completed on 2026-10-16 by fresh native explorer `plan_explorer_assurance` and architect `plan_architect_assurance`, followed by read-only correction verification by the same roles. Both independently read all five complete Approved SPEC / Proposed PLAN pairs and relevant current source against pinned HEAD `a692adf875132074c70d69effe2693443da5ec5b`, and verified all SPEC pins. Reviewed final substantive draft SHA-256 for this PLAN: `1d699b3b50bd96338a936a541cdb1405787d3951e3e5275828dd496d9ae8cbec` (before this assurance-only record).

Explorer: verified source inventory, current RuntimeService references, dependency ordering, named unit/check coverage, exact acceptance traces, scope exclusions and delivery assumptions; no actionable gaps remained. Network branch absence was parent-verified, not independently repeated by the explorer. Architect: required explicit signal/frame unwinding before cleanup, a precise injected renderer-manager lifecycle contract, and removal of a join-bound claim inconsistent with unbounded vendor calls. Parent corrected G3 signal/close/join sequencing and G5 RendererManagerInterface/source export/injection, then both roles verified the corrected drafts. Every numbered acceptance criterion now has an exact trace row; G3 physical evidence remains pending authorized target validation or explicit user deferral. No approved SPEC behavior/content changed during these PLAN corrections.

Disposition: all supported findings resolved; no actionable plan-assurance finding remains. Assurance is advisory and static, not user PLAN approval, future integrated-code assurance, runtime evidence or execution authority. Final artifact digest changes only because this assurance record was appended; parent verifies the final files before approval presentation.

## Approval

Approved by the user on 2026-10-16 with "approve", responding to the presentation of all five complete assured Proposed PLANs at Checkpoint 08. Reviewed Proposed revision SHA-256: `e4462c11ecf84676f2be31f6acf8e5cd9f2808fe2dc7b59ac92f9a808fedf184`. Approval covers this complete PLAN and its pinned Approved SPEC. This records planning approval only; implementation requires a separate valid implement entry with a new session, cleared context, or explicit same-context consent. No implementation, commit, push, merge, publication, deployment, or hardware operation was performed by this approval record.
