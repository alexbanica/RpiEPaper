#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

from cluster_monitor.renderers.AbstractRenderer import AbstractRenderer
from cluster_monitor.renderers.ConsoleRenderer import ConsoleRenderer
from cluster_monitor.renderers.ePaper import EPaperRenderer
from cluster_monitor import RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE
from cluster_monitor.dto import Context


class RendererManager:
    def __init__(self, context: Context):
        if context.render_type == RENDERER_TYPE_CONSOLE:
            self.renderer = ConsoleRenderer(context)
        elif context.render_type == RENDERER_TYPE_EPAPER:
            self.renderer = EPaperRenderer(context)

    def get_renderer(self) -> AbstractRenderer:
        return self.renderer

    def __close__(self) -> None:
        logging.info("Closing RendererManager")
        self.renderer.__close__()
        EPaperRenderer.shutdown()
        logging.info("RendererManager closed")