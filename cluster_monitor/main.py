#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging, os, sys

from cluster_monitor import CONFIG_FILE_PATHS, RESOURCES_DIR, LIB_DIR
if os.path.exists(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

from logging.handlers import TimedRotatingFileHandler
from cluster_monitor.ClusterMonitor import ClusterMonitor
from cluster_monitor.dto import Context
from cluster_monitor.helpers import YamlHelper
from cluster_monitor.renderers import cleanup_epaper

def _setup_logging():
    file_handler = TimedRotatingFileHandler(
        '/var/log/cluster_monitor.log',
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

def main(context: Context):
    try:
        _setup_logging()
        logging.info("Starting Cluster Monitor. Press Ctrl+C to exit.")

        YamlHelper(RESOURCES_DIR).parse_config(context, CONFIG_FILE_PATHS)
        ClusterMonitor(context).start()
    except Exception as e:
        logging.error("Error starting cluster monitor: %s", e)
        cleanup_epaper()
        exit(1)