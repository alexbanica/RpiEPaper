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

## Forgejo Python package publishing

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
  --index-url "https://forgejo.alexlab.nl/api/packages/public/pypi/simple" \
  --extra-index-url "https://pypi.org/simple" \
  "cluster-monitor==1.0.0"

python -m pip install \
  --index-url "https://forgejo.alexlab.nl/api/packages/public/pypi/simple" \
  --extra-index-url "https://pypi.org/simple" \
  "cluster-monitor==1.0.0b4"
```

Forgejo supplies `cluster-monitor`; the additional public PyPI index supplies
third-party dependencies that are not published in Forgejo.

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
- Simple index: `https://forgejo.alexlab.nl/api/packages/public/pypi/simple`

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

### Anonymous post-publish verification

The publish workflow first performs the same credential-free,
dependency-resolving install documented above. It then checks both published
platform wheels independently from the public simple index:

```bash
python -m pip install "cluster-monitor==<version>" --no-deps \
  --index-url "https://forgejo.alexlab.nl/api/packages/public/pypi/simple" \
  --platform linux_armv7l --only-binary=:all: --target /tmp/armv7-verify

python -m pip install "cluster-monitor==<version>" --no-deps \
  --index-url "https://forgejo.alexlab.nl/api/packages/public/pypi/simple" \
  --platform linux_aarch64 --only-binary=:all: --target /tmp/aarch64-verify
```

Replace `<version>` with either `X.Y.Z` or `X.Y.ZbN`.

### Artifact and verification boundary

- Static checks validate check tags, artifact set, `.so` inclusion, and byte identity.
- The anonymous install verification confirms package resolution and packaged bytes for both
  platform wheels.
- It does not replace runtime validation on Raspberry Pi, Jetson, or Sunrise X3 hardware.

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
