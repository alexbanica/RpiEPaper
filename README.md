Project README

## Overview

This project is a Python-based system for gathering, displaying, and managing various system statistics. It is designed to work flexibly across different environments such as Raspberry Pi devices and Docker containers, and supports multiple rendering output options including e-paper displays and consoles.

## Project Structure

```plaintext
.
├── lib/                                # Extra libraries used by the project
│   └── waveshare_epd/                  # E-Paper display driver/library (custom or vendor-provided)
├── resources/                          # Non-code resources
│   └── Font.ttc                        # TrueType font used for rendering display text
├── src/                                # Main source code directory
│   ├── AbstractRenderer.py             # Abstract base class/interface for display renderers
│   ├── ConsoleRenderer.py              # Renderer for displaying stats in the console (CLI)
│   ├── DockerStats.py                  # Utilities for gathering Docker Swarm data (nodes, services, etc.)
│   ├── ePaper.py                       # Abstraction for ePaper hardware, handles page switching via buttons
│   ├── ePaperRenderer.py               # Renderer for outputting stats to an ePaper display
│   ├── RendererManager.py              # Manages which renderer (console/ePaper) to use
│   ├── RemoteConnectionManager.py      # Handles SSH or other remote connections for stats gathering on remote hosts
│   ├── RpiStats.py                     # Gathers stats and info from the local Raspberry Pi device
│   ├── server_status.py                # Entry point script (alternate or CLI wrapper for ServerStatus usage)
│   ├── ServerStatus.py                 # Main app logic: gathers stats, manages rendering, orchestrates everything
│   ├── ServerStatusArgumentParser.py   # Parses command-line arguments for the main application
│   └── __init__.py                     # Package marker for Python
├── setup.py                            # (Not a directory) Installation/setup script for packaging the project
├── .gitignore                          # (Not a directory) Git configuration: files to be ignored in source control
└── README.md   


```

## Features

- **Modular Statistic Gathering:**
    - Supports collecting statistics from Raspberry Pi hardware, Docker containers, and general server environments.
- **Flexible Rendering:**
    - Output system status to e-paper displays, the local console, or potentially other targets.
- **Remote Management:**
    - Capable of initiating connections to remote systems to collect stats.
- **Extendable Design:**
    - Easily add new types of renderers or data collectors by extending the appropriate classes.

## Requirements

### Software Requirements

- Python 3.9.6
- Third-party packages: `numpy`, `paramiko`, `pillow`, `requests`, `six`
- System dependencies for specific renderers (e.g. hardware libraries for e-paper displays)

### Hardware Requirements

- Raspberry Pi (tested on Raspberry Pi 4)
- E-paper display (Waveshare compatible)
- GPIO buttons configuration:
    - Button 1: GPIO 5
    - Button 2: GPIO 6
    - Button 3: GPIO 13

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install numpy paramiko pillow requests six
   ```
4. Additional steps may be necessary for e-paper display support (see documentation for the `lib/waveshare_epd` module)

## Usage

1. Run the ServerStatus script with desired renderer:
   ```bash
   python src/ServerStatus.py --renderer [console|epaper]
   ```

2. Navigation (E-paper display mode):
    - Button 1 (GPIO 5): Docker Swarm Overview
    - Button 2 (GPIO 6): Service Details Table
    - Button 3 (GPIO 13): Additional Statistics

3. Display Features:
    - Automatic updates every 5 seconds
    - ClusterHAT status monitoring
    - Docker Swarm service statistics
    - Remote node monitoring
    - System resource usage

## Customization

- Add new renderers by subclassing `AbstractRenderer.py`
- Enhance statistics sources by expanding modules like `RpiStats.py` or `DockerStats.py`
- Include new resource files (fonts, images) in the `resources/` directory as needed.

## License

Include licensing and contribution policies here if applicable.

---

Feel free to adapt the **Usage** and **Customization** sections once a main entry point or script is clearly defined, or if additional features are added!