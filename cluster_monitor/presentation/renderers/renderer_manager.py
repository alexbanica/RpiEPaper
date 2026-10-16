import logging
import threading

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import RendererInterface, RendererManagerInterface
from cluster_monitor.presentation.renderers.console_renderer import ConsoleRenderer
from cluster_monitor.shared.constants import RENDERER_TYPE_CONSOLE, RENDERER_TYPE_EPAPER


class RendererManager(RendererManagerInterface):
    def __init__(self, context: ContextEntity):
        self._close_condition = threading.Condition()
        self._close_state = "open"
        self._close_owner = None
        self._close_error = None
        self._is_epaper_renderer = False
        if context.render_type == RENDERER_TYPE_CONSOLE:
            self.renderer = ConsoleRenderer(context)
        else:
            from cluster_monitor.presentation.renderers.epapers.epaper_renderer import EpaperRenderer

            self.renderer = EpaperRenderer(context)
            self._is_epaper_renderer = True

    def get_renderer(self) -> RendererInterface:
        return self.renderer

    def close(self) -> None:
        current = threading.get_ident()
        with self._close_condition:
            while self._close_state == "closing" and self._close_owner != current:
                self._close_condition.wait()
            if self._close_state == "closed":
                if self._close_error is not None:
                    raise self._close_error
                return
            if self._close_state == "closing":
                return
            self._close_state = "closing"
            self._close_owner = current

        failures = []
        try:
            self.renderer.close()
        except Exception as error:
            failures.append(error)
            logging.exception("Renderer cleanup failed")
        finally:
            if self._is_epaper_renderer:
                try:
                    from cluster_monitor.presentation.renderers.epapers.epaper_renderer import EpaperRenderer
                    EpaperRenderer.shutdown()
                except Exception as error:
                    failures.append(error)
                    logging.exception("ePaper hardware cleanup failed")
        with self._close_condition:
            self._close_error = failures[0] if failures else None
            self._close_state = "closed"
            self._close_owner = None
            self._close_condition.notify_all()
        if failures:
            raise failures[0]
