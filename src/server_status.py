#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from DockerStats import DockerStats
from RpiStats import RpiStats, RPI_STATS_PYTHON_COMMAND
from RemoteConnectionManager import RemoteConnectionManager
from RendererManager import RendererManager
from AbstractRenderer import AbstractRenderer, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER, NULL_COORDS, RENDER_ALIGN_LEFT
from typing import Optional

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")
DEFAULT_DISPLAY_UPDATE_INTERVAL_S = 1


def draw_docker_stats(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
    if docker is None:
        return prev_coords

    # Draw Docker Title
    stats_coords = renderer.draw_text("Docker Swarm Stats", prev_coords, RENDER_ALIGN_CENTER)
    renderer.draw_text(f"Nodes: {','.join(docker.extract_node_hostnames())}", stats_coords, RENDER_ALIGN_LEFT)
    coords = renderer.draw_text(f"{docker.count_nodes_by_state()}/{docker.count_all_nodes()}", stats_coords, RENDER_ALIGN_RIGHT)

    results = remotes.get_async_results(command_uuid)
    for hostname, stats in results.items():
        if hostname != rpi.get_hostname():
            coords = renderer.draw_text(f"{stats} - (R)", coords, RENDER_ALIGN_LEFT)
        else:
            coords = renderer.draw_text(f"{stats}", coords, RENDER_ALIGN_LEFT)

    coords = renderer.draw_new_subsection(coords)
    coords = renderer.draw_text(f"Services: #{docker.count_all_services()}", coords)
    service_list = docker.extract_service_names()
    coords = renderer.draw_paragraph(service_list, coords)

    return coords

try:
    logging.info("Raspberry Pi Status display. Press Ctrl+C to exit.")
    rpi = RpiStats()
    renderer_manager = RendererManager(True)
    renderer = renderer_manager.get_renderer()
    docker = DockerStats()
    remote_connection_manager = RemoteConnectionManager([])
    command_uuid = remote_connection_manager.attach_command(RPI_STATS_PYTHON_COMMAND)

    # Infinite loop to update the time every second
    while True:
        try:
            remote_connection_manager.update_hostnames(docker.extract_node_hostnames())
            logging.info("Updating display...")
            renderer.refresh()
            coords = renderer.draw_text(rpi.get_current_time(), NULL_COORDS, RENDER_ALIGN_RIGHT)
            if not rpi.is_cluster_hat_on():
                coords = renderer.draw_text(rpi.render_cluster_hat_status(), coords)
                coords = renderer.draw_text(rpi.__str__(), coords)
            else:
                coords = renderer.draw_text(rpi.render_cluster_hat_status())
                coords = renderer.draw_new_section(coords)
                coords = draw_docker_stats(renderer, docker, rpi, remote_connection_manager, command_uuid, coords)
                renderer.draw_new_section(coords)

            renderer.draw_apply()
            time.sleep(DEFAULT_DISPLAY_UPDATE_INTERVAL_S)

        except KeyboardInterrupt:
            logging.info("Interrupted by user. Exiting...")
            renderer_manager.__close__()
            if rpi.is_cluster_hat_on():
                docker.__close__()
                remote_connection_manager.__close__()
            exit(0)

except IOError as e:
    logging.error(e)
    exit(1)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    exit(0)
