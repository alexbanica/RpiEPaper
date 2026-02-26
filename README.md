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
Default config file path: `resources/config.yml`

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
      command_rpi_status: "PYTHONPATH=/mnt/data/ePaperHat python3 -m cluster_monitor -mc"
      command_rpi_hdd_status: "PYTHONPATH=/mnt/data/ePaperHat python3 -m cluster_monitor -mc-hdd"
```
