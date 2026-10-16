# PLAN: Renderable fallback, sparse config merge, reliable alerts, exact IP parsing and local deadlines

Status: Approved

## Approved input and authority

- Date: 2026-10-16; group G4; findings M005, M007, M008, M016, M019.
- Approved SPEC: `../specs/SPEC-maintenance-local-monitoring-config.md`; SHA-256 `2def79f9823a5a9ffe9bfe38126e2a3fec9f3b1968dedea2bb6794203eeca028`. User approved all five complete specifications with "approve" after Checkpoint 06 on 2026-10-16.
- Origin: planning-only request for every audit group; M002/M004 expressly excluded. No batch-authorized status or implementation consent is inferred.
- Research base: `a692adf875132074c70d69effe2693443da5ec5b` on main in `/home/alexbanica/workspace/RpiEPaper`.
- No implementation, branch/worktree creation, commit, push, publication or deployment occurs during this planning request. PLAN approval and valid clean-context implement entry remain separate gates.

## Final state and boundaries

Deliver the approved SPEC unchanged through the deterministic units below. No new discovery/audit is planned: inspect only named patterns, direct dependencies, credible regressions and deterministic outputs. If new behavior is needed, stop affected units for the applicable amendment procedure; do not edit an approved predecessor SPEC/PLAN as part of new-group work.

Independent source ownership from G2. Integrate before final G3 teardown checks; G5 composition follows.

M002 SSH execution/output/cancellation bounds and M004 SSH host-key trust remain excluded from every unit, refactor, review and validation outcome. No claimed bounded overall shutdown or trusted SSH identity may be inferred from these plans.

## Implementation workspace and delivery proposal

All five proposed plans are parts of one coordinated future maintenance delivery. Use branch `maintenance/selected-2026-10-16` at remote `origin` (`git@github.com:alexbanica/RpiEPaper.git`) and one parent-managed isolated workspace `/tmp/agent-worktrees/RpiEPaper/maintenance-selected-2026-10-16`. No main merge, PR merge, tag, upload or deployment is planned. Do not create separate group branches or worktrees.

The explicit research/execution base is pinned to `a692adf875132074c70d69effe2693443da5ec5b`. Future implement entry fetches origin, resolves remote main and records its SHA; a changed remote main or unexpected delivery branch requires reconciliation/amendment before source edits, never silently rebase. An expected verified delivery checkpoint may resume only its same branch and ancestry, not fresh main.

Planning verification on 2026-10-16 found this branch absent locally and on origin; execution must recheck. For initial execution, verify the delivery branch absent locally/remotely and unattached and the exact worktree destination safe. Create/reuse a detached clean worktree at the pinned commit. Preserve invoking main and all unrelated work. Transfer all five approved SPEC/PLAN pairs byte-for-byte, retaining their original content/index/HEAD recovery state and checking digests. Do not transfer unrelated untracked files. For an exact registered-but-absent temporary path, non-forced removal of only that registration followed by verification/recreation is allowed; dirty, present-conflicting, unknown or unsafe state stops as DRAFT without reset/stash/force cleanup.

Immediately before the first authorized commit, recheck exact branch absence and no attachment, create it at verified detached HEAD, stage only accepted coordinated paths, and use explicit push destination `origin HEAD:refs/heads/maintenance/selected-2026-10-16`. Confirm upstream equals that delivery ref and independently fetch/compare remote SHA. A later authorized implement request is required for these effects; this PLAN only proposes them.

After verified push, detach the worktree and restore only byte-unchanged transferred invoking content/index under the implement transfer rules. Retain the clean detached worktree for checkpoint continuation; no forced cleanup. Commit/push/transfer verification failure is DRAFT, never successful delivery.

## Units and exclusive ownership

Parent owns requirements, scheduling, integration, Git and acceptance. At most one active explorer and one architect; use lower native/client capacity, at most three per other specialist category. Record ephemeral ownership/prerequisites/digests before every fresh-context assignment. Independent groups may overlap only on disjoint source; serialize README, contracts, shared application files and all repository mutations/checks. Children are not alone and preserve others' work.

### G4-U1: Local command and alert correctness

- Owner: fresh native developer; immutable source boundary: `cluster_monitor/infrastructure/services/rpi_service.py local subprocess paths and alert cache`.
- Prerequisites: None.
- Work and completion: Apply fixed 10sec deadline to ifconfig/status/alert/each restart off/on child. On timeout kill/terminate and reap child with closed streams before failure returns; avoid Popen context wait trap. Preserve error/fallback paths, 2sec restart delay and no on after failed off. Update alert cache only on success, preserve startup false short-circuit.
- Validation/evidence: Controlled nonhardware child commands demonstrate 10sec timeout plus cleanup overhead, termination/reaping and pipes release; no real clusterhat commands. Observe same-state retry after failure/timeout and dedup after success.
- Developer returns changed paths, checks, SPEC/PLAN digests, findings and remainder; never commits, pushes, deploys or manages worktrees. Aim three minutes, hard five-minute assignment limit. Parent splits oversized work into disjoint bounded assignments before dispatch; interrupted work is reconciled before reassignment.


### G4-U2: Statistics fallback and IP parsing

- Owner: fresh native developer; immutable source boundary: `cluster_monitor/infrastructure/services/rpi_service.py thermal render and ifconfig parsing`.
- Prerequisites: G4-U1; same source owner serialized.
- Work and completion: Render unknown temperature as T: N/A without degree suffix; preserve normal numeric line/fan suffix and collection contract. Parse exact interface blocks, IPv4 only, eth0 then wlan0; no cross-block or suffix matching.
- Validation/evidence: One-shot controlled smoke inputs: numeric/missing/malformed temperature; exact eth0/wlan0, IPv6-only/no IPv4, intervening bridge and misleading interface names; preserve stdout format for monitor client.
- Developer returns changed paths, checks, SPEC/PLAN digests, findings and remainder; never commits, pushes, deploys or manages worktrees. Aim three minutes, hard five-minute assignment limit. Parent splits oversized work into disjoint bounded assignments before dispatch; interrupted work is reconciled before reassignment.


### G4-U3: Sparse YAML overrides

- Owner: fresh native developer; immutable source boundary: `cluster_monitor/infrastructure/parsers/yaml_config_parser.py`.
- Prerequisites: Independent of G4-U1/U2.
- Work and completion: Use effective context values for missing renderer/supervisor keys, preserving explicit values, packaged defaults, existing YAML order and exact env override. No new config or schema-validation scope.
- Validation/evidence: Temporary external YAML operator smoke checks packaged-only threshold30, SSH-only preservation, layered renderer/supervisor partial overrides and missing exact env path failure.
- Developer returns changed paths, checks, SPEC/PLAN digests, findings and remainder; never commits, pushes, deploys or manages worktrees. Aim three minutes, hard five-minute assignment limit. Parent splits oversized work into disjoint bounded assignments before dispatch; interrupted work is reconciled before reassignment.


## Requirement-to-delivery trace

| Approved SPEC anchor | Delivery units | Owned boundary / terminal evidence |
| --- | --- | --- |
| LOCAL-1; Acceptance 1 | G4-U2 | RpiService thermal formatting; numeric/missing/malformed consumer output |
| LOCAL-2; Acceptance 2 | G4-U3 | YamlConfigParser sparse merge; packaged/partial/layered/env precedence observations |
| LOCAL-3; Acceptance 3 | G4-U1 | alert cache and retry; failure/timeout/success observations |
| LOCAL-4; Acceptance 4 | G4-U2 | interface-block parser; IPv4/IPv6, unrelated/suffix interfaces and fallback observations |
| LOCAL-5; Acceptance 5 | G4-U1 | local subprocess timeout/termination/reaping and separate restart deadlines; harmless-child observations |
| Acceptance 6 | All units; final QA | no non-domain tests; syntax/static/operator evidence; no hardware success claimed |
| Scope and preserved behavior/contracts; constraints and exclusions | All units; integrated review | named path diffs preserve all declared invariants, no M002/M004 inclusion or non-domain tests |
| Dependencies, risks, and documentation | All units; DOC and FINAL | verified predecessor handoffs, serialized ownership, README and final lifecycle/delivery evidence |

## Validation commands and evidence

No automated adapter/parser/subprocess tests are created. Use AST/syntax/static checks and controlled one-shot smoke/operator commands. Run harmless local child processes only for timeout evidence; no node restarts, alert GPIO, live sensors or remote SSH. Existing domain tests remain a regression check, not evidence of adapter behavior.

Common required development checks in the isolated execution environment:

- `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests` for existing and newly permitted domain tests only.
- AST syntax parsing of tracked first-party Python files, excluding vendored `lib`; no bytecode/artifacts in source.
- `python -m ruff check cluster_monitor scripts tests` using the repository dev dependency flow in an isolated environment. Ruff was unavailable in the audit environment; provision existing declared development requirements when implementation is authorized. If unavailable then, report exact failed prerequisite rather than treating lint as passed or silently omitting it.
- Parent runs `git diff --check`, inspects changed/staged paths and verifies all group criteria/dependencies/artifact digests. Documentation-only planning does not require rerunning source tests now.

Non-domain checks are controlled operator/static/build/smoke evidence, not new or maintained automated test files. Keep transient output outside the source/worktree, use inert services and harmless child processes, never credentials/live SSH/Docker/HAT. Local checks establish source behavior and specified nonhardware lifecycle contracts; they do not establish deployed permissions, physical output, actual node recovery, registry availability or publication success. If a later requested acceptance check needs live effects, obtain that effect authority or report the exact blocked criterion; never invent evidence.

## Assurance and corrections

Profile: **full** for this entire coordinated change, because cross-component sequencing, shared contracts, executable configuration/process handling and release integrity are involved. One combined independent review wave covers the complete integrated diff across all five approved groups, rather than repeating the same wave per PLAN. Every reviewer independently covers its entire applicable integrated boundary using the actual diff, approved artifacts/digests, trace and exact check evidence.

Required roles: bounded fresh developers, independent code-reviewer, applicable contract-reviewer and security-reviewer, final qa-agent, and one final documentation-writer. Contract review covers sparse config merging, fallbacks, retry and timeout semantics; security review covers process lifecycle/executable local-command boundaries and confirms argument-list/no-shell construction. No command/config expansion is authorized.

Wait for the entire required review wave. Parent disposes every finding, applies one consolidated accepted correction batch through bounded developers, then reruns affected checks. Full final QA independently checks acceptance using new observations where needed, not merely repetition of unchanged successful commands. Repeat the full cycle only for the qualifying confirmed failures/regressions/incompatibilities/security defects defined by implement; speculation does not create review loops. An out-of-scope correction or missing authority is a stop/amendment boundary.

DOC: after final QA and any qualifying corrections, one documentation-writer synchronizes README with final implementation and all five approved SPECs, without inventing behavior. Documentation ownership is parent-serialized across groups. Preserve AGENTS constraints. Because docs/specs and docs/plans contain active work only, remove each completed SPEC and matching PLAN together only after maintained documentation/configuration consolidates durable behavior. Keep any incomplete pair, never delete approved active predecessors to imply completion. Commit removal with final documentation if full delivery is accepted; Git retains reviewed artifacts/history as applicable. Parent verifies final source/docs, digests of any retained active artifacts, staged scope, and final DoD.

## Definition of Done, checkpoints, and recovery

All selected units, all acceptance criteria, preserved invariants, required development checks, independent review findings, qualifying correction cycles, final QA and maintained documentation are assessed. G3 physical display/button evidence remains a separate target-validation prerequisite: before claiming that criterion or terminal coordinated acceptance, obtain explicit authority for the exact operator-supplied target and collect its smoke evidence, or record an explicit user skip/defer. Missing target authority/evidence is a concrete unmet criterion, not implicit permission to deploy or a successful nonhardware substitute. Final coordinated delivery additionally requires verified authorized commit/push of all accepted paths to the exact branch, final remote SHA/upstream, and safe transfer/workspace disposition. No omitted original criterion is claimed met; only explicit user skip/defer can reduce acceptance scope.

A unit handoff or checkpoint is intermediate: parent reports `Checkpoint XX`, remaining obligations and next ready unit, and continues without routine continuation questions. Temporary agent capacity is queued scheduling, not a terminal blocker. Five-minute deadlines are enforced by interruption and evidence/ownership reconciliation, never duplicated overlapping assignments.

For an authorized incomplete checkpoint, reconcile and preserve source/artifacts/checks, commit/push truthful DRAFT to the same branch if safe/authorized, verify remote and detach; retain exact remaining criteria. Resume fetches the same delivery ref, verifies ancestry/no other attachment, fast-forwards only and reattaches the clean registered worktree. Unexpected branch/worktree/base, credentials/effects, unresolved behavior, unsafe unrelated state or unavailable required validation stops affected delivery as evidenced DRAFT after safe independent work; never reset, stash, force-push or silently weaken checks.

## Plan assurance

Required plan assurance completed on 2026-10-16 by fresh native explorer `plan_explorer_assurance` and architect `plan_architect_assurance`, followed by read-only correction verification by the same roles. Both independently read all five complete Approved SPEC / Proposed PLAN pairs and relevant current source against pinned HEAD `a692adf875132074c70d69effe2693443da5ec5b`, and verified all SPEC pins. Reviewed final substantive draft SHA-256 for this PLAN: `d01ebab5a05366e257678a927714092c9538da8c3d17969659692f63d0f11206` (before this assurance-only record).

Explorer: verified source inventory, current RuntimeService references, dependency ordering, named unit/check coverage, exact acceptance traces, scope exclusions and delivery assumptions; no actionable gaps remained. Network branch absence was parent-verified, not independently repeated by the explorer. Architect: required explicit signal/frame unwinding before cleanup, a precise injected renderer-manager lifecycle contract, and removal of a join-bound claim inconsistent with unbounded vendor calls. Parent corrected G3 signal/close/join sequencing and G5 RendererManagerInterface/source export/injection, then both roles verified the corrected drafts. Every numbered acceptance criterion now has an exact trace row; G3 physical evidence remains pending authorized target validation or explicit user deferral. No approved SPEC behavior/content changed during these PLAN corrections.

Disposition: all supported findings resolved; no actionable plan-assurance finding remains. Assurance is advisory and static, not user PLAN approval, future integrated-code assurance, runtime evidence or execution authority. Final artifact digest changes only because this assurance record was appended; parent verifies the final files before approval presentation.

## Approval

Approved by the user on 2026-10-16 with "approve", responding to the presentation of all five complete assured Proposed PLANs at Checkpoint 08. Reviewed Proposed revision SHA-256: `5629f1aa47c543d7413c1977b5450c85cec08339358c57102e4ca464d4a10748`. Approval covers this complete PLAN and its pinned Approved SPEC. This records planning approval only; implementation requires a separate valid implement entry with a new session, cleared context, or explicit same-context consent. No implementation, commit, push, merge, publication, deployment, or hardware operation was performed by this approval record.
