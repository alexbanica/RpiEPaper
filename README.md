Project README

## Overview

This project is a Python-based system for gathering, displaying, and managing various system statistics. It is designed to work flexibly across different environments such as Raspberry Pi devices and Docker containers, and supports multiple rendering output options including e-paper displays and consoles.

## Project Structure

```plaintext
.
├── lib/
│   └── waveshare_epd/        # External or custom e-paper display driver library
├── resources/
│   └── Font.ttc              # Font resource for rendering
├── src/
│   ├── AbstractRenderer.py   # Abstract base class for renderers
│   ├── ConsoleRenderer.py    # Renderer for console output
│   ├── DockerStats.py        # Gathers stats from Docker containers
│   ├── ePaperRenderer.py     # Renderer for e-paper displays
│   ├── RendererManager.py    # Manages switching/selecting renderers
│   ├── RemoteConnectionManager.py # Handles remote connections (e.g., SSH)
│   ├── RpiStats.py           # Gathers Raspberry Pi hardware statistics
│   ├── server_status.py      # Collects generic server status info
│   └── __init__.py
├── setup.py                  # Package installation and dependency management
├── .gitignore
└── README.md                 # Project documentation (this file)
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

- Python 3.9.6
- Third-party packages: `numpy`, `paramiko`, `pillow`, `requests`, `six`
- System dependencies for specific renderers (e.g. hardware libraries for e-paper displays)

## Installation

1. Clone the repository.
2. Install the required packages (preferably within a virtual environment):

   ```bash
   pip install -r requirements.txt
   # or if using setup.py
   python setup.py install
   ```

3. Additional steps may be necessary for e-paper display support (see documentation for the `lib/waveshare_epd` module).

## Usage

- Run the appropriate entry point script (see `src/` for options or contribute a main application script).
- Configure any necessary environment variables for remote connections or display selection.
- Output can be toggled among different renderer types based on your needs or hardware.

## Customization

- Add new renderers by subclassing `AbstractRenderer.py`
- Enhance statistics sources by expanding modules like `RpiStats.py` or `DockerStats.py`
- Include new resource files (fonts, images) in the `resources/` directory as needed.

## License

Include licensing and contribution policies here if applicable.

---

Feel free to adapt the **Usage** and **Customization** sections once a main entry point or script is clearly defined, or if additional features are added!