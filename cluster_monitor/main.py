#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import logging
import argparse
from logging.handlers import TimedRotatingFileHandler
from cluster_monitor import cleanup_epaper, ARG_RENDERER_CHOICES, ARG_PAGE_CHOICES, RENDERER_TYPE_EPAPER, CONFIG_FILE_PATHS
from cluster_monitor.ClusterMonitor import ClusterMonitor
from cluster_monitor.dto import Context
from cluster_monitor.helpers import YamlHelper

configdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')

def _setup_logging():
    file_handler = TimedRotatingFileHandler(
        '/var/log/server_status.log',
        when='midnight',
        interval=1,
        backupCount=5
    )
    console_handler = logging.StreamHandler()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s",
        handlers=[file_handler, console_handler]
    )

def _console_parse_arguments(context: Context) -> None:
    parser = argparse.ArgumentParser(description='Server Status Display')
    parser.add_argument('-r', '--renderer', choices=ARG_RENDERER_CHOICES, default='epaper',
                        help='Choose renderer type: console or epaper')
    parser.add_argument('-p', '--page', choices=ARG_PAGE_CHOICES, default=1,
                        help='Choose default page nr: 1 or 2')

    args = parser.parse_args()
    context.default_page = int(args.page)
    context.render_type = args.renderer

def main():
    _setup_logging()
    try:
        logging.info("Starting Cluster Monitor. Press Ctrl+C to exit.")
        context = Context(1, RENDERER_TYPE_EPAPER)
        YamlHelper(configdir).parse_config(context, CONFIG_FILE_PATHS)
        _console_parse_arguments(context)
        ClusterMonitor(context).start()
    except Exception as e:
        logging.error(f"Error starting server status: {e}")
        cleanup_epaper()