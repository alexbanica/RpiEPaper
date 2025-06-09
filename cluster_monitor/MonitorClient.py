#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

from cluster_monitor.services.RpiService import RpiService

class MonitorClient:
    singleton = None

    def __init__(self):
        self.rpi_service = RpiService()
        logging.info("Cluster Client initialized")

    def render_rpi_stats(self):
        print(self.rpi_service.render_stats())
