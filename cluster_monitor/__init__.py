import sys

from cluster_monitor.shared.constants import (
    ARG_PAGE_CHOICES,
    ARG_RENDERER_CHOICES,
    CONFIG_FILE_PATHS,
    LIB_DIR,
    RENDERER_TYPE_CONSOLE,
    RENDERER_TYPE_EPAPER,
    RESOURCES_DIR,
)

__version__ = "1.0.0"
__author__ = "Ionut-Alexandru Banica"

if str(LIB_DIR) not in sys.path:
    sys.path.append(str(LIB_DIR))
