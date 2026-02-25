from cluster_monitor.domain.services import RendererInterface
from cluster_monitor.shared.constants import NULL_COORDS, RENDER_ALIGN_CENTER, RENDER_ALIGN_LEFT, RENDER_ALIGN_RIGHT

__all__ = [
    "AbstractRenderer",
    "NULL_COORDS",
    "RENDER_ALIGN_LEFT",
    "RENDER_ALIGN_RIGHT",
    "RENDER_ALIGN_CENTER",
]


class AbstractRenderer(RendererInterface):
    pass
