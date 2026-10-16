# Docker status and application dependency maintenance

Status: Approved

## Authority and identity

- Date: 2026-10-16; group G5; findings M014, M015, M017, M018.
- Origin: the parent maintenance audit and user request for every group's SPEC/PLAN, excluding M002/M004 from SSH.
- Behavior decision: on 2026-10-16, "use recommendations" selected `running/-` for global-service replica display.
- Research base: `main`, `a692adf875132074c70d69effe2693443da5ec5b`; invoking checkout `/home/alexbanica/workspace/RpiEPaper`.
- Planning only; no implementation, commit, push, merge, deployment, or cluster mutation authorization. No approved predecessor SPEC/PLAN exists here for this scope. PLAN authoring follows approval of this complete SPEC.

## Problem and evidence

- M014: `cluster_monitor/infrastructure/services/docker_service.py:78-81,137-140` queries the same service tasks once for running counts and again for node resolution.
- M015: `cluster_monitor/application/services/runtime_service.py:6-10` imports concrete infrastructure and `cluster_monitor_service.py:8` imports presentation management, contrary to inward dependency rules.
- M017: `cluster_monitor/domain/entities/docker_status_entity.py:25-35` treats a registry port as a tag for an untagged image.
- M018: `docker_service.py:94` fabricates a desired count of five when replicated configuration is absent; `DockerStatusEntity.to_dict():61-62` still renders this denominator for global services.

## Scope and preserved contracts

Own Docker task/status extraction, deterministic domain status formatting, permitted domain tests, application dependency injection, and the outer runtime composition/entrypoint wiring needed to remove application imports of infrastructure/presentation. Extend existing inward-facing interfaces only where necessary; follow Interface/Abstract naming conventions and canonical module paths. Update README architecture/status documentation.

Preserve CLI flags/entrypoints, console and monitor-client hardware isolation, logging/configuration sequence, early Raspberry Pi GPIO discovery, packaged resources, polling cadence, service ordering, node mapping, ports/truncation, replicated-service counts, global deployment label, signals, and the other groups' accepted lifecycle/result behavior.

Do not change Docker task selection semantics, add retries/caches across refreshes, infer global placement from all cluster nodes, redesign the UI, add legacy module wrappers, or broaden into a general domain/concurrency rewrite. SSH M002/M004 remain excluded.

## Required behavior

### DOCKER-1: One task snapshot per service extraction (M014)

Within one service-details extraction, fetch each service's tasks once and use that same collection for both running replica count and node placement. Preserve existing filtering, order, and error propagation. A later extraction may fetch fresh tasks; no cross-cycle caching is introduced.

### DOCKER-2: Inward application dependencies (M015)

Application orchestration must not import concrete infrastructure adapters or presentation managers/renderers. Compose these concrete objects at an outer presentation/composition boundary and inject the domain-facing service/renderer contracts required by the application. Do not move adapter behavior into application or domain merely to remove imports.

Retain one clear owner for created resources and preserve startup ordering: runtime logging/configuration, conditional ePaper GPIO discovery before Waveshare imports, adapter/renderer composition, and monitoring. Monitor-client mode must still bypass full monitor/Docker/ePaper setup; console mode must not import Waveshare or initialize GPIO discovery. Existing entrypoints must resolve directly to canonical modules without compatibility wrappers.

Integrate this dependency refactoring after G2-G4 behavior has been established. It must preserve G3 cleanup ownership and frame coordination, G2 SSH collection semantics, and G4 local-command/configuration behavior. It grants no authority to alter earlier approved artifacts.

### DOCKER-3: Image tags follow the final path component (M017)

Strip an optional image digest before identifying an explicit tag. Only a colon after the final slash separates an image tag; a registry port before that slash is not a tag. Preserve `-` when no explicit tag exists, preserve tagged/digest-tagged values, and preserve the existing ten-character display truncation.

### DOCKER-4: Global replica targets are unavailable (M018)

Render a global service's replica field as `<running>/-`, including `0/-` when no task is running. Preserve the `global` deployment label. Do not manufacture or derive a desired target count. The adapter/domain contract must represent absence of a global desired count rather than retaining a fabricated numeric five hidden behind formatting.

Replicated services retain `<running>/<configured desired>`, including an explicit desired zero. Non-global modes outside the existing supported representation are not newly specified by this change; do not introduce new mode support or placement assumptions.

## Acceptance and regression validation

1. One extraction makes one task request per service; running counts and nodes come from that snapshot. Subsequent calls refresh normally.
2. Deterministic domain tests cover tagged/untagged images, registry ports, digests, truncation, global `running/-` including zero, and unchanged replicated values/ports formatting.
3. Static import/dependency inspection establishes that application code does not import infrastructure or presentation and domain does not acquire those dependencies. Concrete composition remains outside application/domain.
4. Structural and controlled smoke checks preserve CLI/monitor-client/console/ePaper composition, configuration, discovery-before-Waveshare ordering, signal wiring, and lifecycle semantics from G2-G4. Do not execute hardware discovery or live cluster commands without separately permitted target checks.
5. Add/maintain automated tests only for deterministic domain logic. Validate adapters/composition with static, syntax, structural, and operator/smoke checks rather than non-domain automated tests.

## Dependencies, risks, and documentation

G1 is independent. The Docker/domain formatting work is independent of G2-G4 source changes; the M015 composition integration follows G2, G3, and G4 and is serialized against their source ownership. G3 retains application cleanup/frame behavior ownership until its work is integrated; G5 then owns the composition refactor, preserving verified predecessor behavior.

README must describe canonical composition responsibilities, image-tag parsing, and global `running/-` display. Architecture work has the broadest regression boundary and requires explicit dependency/startup/lifecycle checks in the future PLAN. Static/domain evidence does not establish actual Docker availability or display success.

## Approval

Approved by the user on 2026-10-16 in the parent conversation with "approve", responding to the presentation of all five complete Proposed specifications at Checkpoint 06. Approval covers this complete specification, including the previously accepted recommendations. It does not approve a PLAN or authorize implementation, commit, push, or deployment.
