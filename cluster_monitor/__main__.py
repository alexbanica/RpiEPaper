#!/usr/bin/python
# -*- coding:utf-8 -*-
import argparse
from cluster_monitor.dto import Context
from cluster_monitor import ARG_RENDERER_CHOICES, ARG_PAGE_CHOICES, RENDERER_TYPE_EPAPER

def _console_parse_arguments(context: Context) -> None:
    parser = argparse.ArgumentParser(description='Server Status Display')
    parser.add_argument('-r', '--renderer', choices=ARG_RENDERER_CHOICES, default=RENDERER_TYPE_EPAPER,
                        help='Choose renderer type: console or epaper')
    parser.add_argument('-p', '--page', choices=ARG_PAGE_CHOICES, default=1,
                        help='Choose default page nr: 1 or 2')
    parser.add_argument('-mc', '--monitor-client', action='store_true', default=False,
                        help='Choose if you execute this as a monitor client')

    args = parser.parse_args()
    context.default_page = int(args.page)
    context.render_type = args.renderer
    context.is_monitor_client = args.monitor_client

if __name__ == "__main__":
    context = Context(1, RENDERER_TYPE_EPAPER)
    _console_parse_arguments(context)

    if context.is_monitor_client:
        from cluster_monitor.MonitorClient import MonitorClient
        MonitorClient().render_rpi_stats()
    else:
        from cluster_monitor.main import main
        main(context)
    exit(0)