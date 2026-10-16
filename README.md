# Cluster Monitor

Python-based cluster monitor for Raspberry Pi/ePaper, Docker Swarm, and remote SSH nodes.

## Runtime Compatibility
This rewrite preserves:
- CLI flags: `-r`, `-p`, `-mc`, `-mc-hdd`
- YAML config structure under `cluster_monitor.*`
- Main runtime entrypoint: `python -m cluster_monitor`

## Architecture
The codebase uses a DDD/onion layout:
- `cluster_monitor/domain`: entities and interfaces
- `cluster_monitor/application`: orchestration services
- `cluster_monitor/infrastructure`: adapters and parsers
- `cluster_monitor/presentation`: renderers and controllers
- `cluster_monitor/shared`: constants and shared values

## Installation

1. Create virtualenv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install base dependencies:
```bash
pip install -r requirements.txt
```

3. Install platform-specific extras:
- Raspberry Pi:
```bash
pip install -r requirements/rpi.txt
```
- Jetson:
```bash
pip install -r requirements/jetson.txt
```
- Sunrise X3:
```bash
pip install -r requirements/sunrise_x3.txt
```

4. Install package:
```bash
pip install .
```

For a Raspberry Pi installation from this source checkout, the package extra
installs the Raspberry Pi dependencies together:

```bash
pip install '.[rpi]'
```

For an already published release available from the established package index,
install its Raspberry Pi extra with an exact version:

```bash
python -m pip install \
  --index-url "https://pypi.alexlab.nl/simple/" \
  "cluster-monitor[rpi]==<version>"
```

An existing virtual environment with `include-system-site-packages = true` can
also use `lgpio>=0.2.2.0` supplied by system Python, provided the active
environment has the other runtime dependencies it needs. The explicit
Raspberry Pi extra is the supported installation path for declaring all
platform dependencies.

### Raspberry Pi ePaper GPIO discovery

Before importing Waveshare modules for Raspberry Pi ePaper, startup discovers
the GPIO controller from read-only chip and line metadata and selects one
explicit `gpiozero` `LGPIOFactory`. A controller matches only when it exposes
all eight required BCM lines at the corresponding offsets: 5, 6, 13, 17, 18,
19, 24, and 25, each named `GPIO<N>`. The match must be unique; chip numbers,
enumeration order, and controller labels alone do not identify the controller.
Metadata handles are closed, and discovery does not claim GPIO lines.

For permission errors, retain the existing `sudo` invocation and device
permissions, then check whether that runtime user can access the
`/dev/gpiochip*` devices. Make sure the active environment provides
`lgpio>=0.2.2.0`. Unset `GPIOZERO_PIN_FACTORY` or set it exactly to `lgpio`;
other explicit values are reported as conflicts. Startup fails with device and
backend diagnostics when metadata inspection is inconclusive, no controller or
multiple controllers match, required dependencies/backend are unavailable, or
the factory selection conflicts. An existing factory is reused only when it
is an `LGPIOFactory` for the discovered chip. There is no fixed-chip or
alternate-backend fallback for this Raspberry Pi ePaper path. The shared
factory remains under gpiozero's process-lifetime cleanup.

If startup reports that `LGPIOFactory` opened or reported a different chip,
install a gpiozero version that honors the explicit `chip` argument. Startup
checks the new factory's reported chip. A mismatch stops initialization and
closes that factory without registering it as gpiozero's process-wide factory
or importing Waveshare modules.

The native read-only check on Pi51 on 2026-10-12 selected `/dev/gpiochip15`
(`pinctrl-rp1`) and verified all eight line-name/offset mappings. Chip 15 is an
observation from that check, not a stable configuration value. Repeated
configuration reused the same `LGPIOFactory(chip=15)` instance; the isolated
check closed and cleared its factory afterward. It made no GPIO line claims.
This check does not validate physical display output, button operation, a full
monitor run, detached startup, or deployment. The change preserves the existing
sudo invocation, wiring, SPI settings, and YAML configuration; those do not need
to change for discovery.

## Forgejo publication and routed package installation

### GitHub checks and branch rules

- Pull-request checks for `main`: `.github/workflows/ci.yml`
  - `lint` (runs Ruff on `cluster_monitor`, `scripts`, and `tests`)
  - `test (3.12)` (runs `python -m unittest discover -s tests` on Python 3.12)
- Push checks for `main`: `lint` and `test (3.12)`.
- Configure these checks manually as required checks in branch protection. The repository
  setup toolchain does not configure branch protection automatically.

### Release tags and version mapping

The publish workflow accepts only:

- Stable tags: `X.Y.Z` where X, Y, and Z are non-negative integers without leading zeroes (for example `1.0.0`)
- Beta tags: `X.Y.Z-betaN` where N is a positive integer without leading zeroes
  (for example `1.0.0-beta4`)

Leading `v` is intentionally rejected (`v1.0.0` is invalid).
Beta tags are normalized to PEP 440 in distribution metadata and installs:

- Tag `1.0.0-beta4` → canonical version `1.0.0b4`

Exact install forms:

```bash
python -m pip install \
  --index-url "https://pypi.alexlab.nl/simple/" \
  "cluster-monitor==1.0.0"

python -m pip install \
  --index-url "https://pypi.alexlab.nl/simple/" \
  "cluster-monitor==1.0.0b4"
```

Use `https://pypi.alexlab.nl/simple/` as the sole install and download index.
It routes `cluster-monitor` to its Forgejo package source and resolves public
third-party dependencies through the cluster cache. Publication remains a
direct Forgejo upload.

The publish workflow triggers on stable and beta tag globs matching
`[0-9]*.[0-9]*.[0-9]*` and `[0-9]*.[0-9]*.[0-9]*-beta[1-9][0-9]*`, then performs
strict exact tag validation before any build or upload step.

The repository uses the shared Python-project workflow layout
`.github/workflows/ci.yml` and `.github/workflows/publish.yml`. External actions
are pinned to immutable commit SHAs, checkout credentials are not persisted, CI
runs cancel superseded executions for the same ref, publication runs do not
cancel in progress, and Dependabot groups weekly GitHub Actions updates.

### Forgejo package endpoints

- Upload endpoint: `https://forgejo.alexlab.nl/api/packages/public/pypi`
- Routed install index: `https://pypi.alexlab.nl/simple/`

### GitHub credentials

Set:

- Repository secret: `FORGEJO_PACKAGE_USERNAME`
- Repository secret: `FORGEJO_PACKAGE_TOKEN`

Only the publish upload step receives these values. They are intentionally not used for lint,
tests, build, or anonymous verification steps.

### Release artifacts and native libraries

The workflow publishes exactly three artifacts for each release version:

- `cluster_monitor-<version>.tar.gz`
- `cluster_monitor-<version>-py3-none-linux_armv7l.whl`
- `cluster_monitor-<version>-py3-none-linux_aarch64.whl`

There is no universal wheel.

All artifacts include these required Waveshare files:

- `waveshare_epd/DEV_Config_32.so`
- `waveshare_epd/DEV_Config_64.so`
- `waveshare_epd/sysfs_gpio.so`
- `waveshare_epd/sysfs_software_spi.so`

The release process is immutable per version: an existing package version in Forgejo is not overwritten.

### Pre-upload validation and anonymous post-publish verification

Before upload, the publisher validates the exact stable or beta release version,
the three expected archives, distribution metadata, runtime version, package
resources, native-library bytes and ELF contracts, wheel tags and RECORD files.
Twine validation also runs before the upload boundary. A local validation error
prevents upload. The builder resolves the selected output directory once and
preflights all its entries before deleting anything: only existing regular,
nonsymlink artifacts named for the requested version may be replaced. Other
files, other-version artifacts, symlinks, directories and special entries cause
preflight failure with existing contents preserved. This does not promise to
restore old expected artifacts if a subsequent build fails.

To verify one artifact against the requested release tag, pass both options;
the tag selects the canonical expected version without changing checkout
metadata or building an artifact:

```bash
python -m scripts.package_artifacts \
  --verify dist/cluster_monitor-1.2.3b4-py3-none-linux_aarch64.whl \
  --release-tag 1.2.3-beta4
```

Without `--release-tag`, verification uses the version in the checkout.

Local archive validation establishes those checks on the selected files; it does
not establish that Forgejo accepted or serves them. After upload, the workflow
performs the credential-free, dependency-resolving install documented above,
then checks both published platform wheels independently from the routed index:

```bash
python -m pip install "cluster-monitor==<version>" --no-deps \
  --index-url "https://pypi.alexlab.nl/simple/" \
  --platform linux_armv7l --only-binary=:all: --target /tmp/armv7-verify

python -m pip install "cluster-monitor==<version>" --no-deps \
  --index-url "https://pypi.alexlab.nl/simple/" \
  --platform linux_aarch64 --only-binary=:all: --target /tmp/aarch64-verify
```

Replace `<version>` with either `X.Y.Z` or `X.Y.ZbN`.

These anonymous checks establish that the routed index resolves the uploaded
package and that both platform wheels install with the expected packaged
resources and runtime version. They do not prove native execution or physical
display behavior on target hardware.

### Artifact and verification boundary

- Local archive checks validate the exact artifact set, distribution and runtime
  versions, `.so` and package-resource contents and byte identity, platform
  metadata, and wheel RECORD integrity before upload.
- The anonymous install verification confirms package resolution and packaged bytes for both
  platform wheels.
- It does not replace runtime validation on Raspberry Pi, Jetson, or Sunrise X3 hardware.

### Current verification status

The workflows and release checks above are configured, but repository-local
evidence does not establish a current successful hosted GitHub Actions publish,
live Forgejo upload and anonymous target-platform install, required branch
protection, or native execution on Raspberry Pi/ePaper, Jetson, or Sunrise X3
hardware. Treat those as pending operational verification. Static archive and
byte checks do not prove that the packaged native libraries load or that display,
SSH, Docker, sensor, and renderer integrations work on target hardware.
For this delivery, the user explicitly instructed: “Defer physical validation for
this delivery.” No physical display or button success was established.

## Usage

Run main monitor:
```bash
python -m cluster_monitor --renderer epaper
```

Run monitor client mode:
```bash
python -m cluster_monitor -mc
python -m cluster_monitor -mc-hdd
```

## Runtime behavior and operational limits

`RuntimeController` is the outer composition point: it loads configuration,
performs ePaper GPIO discovery before Waveshare imports when needed, creates
the concrete adapters and renderer, then injects their domain-facing contracts
into application orchestration. It owns partially created resources if startup
composition fails; after monitor construction, the monitor owns normal cleanup.
Monitor-client mode bypasses the full monitor, Docker and ePaper setup. Console
mode does not import Waveshare hardware or discover GPIO.

Remote collection treats a completed first poll with no hosts or no results as
complete, so an empty result does not keep the display on a loading screen.
Remote command exit status determines success: status zero keeps stdout even
when stderr contains a warning; nonzero, missing or invalid status is a
per-host failure. Client and result updates use coordinated ownership and
readers receive stable naturally sorted snapshots. SSH command execution and
stream reads remain unbounded, and the existing SSH host-key policy remains in
effect; no bounded shutdown or trusted-host verification is implied.

Local `ifconfig` and `clusterhat` commands have a 10-second deadline. On
timeout, the child is killed and reaped and its pipes are closed. This applies
separately to status, each alert change and each restart off/on command; the
restart-on command is skipped if its off command fails. Alert state advances
only after a successful command, so a failed transition is retried next time.
Unavailable or malformed temperature renders as `T: N/A`. IP selection uses
IPv4 from the exact `eth0` block first, then exact `wlan0`, otherwise `N/A`.

Sparse external YAML overrides preserve unspecified effective renderer and
supervisor values as well as SSH settings. Packaged defaults load first, then
the established external files; `CLUSTER_MONITOR_CONFIG_FILE` selects one exact
final override and still fails if that file is missing.

ePaper frame drawing, page refresh and periodic hard refresh are serialized.
Closing wakes and joins the periodic worker before final panel cleanup. Monitor
shutdown attempts owned renderer, supervisor, Docker and remote cleanup even if
the HAT is off or an earlier cleanup step fails; errors remain observable.
Existing remote SSH calls, vendor display operations and other external calls
can still block, so overall shutdown is not bounded.

Docker service details use one task snapshot per service extraction. Image tags
are taken from the final image path component after any digest is removed, so a
registry port is not mistaken for a tag. Global services show running replicas
as `running/-` (including `0/-`); replicated services show their configured
target.

## Configuration

The installed package always loads its bundled default configuration from
`cluster_monitor/resources/config.yml`. Set `CLUSTER_MONITOR_CONFIG_FILE` to an
exact external YAML file that should be loaded afterward as the final override:

```bash
CLUSTER_MONITOR_CONFIG_FILE=/mnt/data/ePaperHat/resources/config.local.yml \
  /mnt/data/.venv/bin/python -m cluster_monitor --renderer epaper
```

When the variable is unset, the runtime checks `./resources` for the established
`config.yaml`, `config.yml`, `config.local.yaml`, and `config.local.yml` files,
preserving source-checkout behavior. An explicitly configured path must exist;
otherwise startup fails instead of silently using a different configuration.
Keep deployment-specific values in the external file; local configuration is
not included in published packages.

Example:
```yaml
cluster_monitor:
  supervisor:
    docker_node_down_threshold_sec: 30
  renderer:
    init_interval_sec: 300
    display_update_interval_sec: 5
  remote_service:
    ssh:
      user: ''
      key_path: ''
      command_rpi_status: "/mnt/data/.venv/bin/python -m cluster_monitor -mc"
      command_rpi_hdd_status: "/mnt/data/.venv/bin/python -m cluster_monitor -mc-hdd"
```

### Raspberry Pi 5 with Python 3.13

Expose system Python packages to the existing virtual environment:

```bash
sed -i \
  's/^include-system-site-packages = false$/include-system-site-packages = true/' \
  ~/.venv/pyvenv.cfg
```
