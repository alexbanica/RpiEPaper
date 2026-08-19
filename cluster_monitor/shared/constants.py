"""Shared project constants."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = PACKAGE_DIR.parent
LIB_DIR = PROJECT_DIR / "lib"
RESOURCES_DIR = PACKAGE_DIR / "resources"
CONFIG_DIR_ENV = "CLUSTER_MONITOR_CONFIG_DIR"

RENDERER_TYPE_EPAPER = "epaper"
RENDERER_TYPE_CONSOLE = "console"
ARG_RENDERER_CHOICES = [RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE]
ARG_PAGE_CHOICES = ["1", "2", "3", "4"]
CONFIG_FILE_PATHS = ["config.yaml", "config.yml", "config.local.yaml", "config.local.yml"]

RENDER_ALIGN_CENTER = "center"
RENDER_ALIGN_LEFT = "left"
RENDER_ALIGN_RIGHT = "right"
NULL_COORDS = (0, 0, 0, 0)
