from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import RendererInterface
from cluster_monitor.presentation.renderers.console_renderer import ConsoleRenderer
from cluster_monitor.shared.constants import RENDERER_TYPE_CONSOLE, RENDERER_TYPE_EPAPER


class RendererManager:
    def __init__(self, context: ContextEntity):
        if context.render_type == RENDERER_TYPE_CONSOLE:
            self.renderer = ConsoleRenderer(context)
        else:
            from cluster_monitor.presentation.renderers.epapers.epaper_renderer import EpaperRenderer

            self.renderer = EpaperRenderer(context)

    def get_renderer(self) -> RendererInterface:
        return self.renderer

    def close(self) -> None:
        self.renderer.close()
        from cluster_monitor.presentation.renderers.epapers.epaper_renderer import EpaperRenderer

        EpaperRenderer.shutdown()
