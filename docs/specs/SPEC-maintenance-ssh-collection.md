# SSH collection maintenance

Status: Approved

## Authority and identity

- Date: 2026-10-16.
- Group: G2, SSH collection; findings M006, M010, M013.
- Origin: the maintenance audit in the parent conversation, followed by the user's request: "create spec plans for every group. Exclude from the ssh group the 002 and 004".
- Research base: `main`, `a692adf875132074c70d69effe2693443da5ec5b`, in `/home/alexbanica/workspace/RpiEPaper`.
- Planning only. No implementation, commit, push, merge, or deployment is authorized. No earlier approved SPEC/PLAN exists in this checkout for this work.
- This is a separate group specification; user approval of this complete document is required before its PLAN is authored.

## Problem and evidence

- M006: `remote_service.py:140-147` identifies a command as busy whenever its lifetime running flag is true and its result map is empty. Completed zero-host or failed-host attempts therefore remain busy and suppress content through `cluster_monitor_service.py:107-110,153-165`.
- M010: hostname updates mutate and close `clients` outside the lock held by polling (`remote_service.py:86-94,114-138`). Result reading and result removal also share mutable state without a consistent snapshot boundary.
- M013: `remote_service.py:78-84` treats any stderr as failure and does not inspect the remote exit status.

Paths above are relative to `cluster_monitor/infrastructure/services`, except the application service and domain entities, whose canonical paths are identified below. These are source-confirmed mechanisms, not evidence of a particular deployed failure.

## Scope and preserved behavior

Owned correction boundaries: `cluster_monitor/infrastructure/services/remote_service.py`, `cluster_monitor/domain/entities/async_command_cache_entity.py`, `cluster_monitor/domain/entities/async_commands_entity.py`, and only the application busy gate if required for the specified result semantics. Maintain the public remote-service interface unless an internal state contract requires a minimal compatible extension.

Preserve configured commands, usernames, key paths, host ordering, polling cadence, command UUID identity, and successful output stripping/decoding. Command failure continues to remove that host's connection and results; normal hostname reconciliation may reconnect it. Do not add stale-result retention or change the existing health aggregation contract.

Explicit exclusions: M002 SSH deadlines, stream-draining/output limits and cancellation bounds; M004 host-key trust policy/provisioning. Existing SSH trust behavior and unbounded command execution remain. No new SSH configuration, parallel host execution, deployment, or live access is included.

## Required behavior

### SSH-1: Initialization and empty results (M006)

Separate worker lifetime, initial collection completion, and result availability. A command is initially busy only until its first collection attempt completes or it is stopped. A completed attempt against zero hosts is completed, not perpetually busy. The same applies when every attempted host fails promptly.

Once initial collection has completed, later recurring attempts must not restore a global loading screen merely because their result map is empty. With ready Docker state and an active HAT, completed failed/empty remote collections must allow local statistics and other content pages to render. Existing error logging remains available; no new error screen is required.

This requirement does not promise completion of an SSH operation that never returns: that is excluded M002.

### SSH-2: Consistent connection and result ownership (M010)

Coordinate connection addition, removal, closure, command use, and service shutdown so a client cannot be removed or closed concurrently with its command execution. Serialize hostname reconciliation and protect the update-in-progress state. An update worker must release its in-progress state even when reconciliation fails.

Closing the service prevents hostname updates from reopening connections or launching additional reconciliation workers. Later hostname-update calls are ignored. Close is idempotent and coordinates any already-started reconciliation worker before considering client cleanup complete. Restarting a closed service instance is not supported; preserve ordinary reconnection while the service remains open.

Expose coherent result snapshots: readers must not iterate a mapping while another thread removes or replaces its entries. Host removal must be reflected consistently across command result collections. Do not introduce lock-order cycles or self-joins. The existing possibility of waiting indefinitely for a nonreturning command remains an explicitly excluded limitation.

### SSH-3: Exit status determines command success (M013)

After command streams complete, collect the remote exit status. Status zero returns stdout even when stderr contains warnings; log nonempty stderr diagnostically. A nonzero or unavailable/invalid exit status is a failed collection even when stderr is empty, with diagnostics identifying the host and status. Preserve per-host failure isolation and current removal/reconnection behavior.

## Acceptance and regression validation

1. Completed zero-host and all-host-failed initial attempts stop being busy. Successful initial results preserve natural host ordering. Later empty attempts do not suppress unrelated content pages.
2. Status zero with stderr preserves stdout and the connection. Nonzero status with empty stderr fails and follows existing host removal behavior. Nonzero status with stderr retains useful diagnostics.
3. Controlled nonhardware operator/smoke checks exercise reconciliation during polling, result reads during host removal, update failure, and shutdown. No concurrent use-after-close, dictionary-iteration failure, stuck update-in-progress state after a completed failure, or lock-order deadlock is permitted.
4. Preserve configured command strings, polling interval, normal stdout formatting, interface consumers, and the unchanged M002/M004 boundaries.
5. Automated tests may be added only for new deterministic domain state logic. Adapter/application behavior is validated with static, syntax, structural, and controlled operator/smoke checks, without creating non-domain automated tests.

## Dependencies, risks, and documentation

G3 owns application resource shutdown; coordinate that service boundary before implementation and integrate SSH cleanup ordering with it. G5 architecture work follows the behavioral groups and must preserve these semantics. No group grants authority to implement another group's findings.

Document completed-empty collection behavior and exit-status handling in README runtime guidance. State that this group does not provide bounded SSH execution or trusted-host verification. Runtime occurrence, real SSH behavior, and target cleanup remain unverified until permitted validation occurs.

## Approval

Approved by the user on 2026-10-16 in the parent conversation with "approve", responding to the presentation of all five complete Proposed specifications at Checkpoint 06. Approval covers this complete specification, including the previously accepted recommendations. It does not approve a PLAN or authorize implementation, commit, push, or deployment.
