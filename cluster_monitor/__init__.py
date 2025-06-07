#!/usr/bin/python
# -*- coding:utf-8 -*-
__version__ = "1.0.0"
__author__ = "Ionut-Alexandru Banica"

import os, sys
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')

if os.path.exists(libdir) and libdir not in sys.path:
    sys.path.append(libdir)

RENDERER_TYPE_EPAPER = 'epaper'
RENDERER_TYPE_CONSOLE = 'console'
ARG_RENDERER_CHOICES = [RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE]
ARG_PAGE_CHOICES = ['1', '2', '3']
CONFIG_FILE_PATHS = ["config.yaml", "config.yml", "config.local.yaml", "config.local.yml"]

from cluster_monitor.renderers import cleanup_epaper, RendererManager
from cluster_monitor.services import DockerService, RemoteService, RpiService