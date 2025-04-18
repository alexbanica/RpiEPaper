#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from DockerStats import DockerStats
from RpiStats import RpiStats
from RemoteConnectionManager import RemoteConnectionManager
from RendererManager import RendererManager
from AbstractRenderer import AbstractRenderer, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER, NULL_COORDS, RENDER_ALIGN_LEFT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")


def draw_docker_stats(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
    if docker is None:
        return prev_coords

    # Draw Docker Title
    stats_coords = renderer.draw_text("Docker Swarm Stats", prev_coords, RENDER_ALIGN_CENTER)
    renderer.draw_text(f"Nodes: {','.join(docker.extract_node_hostnames())}", stats_coords, RENDER_ALIGN_LEFT)
    coords = renderer.draw_text(f"{docker.count_nodes_by_state()}/{docker.count_all_nodes()}", stats_coords, RENDER_ALIGN_RIGHT)

    results = remotes.execute_on_all("PYTHONPATH=/mnt/data/ePaperHat/src python3 -c 'from RpiStats import RpiStats; print(RpiStats())'")
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
    docker = None
    remote_connection_manager = None
    renderer = RendererManager(True).get_renderer()
    if rpi.is_cluster_hat_on():
        docker = DockerStats()
        remote_connection_manager = RemoteConnectionManager(docker.extract_node_hostnames())

    # Infinite loop to update the time every second
    while True:
        try:
            logging.info("Updating display...")
            renderer.refresh()
            coords = renderer.draw_text(rpi.get_current_time(), NULL_COORDS, RENDER_ALIGN_RIGHT)
            if not rpi.is_cluster_hat_on():
                coords = renderer.draw_text(rpi.__str__(), coords)
            else:
                coords = renderer.draw_text("ClusterHat info here")
                coords = renderer.draw_new_section(coords)
                coords = draw_docker_stats(renderer, docker, rpi, remote_connection_manager, coords)
                renderer.draw_new_section(coords)

            renderer.draw_apply()
            time.sleep(5)

        except KeyboardInterrupt:
            logging.info("Interrupted by user. Exiting...")
            renderer.__close__()
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
