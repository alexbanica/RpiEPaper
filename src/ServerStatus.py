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

DEFAULT_DISPLAY_UPDATE_INTERVAL_S = 5


class ServerStatus:
    def __init__(self, console_args):
        self.is_running = True
        self.console_args = console_args
        self.rpi = RpiStats()
        self.docker = DockerStats()
        self.renderer_manager = RendererManager(console_args.renderer == ARG_RENDERER_TYPE_CONSOLE)
        self.remote_connection_manager = RemoteConnectionManager([])

    def draw_rpi_stats(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.rpi is None:
            return prev_coords
        coords = renderer.draw_text("RaspberryPI Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_new_subsection(coords)
        coords = renderer.draw_text(str(self.rpi), coords)

        return coords

    def draw_docker_stats_pag_1(self, renderer: AbstractRenderer, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Stats", prev_coords, RENDER_ALIGN_CENTER)
        renderer.draw_text(f"Nodes: {','.join(self.docker.extract_node_hostnames())}", stats_coords, RENDER_ALIGN_LEFT)
        coords = renderer.draw_text(f"{self.docker.count_nodes_by_state()}/{self.docker.count_all_nodes()}", stats_coords, RENDER_ALIGN_RIGHT)

        results = self.remote_connection_manager.get_async_results(command_uuid)
        for hostname, stats in results.items():
            if hostname != self.rpi.get_hostname():
                coords = renderer.draw_text(f"{stats} - (R)", coords, RENDER_ALIGN_LEFT)
            else:
                coords = renderer.draw_text(f"{stats}", coords, RENDER_ALIGN_LEFT)

        coords = renderer.draw_new_subsection(coords)
        coords = renderer.draw_text(f"Services: #{self.docker.count_all_services()}", coords)
        service_list = self.docker.extract_service_names_with_ports()
        coords = renderer.draw_paragraph(service_list, coords)

        return coords

    def draw_docker_stats_pag_2(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Services Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_text(f"#{self.docker.count_all_services()}", prev_coords, RENDER_ALIGN_RIGHT)
        services = self.docker.extract_service_details()

        coords = renderer.draw_table(
            {'name': 'Name','image': 'Img','ports': 'Ports', 'replicas': 'R', 'created': 'Created'},
            [serviceStats.to_dict() for serviceStats in services],
            coords
        )

        return coords

    def draw_docker_stats_pag_3(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Stats Page 3", prev_coords, RENDER_ALIGN_CENTER)

        return stats_coords

    def draw_docker_stats_pag_4(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Stats Page 4", prev_coords, RENDER_ALIGN_CENTER)

        return stats_coords

    def _is_busy(self) -> bool:
        if not self.rpi.is_cluster_hat_on():
            return False
        if self.docker.is_busy():
            return True
        if self.remote_connection_manager.is_busy():
            return True
        return False

    def start(self):
        logging.info("Server Status display. Press Ctrl+C to exit.")
        renderer = self.renderer_manager.get_renderer()
        command_uuid = self.remote_connection_manager.attach_command(RPI_STATS_PYTHON_COMMAND)
        self.remote_connection_manager.execute_on_all_async(command_uuid)

        while self.is_running:
            try:
                logging.debug("Updating display...")
                renderer.refresh()
                self.remote_connection_manager.update_hostnames(self.docker.extract_node_hostnames())
                if self._is_busy():
                    logging.debug("Docker or remote connection busy. Waiting for completion...")
                    renderer.draw_loading()
                else:
                    renderer.draw_text(self.rpi.get_current_time() + renderer.draw_pagination(), NULL_COORDS, RENDER_ALIGN_RIGHT)
                    coords = renderer.draw_text(self.rpi.render_cluster_hat_status())
                    coords = renderer.draw_new_section(coords)
                    if not self.rpi.is_cluster_hat_on():
                        coords = self.draw_rpi_stats(renderer, coords)
                    else:
                        if renderer.get_controller().get_current_page() == 1:
                            coords = self.draw_docker_stats_pag_1(renderer, command_uuid, coords)
                            renderer.draw_new_section(coords)
                        elif renderer.get_controller().get_current_page() == 2:
                            self.draw_docker_stats_pag_2(renderer, coords)
                        elif renderer.get_controller().get_current_page() == 3:
                            coords = self.draw_docker_stats_pag_3(renderer, coords)
                            renderer.draw_new_section(coords)
                        elif renderer.get_controller().get_current_page() == 4:
                            coords = self.draw_docker_stats_pag_4(renderer, coords)
                            renderer.draw_new_section(coords)

                renderer.draw_apply()
                time.sleep(DEFAULT_DISPLAY_UPDATE_INTERVAL_S)

            except KeyboardInterrupt:
                logging.info("Interrupted by user. Exiting...")
                self.__close__()
            except Exception as e:
                logging.error(f"Error updating display: {e}")
                self.__close__()
                raise e

    def __close__(self):
        logging.info("Closing Server Status")
        self.is_running = False
        self.renderer_manager.__close__()
        if self.rpi.is_cluster_hat_on():
            self.docker.__close__()
            self.remote_connection_manager.__close__()
        logging.info("Server Status shutting down")