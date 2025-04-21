import logging
from ConsoleRenderer import ConsoleRenderer
from ePaperRenderer import EPaperRenderer
from AbstractRenderer import AbstractRenderer

class RendererManager:
    def __init__(self, use_console: bool):
        if use_console:
            self.renderer = ConsoleRenderer()
        else:
            self.renderer = EPaperRenderer()

    def get_renderer(self) -> AbstractRenderer:
        return self.renderer

    def __close__(self):
        logging.info("Closing RendererManager")
        self.renderer.__close__()
        EPaperRenderer.shutdown()
        logging.info("RendererManager closed")