#!/usr/bin/python
# -*- coding:utf-8 -*-

__version__ = "1.0.0"
__author__ = "Ionut-Alexandru Banica"

import os, sys
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')

RENDERER_TYPE_EPAPER = 'epaper'
RENDERER_TYPE_CONSOLE = 'console'
ARG_RENDERER_CHOICES = [RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE]
ARG_PAGE_CHOICES = ['1', '2', '3', '4']
ARG_BOOL_CHOICES = ['1', '0']
CONFIG_FILE_PATHS = ["config.yaml", "config.yml", "config.local.yaml", "config.local.yml"]