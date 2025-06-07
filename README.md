# Cluster Monitor

## Overview

This project is a Python-based system for gathering, displaying, and managing various system statistics. It is designed to work flexibly across different environments, including Raspberry Pi devices, Docker containers, and remote systems via SSH. The output can be rendered to e-paper displays, the console, or other user-extendable outputs.

---

## Project Structure

```plaintext
.
├── cluster_monitor/                    # Main source code directory
│   ├── renderers/                      # Rendering logic for e-paper, console, etc.
│   │   ├── AbstractRenderer.py         # Base class/interface for display renderers
│   │   ├── ConsoleRenderer.py          # Renderer for the console
│   │   └── ePaper/                     # ePaper-specific rendering components
│   │       ├── ePaperController.py     # Handles ePaper page navigation via GPIO buttons
│   │       └── ePaperRenderer.py       # Renderer for rendering to ePaper displays
│   ├── services/                       # Service modules for data collection
│   │   ├── DockerService.py            # Handles Docker Swarm data collection
│   │   ├── RemoteService.py            # Manages SSH connections for remote monitoring
│   │   └── RpiService.py               # Collects statistics from the Raspberry Pi
│   ├── helpers/                        # Utility helpers
│   │   └── YamlHelper.py               # YAML file loader for configuration
│   ├── __main__.py                     # Entry point for the package
│   ├── Context.py                      # Context class for application configuration/management
│   └── RendererManager.py              # Manager for determining which renderer to use
├── lib/                                # Extra libraries (e.g., ePaper drivers)
│   └── waveshare_epd/                  # E-Paper display driver/library (custom or vendor-provided)
├── resources/                          # Non-code resources
│   ├── Font.ttc                        # TrueType font used for rendering display text
│   └── config.local.yml                # Example of local overrides for configuration
├── tests/                              # Unit tests
├── setup.py                            # Installation/setup script for packaging the project
├── .gitignore                          # Git configuration: files/directories to ignore
└── README.md                           # Project documentation
```

---

## Features

- **Modular Statistic Gathering:**
    - Collect statistics from various sources:
        - **Raspberry Pi statistics**
        - **Docker Swarm statistics** (nodes, services, ports, etc.)
        - **Remote systems** via SSH asynchronously
- **Flexible Rendering Options:**
    - Render system statistics to:
        - E-paper displays (for Raspberry Pi devices)
        - The local console (CLI)
- **Real-Time Updates:**
    - Regular refresh intervals (default: every 5 seconds) to dynamically update displayed information.
- **Dynamic Configuration:**
    - Load configuration files (`config.yml` and `config.local.yml`) to easily manage settings.
- **Extendable Design:**
    - Add new data collectors and renderers by subclassing the provided base classes.

---

## Requirements

### Software Requirements

- Python 3.9+
- Required Python packages:
    - `Pillow`: For rendering images/text to ePaper outputs
    - `gpiozero`: Raspberry Pi GPIO handling for buttons
    - `docker`: API integration for Docker Swarm
    - `natsort`: For sorting Docker services by ports or other metrics
    - `paramiko`: SSH library for communicating with remote systems
    - `PyYAML`: Handling YAML configuration files
    - `numpy`: General-purpose numerical computations
    - `requests`: For REST API requests
    - `six`: Python 2/3 compatibility
- Platform-specific dependencies:
    - **Raspberry Pi:** `RPi.GPIO` and `spidev`
    - **Jetson Nano:** `Jetson.GPIO`
    - **Sunrise X3:** `Hobot.GPIO`

### Hardware Requirements

- **Raspberry Pi** (Tested on Raspberry Pi 4)
- **E-paper display** (Waveshare-compatible, 2.7-inch model tested)
- **GPIO Buttons** for navigation (mapped to GPIO 5, 6, and 13):
    - Button 1 (GPIO 5): Docker Swarm Overview
    - Button 2 (GPIO 6): Service Details Table
    - Button 3 (GPIO 13): Additional Statistics

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<username>/cluster-monitor.git
   cd cluster-monitor
   ```

2. **Set up a Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install platform-specific libraries, if applicable:**
    - For **Raspberry Pi**:
      ```bash
      pip install RPi.GPIO spidev
      ```
    - For **Jetson Nano**:
      ```bash
      pip install Jetson.GPIO
      ```
    - For **Sunrise X3**:
      ```bash
      pip install Hobot.GPIO spidev
      ```

5. **Install the package:**
   ```bash
   python setup.py install
   ```

---

## Configuration

### Base Configuration File (`config.yml`)
- Contains default settings for application behavior.

### Local Overrides (`config.local.yml`)
- Allows you to override base configuration without modifying the default file.

### Example Configuration (`config.yml`):

```yaml
cluster_monitor:
  remote_service:
    ssh:
      user: "username"
      key_path: "/path/to/key"
      command: "docker stats"
```

---

## Usage

### Running the Application

Run the Cluster Monitor application using the desired renderer:

```bash
python -m cluster_monitor --renderer [console|epaper]
```

### Navigation (E-paper Mode)

- **Button 1 (GPIO 5):** Docker Swarm Overview
- **Button 2 (GPIO 6):** Service Details Table
- **Button 3 (GPIO 13):** Additional Statistics

---

## Customization

- **Add New Renderers:**
    - Create new renderer classes by subclassing `AbstractRenderer.py`.
- **Add New Data Collectors:**
    - Extend one of the `services` modules (e.g., `DockerService.py`, `RpiService.py`).
- **Include Additional Resources:**
    - Add fonts, images, or other resources in the `resources/` directory.

---

## Known Updates

### Changes Made in the Recent Update:
- `DockerStats.py` has been renamed to `DockerService.py`. Update imports accordingly.
- Configuration loading now uses a new helper module: `YamlHelper.py`.
- The `setup.py` dependencies include `PyYAML` for configuration management.
- Main entry point has been updated. Run using:
  ```bash
  python -m cluster_monitor
  ```

---

## License

Include licensing and contribution policies here.
```