# Local monitoring and configuration maintenance

Status: Approved

## Authority and identity

- Date: 2026-10-16; group G4; findings M005, M007, M008, M016, M019.
- Origin: the parent maintenance audit and the user's request for SPEC/PLAN pairs for every group with M002/M004 excluded from SSH.
- Behavior decision: the user's "use recommendations" on 2026-10-16 selected a 10-second deadline per local subprocess, followed by termination and reaping on timeout; restart off/on commands have separate deadlines. This does not authorize SSH execution bounds.
- Research base: `main`, `a692adf875132074c70d69effe2693443da5ec5b`; invoking checkout `/home/alexbanica/workspace/RpiEPaper`.
- Planning only. No implementation, hardware action, node restart, deployment, commit, or push authority. No earlier approved SPEC/PLAN exists here for this scope. The PLAN requires separate SPEC approval first.

## Problem and evidence

- M005: `cluster_monitor/infrastructure/services/rpi_service.py:55-60,160-168` returns a string on thermal failure, then formats it as a float.
- M007: `cluster_monitor/infrastructure/parsers/yaml_config_parser.py:25-40,59-66` loads overrides but resets omitted renderer/supervisor fields to literals. An SSH-only override changes packaged supervisor threshold 30 to 60 seconds.
- M008: `rpi_service.py:204-213` updates cached alert state before the command succeeds and suppresses subsequent identical retries after failure.
- M016: `rpi_service.py:36-42` matches IP addresses across interface boundaries with DOTALL.
- M019: local status, alert, restart, and IP commands have no subprocess deadline (`rpi_service.py:36-38,117-122,190-213`).

## Scope and preserved behavior

Own the RPi service, YAML parser, and only required domain-facing contract annotations. Preserve commands as argument lists without a shell, configured SSH commands/credentials/trust, normal numeric statistics formatting, interface preference `eth0` then `wlan0`, restart host selection and two-second off/on gap, disk behavior, HAT health policy, YAML filenames and external-file precedence, packaged defaults, and CLI modes.

Do not add configuration keys, change supervisor restart selection/cooldown, add network address discovery mechanisms, alter hardware wiring/backend selection, change SSH execution, or execute any HAT/node command as part of planning.

## Required behavior

### LOCAL-1: Renderable temperature fallback (M005)

Unavailable, unreadable, or malformed thermal input must produce the statistics field `T: N/A`, without numeric formatting failure, duplicated `T:` prefix, or a degree suffix implying a measured value. Preserve normal numeric temperature precision and the rest of the statistics line, including fan suffix. Both monitor-client and full-monitor consumers receive a usable line. A minimal rendering correction may preserve the existing collection return contract rather than introducing unnecessary interface changes.

### LOCAL-2: Partial overrides preserve effective values (M007)

An omitted renderer or supervisor key preserves the current effective context value, consistently with SSH keys. An explicitly supplied key replaces only that key. Apply packaged defaults first and external files in their established order; an explicitly selected environment path remains the exact final override and retains fail-on-missing behavior.

An SSH-only override must preserve the packaged threshold of 30 seconds and renderer settings. Later sparse files must preserve explicit earlier settings. This work does not redesign schema validation, null/type handling, or explicit-value interpretation.

### LOCAL-3: Alert cache reflects successful transitions (M008)

Update cached alert state only after a successful command. Command failure or timeout leaves the prior confirmed state unchanged and remains observable using the existing failure path. A subsequent identical requested transition must retry. An already confirmed state continues to suppress redundant commands. Preserve initial cache behavior; do not add an unsolicited startup alert command.

### LOCAL-4: Parse IP addresses within exact interface blocks (M016)

Match exact interface names, not suffixes of other names. Select an IPv4 address only from that interface's own output block. Prefer `eth0` when it has IPv4, otherwise `wlan0`; if neither has IPv4, return `N/A`. Ignore intervening Docker/bridge/virtual interfaces and IPv6-only data. Preserve failure fallback and the existing `ifconfig` collection mechanism.

### LOCAL-5: Bound local subprocess execution (M019)

Each existing `ifconfig` or `clusterhat` subprocess has a 10-second execution deadline. On timeout terminate the child and reap it, releasing its pipes/resources; avoid an unbounded cleanup wait caused by the subprocess context manager. Do not leave the command executing in the background after reporting timeout. This is not a hard real-time guarantee for operating-system process creation or scheduling.

Apply the deadline separately to `clusterhat status`, each alert transition, and each restart off/on command. Preserve existing failure behavior: status failure logs and returns the existing off/unavailable status entity; IP failure returns `N/A`; alert failure remains an error and does not advance its cache; restart failure logs and stops that host's current restart sequence. Do not issue the on step after a failed/timed-out off step. Keep other hosts' existing restart isolation.

No output cap or SSH execution timeout is introduced. G3 cannot claim globally bounded shutdown merely because these local commands are bounded.

## Acceptance and validation

1. Numeric thermal values retain normal formatting; missing/malformed input renders `T: N/A` in both consumers without an exception.
2. Packaged-only, SSH-only, renderer-only, and layered sparse YAML preserve omitted values; explicit settings and exact environment-file selection retain precedence.
3. Failed/timed-out alert transitions are retried on the next identical request; confirmed states remain deduplicated.
4. IP checks cover Ethernet, Wi-Fi fallback, no IPv4, IPv6-only blocks, misleading names, and an unrelated interface between Ethernet and Wi-Fi.
5. Controlled nonhardware subprocess checks establish timeout, child termination/reaping, closed resources, preserved fallback/exception behavior, and separate restart deadlines. These checks must not execute real HAT/restart commands.
6. No non-domain automated tests are created or maintained. Use syntax/static/structural, controlled smoke/operator checks, and existing permitted domain tests. Hardware readings, alerts, or real restart success require separately permitted target evidence.

## Dependencies, risks, and documentation

G3 owns application teardown; it must preserve attempts on remaining resources after an alert error. G5 architecture changes follow the behavioral groups and retain these semantics. G2's excluded SSH bounds and trust policy remain unchanged.

Document partial-override semantics, temperature fallback, exact-interface IP preference, and the local 10-second timeout/reaping policy in README. A local command that previously took more than 10 seconds will now fail through its defined failure path; that is the accepted behavior change. No live failure frequency or hardware success is claimed.

## Approval

Approved by the user on 2026-10-16 in the parent conversation with "approve", responding to the presentation of all five complete Proposed specifications at Checkpoint 06. Approval covers this complete specification, including the previously accepted recommendations. It does not approve a PLAN or authorize implementation, commit, push, or deployment.
