#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from ConsoleRenderer import ConsoleRenderer
from ePaperRenderer import EPaperRenderer
from AbstractRenderer import AbstractRenderer
from ServerStatusContext import RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE


class RendererManager:
    def __init__(self, renderer: str):
        if renderer == RENDERER_TYPE_CONSOLE:
            self.renderer = ConsoleRenderer()
        elif renderer == RENDERER_TYPE_EPAPER:
            self.renderer = EPaperRenderer()

    def get_renderer(self) -> AbstractRenderer:
        return self.renderer

    def __close__(self):
        logging.info("Closing RendererManager")
        self.renderer.__close__()
        EPaperRenderer.shutdown()
        logging.info("RendererManager closed")