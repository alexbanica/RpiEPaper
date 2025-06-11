#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

from cluster_monitor.dto import Context
from cluster_monitor.services.RpiService import RpiService

class MonitorClient:
    singleton = None

    def __init__(self):
        self.rpi_service = RpiService()
        logging.info("Cluster Client initialized")

    def render_rpi_stats(self):
        print(self.rpi_service.render_stats())

    def render_disk_stats(self):
        for disk_usage in self.rpi_service.get_disk_usages():
            print(disk_usage.render())

    def render(self, context: Context):
        if context.show_hdd_stats:
            self.render_disk_stats()
            return

        self.render_rpi_stats()


