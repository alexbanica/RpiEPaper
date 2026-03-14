# Spec: Storage Temperature in Disk Usage Output

## Purpose
Expose storage temperature for the storage devices backing the disk usage entries shown by the monitor, for both the main Raspberry Pi and attached Raspberry Pi Zero nodes.

## Definitions
- Displayed disk usage entry: a `DiskUsageInfoEntity` returned by `RpiService.get_disk_usages(...)`.
- Backing storage device: the base block device that provides the filesystem for a displayed disk usage entry.
- Base block device: a device path such as `/dev/nvme0n1` or `/dev/sda`, not a partition path such as `/dev/nvme0n1p1` or `/dev/sda1`.
- Storage temperature: the temperature reading for a backing storage device, rendered in Celsius when available.
- Compact disk label: the final path segment of the mount path used for rendering, with `/` preserved as `/`.

## Behavior
1. `RpiService` exposes a method that accepts a storage device identifier and returns that device's temperature.
2. `RpiService` exposes a separate method that discovers the storage devices backing the disk usage entries currently being displayed.
3. Discovery is scoped only to the devices behind the disk usage entries returned for rendering, not every block device visible on the system.
4. Partition-backed mount points are normalized to their base block device before temperature lookup.
5. Disk usage rendering is enriched with storage temperature when available.
6. If a storage temperature cannot be determined for a displayed disk entry, the rendered output includes `T:N/A`.
7. The monitor client HDD output uses the same disk usage rendering format as the main node, so attached Raspberry Pi Zero nodes return temperature-enriched disk rows through `MonitorClientService`.
8. The page that lists disk usages for the main node and attached nodes displays the compact disk label instead of the full mount path to reduce line width pressure on the display.
9. Compact disk labels are derived deterministically:
- `/` remains `/`
- `/mnt/data` renders as `data`
- `/mnt/ssd_data` renders as `ssd_data`
- `/mnt/hdd_data` renders as `hdd_data`
10. Existing disk usage collection remains functional even when no storage temperature is available on a node.

## Invariants
1. Existing CLI compatibility remains unchanged, including `-mc` and `-mc-hdd`.
2. Existing remote HDD stats collection remains text-based through the monitor client flow.
3. No HTTP API, OpenAPI, or `.http` artifacts are introduced.
4. Disk usage output still includes usage size and usage percentage for every displayed entry.

## Constraints
1. Temperature detection logic lives in `RpiService`.
2. Temperature detection and storage-device discovery are separate methods.
3. The display format must remain compact enough for the existing disk usage page layout.
4. Unsupported devices must not fail the full disk usage rendering flow.

## Assumptions
1. A displayed disk usage entry can be mapped to a backing block device on the local node.
2. Storage temperature support may differ by device type and host capabilities.
3. Returning an unavailable marker is acceptable when a backing device does not expose temperature.

## Acceptance Criteria
1. `RpiServiceInterface` defines separate methods for storage-device discovery and per-device temperature lookup.
2. `RpiService` resolves backing base devices for the displayed disk usage entries and attempts temperature lookup per device.
3. Disk usage render output includes storage temperature when available and `T:N/A` when unavailable.
4. The rendered disk label is compact and does not use the full mount path except for `/`.
5. `MonitorClientService` emits the same temperature-enriched disk usage rows used by the main node display flow.
6. Tests cover:
- backing-device normalization for partitioned devices
- compact disk label rendering
- `T:N/A` fallback behavior
- monitor-client disk output compatibility
