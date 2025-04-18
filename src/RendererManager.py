from ConsoleRenderer import ConsoleRenderer
from ePaperRenderer import EPaperRenderer
from AbstractRenderer import AbstractRenderer

class RendererManager:
    def __init__(self, use_console: bool):
        """
        Initialize the RendererManager with the appropriate renderer.

        Args:
            use_console (bool): Whether to use the ConsoleRenderer.
        """
        if use_console:
            self.renderer = ConsoleRenderer()
        else:
            self.renderer = EPaperRenderer()

    def get_renderer(self) -> AbstractRenderer:
        """
        Get the active renderer.
        """
        return self.renderer