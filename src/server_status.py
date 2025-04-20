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
from ServerStatusArgumentParser import ServerStatusArgumentParser, ARG_RENDERER_TYPE_CONSOLE, ARG_RENDERER_TYPE_EPAPER

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")
DEFAULT_DISPLAY_UPDATE_INTERVAL_S = 5

def draw_docker_stats_pag_1(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
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

def draw_docker_stats_pag_2(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
    if docker is None:
        return prev_coords

    # Draw Docker Title
    stats_coords = renderer.draw_text("Docker Swarm Services Stats", prev_coords, RENDER_ALIGN_CENTER)
    coords = renderer.draw_text(f"#{docker.count_all_services()}", stats_coords, RENDER_ALIGN_RIGHT)
    service_list = docker.extract_service_names()
    coords = renderer.draw_paragraph(service_list, coords)

    return coords

def draw_docker_stats_pag_3(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
    if docker is None:
        return prev_coords

    # Draw Docker Title
    stats_coords = renderer.draw_text("Docker Swarm Stats Page 3", prev_coords, RENDER_ALIGN_CENTER)

    return stats_coords

def draw_docker_stats_pag_4(renderer: AbstractRenderer, docker: DockerStats, rpi: RpiStats, remotes: RemoteConnectionManager, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
    if docker is None:
        return prev_coords

    # Draw Docker Title
    stats_coords = renderer.draw_text("Docker Swarm Stats Page 4", prev_coords, RENDER_ALIGN_CENTER)

    return stats_coords

def _is_busy(rpi: RpiStats, docker:DockerStats, remote_connection_manager:RemoteConnectionManager) -> bool:
    if not rpi.is_cluster_hat_on():
        return False
    if docker.is_busy():
        return True
    if remote_connection_manager.is_busy():
        return True
    return False

try:
    logging.info("Server Status display. Press Ctrl+C to exit.")
    args = ServerStatusArgumentParser.parse()
    rpi = RpiStats()
    renderer_manager = RendererManager(args.renderer == ARG_RENDERER_TYPE_CONSOLE)
    renderer = renderer_manager.get_renderer()
    docker = DockerStats()
    remote_connection_manager = RemoteConnectionManager([])
    command_uuid = remote_connection_manager.attach_command(RPI_STATS_PYTHON_COMMAND)
    remote_connection_manager.execute_on_all_async(command_uuid)

    while True:
        try:
            renderer.refresh()
            remote_connection_manager.update_hostnames(docker.extract_node_hostnames())
            if _is_busy(rpi, docker, remote_connection_manager):
                logging.debug("Docker or remote connection busy. Waiting for completion...")
                renderer.draw_loading()
            else:
                coords = renderer.draw_text(rpi.get_current_time() + renderer.draw_pagination(), NULL_COORDS, RENDER_ALIGN_RIGHT)
                if not rpi.is_cluster_hat_on():
                    coords = renderer.draw_text(rpi.render_cluster_hat_status())
                    coords = renderer.draw_text(str(rpi), coords)
                else:
                    if renderer.get_mixin().get_current_page() == 1:
                        coords = renderer.draw_text(rpi.render_cluster_hat_status())
                        coords = renderer.draw_new_section(coords)
                        coords = draw_docker_stats_pag_1(renderer, docker, rpi, remote_connection_manager, command_uuid, coords)
                        renderer.draw_new_section(coords)
                    elif renderer.get_mixin().get_current_page() == 2:
                        coords = renderer.draw_text(rpi.render_cluster_hat_status())
                        coords = renderer.draw_new_section(coords)
                        coords = draw_docker_stats_pag_2(renderer, docker, rpi, remote_connection_manager, command_uuid, coords)
                        renderer.draw_new_section(coords)
                    elif renderer.get_mixin().get_current_page() == 3:
                        coords = renderer.draw_text(rpi.render_cluster_hat_status())
                        coords = renderer.draw_new_section(coords)
                        coords = draw_docker_stats_pag_3(renderer, docker, rpi, remote_connection_manager, command_uuid, coords)
                        renderer.draw_new_section(coords)
                    elif renderer.get_mixin().get_current_page() == 4:
                        coords = renderer.draw_text(rpi.render_cluster_hat_status())
                        coords = renderer.draw_new_section(coords)
                        coords = draw_docker_stats_pag_4(renderer, docker, rpi, remote_connection_manager, command_uuid, coords)
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
