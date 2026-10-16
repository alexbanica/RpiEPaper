# Display and monitor lifecycle maintenance

Status: Approved

## Authority and identity

- Date: 2026-10-16.
- Group: G3, display lifecycle; findings M003 and M009.
- Origin: the maintenance audit in the parent conversation and the user's request to create specifications and plans for every group, excluding only M002/M004 from SSH.
- Research base: `main`, `a692adf875132074c70d69effe2693443da5ec5b`, in `/home/alexbanica/workspace/RpiEPaper`.
- Planning only; no implementation, commit, push, merge, or deployment authorization. No earlier approved SPEC/PLAN exists in this checkout for this work.
- User approval of this complete document is required before authoring its PLAN.

## Problem and evidence

- M003: `cluster_monitor/presentation/renderers/epapers/epaper_renderer.py:41-55` starts a periodic worker that sleeps then refreshes unconditionally. `close():205-210` neither wakes nor joins it before panel shutdown. `renderer_manager.py:21-26` subsequently releases hardware. Periodic operations can overlap drawing or access hardware after cleanup.
- M009: `cluster_monitor/application/services/runtime_service.py:45-56` creates Docker and remote resources unconditionally. `cluster_monitor_service.py:178-185` closes them only when a fresh HAT status check reports on. Off or failed HAT status therefore skips cleanup of owned resources.

These are confirmed source mechanisms; physical failure or deployed shutdown behavior was not observed.

## Scope, definitions, and preserved behavior

Owned boundaries: periodic ePaper refresh and renderer shutdown in `epaper_renderer.py`, renderer ownership/cleanup in `renderer_manager.py`, and monitor teardown in `cluster_monitor_service.py`. Controller lifecycle may be adjusted only as necessary to coordinate these existing resources. Preserve display geometry, fonts, pages, buttons, scrolling, refresh configuration, normal rendering, and CLI behavior.

A frame transaction consists of clearing/preparing the frame, drawing its contents, and applying it to the panel. A hard refresh is an exclusive panel operation. Shutdown begins when the owner requests closure; cleanup is complete after all applicable owned resources have received teardown and any teardown errors have been reported.

Preserve Raspberry Pi GPIO discovery and the shared process-lifetime gpiozero factory. Do not add alternate GPIO backends, close the shared factory, change native vendor code, redesign drawing geometry, or deploy to hardware. M002 SSH bounds remain excluded; no bounded shutdown guarantee is made when an existing external operation never returns.

## Required behavior

### LIFE-1: Exclusive panel/frame lifecycle (M003)

Periodic hard refresh must not overlap a frame transaction, page-change hard refresh, or shutdown. Coordinate image/drawing state as well as panel calls so periodic reset cannot erase or replace an in-progress frame. Preserve the configured refresh interval; a nonpositive interval disables periodic initialization.

Shutdown must signal and wake a waiting periodic worker, prevent any new refresh from starting, allow an already active operation to finish, and join the worker before final panel clear/sleep and hardware cleanup. A sleeping worker must not wait out the full configured refresh interval before it can terminate. No EPD operation may occur after hardware cleanup.

Initialization failure must not leave a newly started periodic worker accessing partially constructed or released state. Close remains safe for repeated calls; teardown cannot join its own thread or deadlock against frame ownership. These requirements do not add deadlines to vendor hardware calls.

### LIFE-2: Cleanup follows ownership (M009)

The monitor must attempt cleanup of every resource it created, independently of current HAT state or failure to read that state. Stop monitor execution, attempt alert reset, close the renderer, supervisor, Docker collection, and remote collection. A failure in one cleanup action must not prevent attempts on the remaining owned resources.

Keep cleanup errors observable: record each failure, complete the remaining teardown attempts, then preserve a failure outcome for the initiating caller rather than falsely reporting clean shutdown. Reentrant or repeated shutdown must not start overlapping teardown or repeat successful resource cleanup. Do not add new resource creation during teardown.

Coordinate application-level closure with G2's remote client/worker ownership. Do not compensate for excluded SSH bounds by silently abandoning live workers or claiming a bounded stop.

## Acceptance and regression validation

1. A periodic wake during drawing waits for the current frame transaction. Page-change and periodic refresh cannot operate on the panel concurrently.
2. Close during the periodic wait wakes/stops the worker promptly without a final refresh. Close during an active refresh waits for it before final panel shutdown. No calls follow hardware cleanup.
3. Repeated/reentrant close and construction failure do not create duplicate cleanup, self-join, or partially initialized worker access.
4. With HAT on, off, or status-read failure, each created Docker/remote/supervisor/renderer resource receives cleanup. An injected earlier cleanup failure does not suppress later cleanup attempts and remains observable afterward.
5. Preserve console operation without Waveshare imports and GPIO discovery, all display pages/button behavior, configured periodic disablement, and process-lifetime factory ownership.
6. Use static/syntax/structural checks and controlled nonhardware lifecycle/operator smoke checks. Do not create automated presentation/application/infrastructure tests. A permitted target smoke check is needed to establish actual panel output and button operation; static evidence alone cannot establish that result.

## Dependencies, risks, and documentation

G2 owns remote lifecycle internals; implementation ownership for the application close boundary stays with G3. G4 owns local subprocess timeouts and alert-state correctness, which may affect shutdown timing but do not change G3's unconditional cleanup requirement. G5 composition changes follow these groups and must preserve their resource ownership.

Document resource teardown, periodic refresh serialization, and remaining unbounded external-operation limitations in README. Main retains cross-group integration and final acceptance. No implementation plan, worktree, delivery branch, or live effect is authorized by this Proposed specification.

## Approval

Approved by the user on 2026-10-16 in the parent conversation with "approve", responding to the presentation of all five complete Proposed specifications at Checkpoint 06. Approval covers this complete specification, including the previously accepted recommendations. It does not approve a PLAN or authorize implementation, commit, push, or deployment.
