#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import logging
import signal

from cluster_monitor.services.RpiService import RpiService
from cluster_monitor.services.DockerService import DockerService
from cluster_monitor.services.RemoteService import RemoteService
from cluster_monitor.renderers import RendererManager, AbstractRenderer, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER, NULL_COORDS, RENDER_ALIGN_LEFT
from cluster_monitor.dto import Context
from typing import Optional

DEFAULT_DISPLAY_UPDATE_INTERVAL_S = 5

class ClusterMonitor:
    singleton = None

    def __init__(self, context: Context):
        self.is_running = True
        self._is_healthy = True
        self.context = context
        self.rpi_service = RpiService()
        self.docker_service = DockerService()
        self.renderer_manager = RendererManager(self.context)
        self.remote_connection_service = RemoteService([], context.remote_ssh_username, context.remote_ssh_key_path)
        ClusterMonitor.singleton = self
        self._setup_signal_handlers()
        logging.info("Cluster Monitor initialized with context info: %s", context)

    def draw_rpi_stats(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.rpi_service is None:
            return prev_coords
        coords = renderer.draw_text("RaspberryPI Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_new_subsection(coords)
        coords = renderer.draw_text(str(self.rpi_service.render_stats()), coords)

        return coords

    def draw_docker_stats_pag_1(self, renderer: AbstractRenderer, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker_service is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Resources Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_text(f"N: {self.docker_service.count_nodes_by_state()}/{self.docker_service.count_all_nodes()} - S: #{self.docker_service.count_all_services()} - P: #{len(self.docker_service.get_open_ports())}", stats_coords)
        coords = renderer.draw_new_subsection(coords)
        results = self.remote_connection_service.get_async_results(command_uuid)
        for hostname, stats in results.items():
            if hostname != self.rpi_service.get_hostname():
                coords = renderer.draw_text(f"{stats} - (R)", coords, RENDER_ALIGN_LEFT)
            else:
                coords = renderer.draw_text(f"{stats}", coords, RENDER_ALIGN_LEFT)

        subsection_coords = renderer.draw_new_subsection(coords)
        host_ports = self.docker_service.extract_open_host_ports()
        coords = renderer.draw_text("P: ", subsection_coords)
        coords = renderer.draw_paragraph([f":{port}" for port in host_ports], (coords[0], coords[1], coords[2], subsection_coords[3]), "P: ")

        return coords

    def draw_docker_stats_pag_2(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker_service is None:
            return prev_coords

        # Draw Docker Title
        stats_coords = renderer.draw_text("Docker Swarm Services Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_text(f"#{self.docker_service.count_all_services()}", prev_coords, RENDER_ALIGN_RIGHT)
        services = self.docker_service.extract_service_details()

        # Calculate visible service range
        start_index = renderer.get_current_scroll_offset()
        end_index = min(renderer.get_current_scroll_offset() + renderer.get_current_scroll_step(), len(services))
        visible_services = services[start_index:end_index]

        coords = renderer.draw_table(
                {'name': 'Name','image': 'Img','ports': 'Ports', 'replicas': 'R'},
                [serviceStats.to_dict() for serviceStats in visible_services],
                coords
            )

        return coords

    def draw_docker_stats_pag_3(self, renderer: AbstractRenderer, command_uuid: Optional[str], prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker_service is None:
            return prev_coords

        stats_coords = renderer.draw_text("Hard Disk Usages", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_new_subsection(stats_coords)

        disk_usages = self.rpi_service.get_disk_usages()
        for disk_usage in disk_usages:
            coords = renderer.draw_text(f"{self.rpi_service.get_hostname()} - {disk_usage.render()}", coords, RENDER_ALIGN_LEFT)

        results = self.remote_connection_service.get_async_results(command_uuid)
        for hostname, stats in results.items():
            if hostname == self.rpi_service.get_hostname():
                continue
            coords = renderer.draw_text(f"{hostname} - {stats}", coords, RENDER_ALIGN_LEFT)

        return stats_coords

    def draw_docker_stats_pag_4(self, renderer: AbstractRenderer, prev_coords:tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int,int,int]:
        if self.docker_service is None:
            return prev_coords

        # Draw Docker Title
        prev_coords = renderer.draw_text("Cluster Logs", prev_coords, RENDER_ALIGN_CENTER)
        prev_coords = renderer.draw_new_subsection(prev_coords)
        log_lines = self.rpi_service.render_logs(
            self.rpi_service.get_lines_from_file('/var/log/cluster_monitor.log')
        )

        for line in log_lines:
            #logging.warning(line)
            prev_coords = renderer.draw_text(line, prev_coords, RENDER_ALIGN_LEFT)

        return prev_coords

    def _is_busy(self) -> bool:
        if not self.rpi_service.is_cluster_hat_on():
            return False
        if self.docker_service.is_busy():
            return True
        if self.remote_connection_service.is_busy():
            return True
        return False

    def is_healthy(self) -> bool:
        return self._is_healthy and \
            self.docker_service.is_healthy() and \
            self.remote_connection_service.is_healthy() and \
            self.rpi_service.is_healthy()

    def start(self) -> None:
        logging.info("Cluster Monitor display. Press Ctrl+C to exit.")
        renderer = self.renderer_manager.get_renderer()
        rpi_stats_command_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_status_command)
        rpi_hdd_command_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_hdd_status_command)
        self.remote_connection_service.execute_on_all_async(rpi_stats_command_uuid)
        self.remote_connection_service.execute_on_all_async(rpi_hdd_command_uuid)
        current_drawing_page = renderer.get_controller().get_current_page()

        while self.is_running:
            try:
                logging.debug("Updating display...")
                if current_drawing_page != renderer.get_controller().get_current_page():
                    current_drawing_page = renderer.get_controller().get_current_page()
                    renderer.hard_refresh()
                    continue

                if not self.is_healthy():
                    self.rpi_service.set_cluster_hat_alert(True)
                else:
                    self.rpi_service.set_cluster_hat_alert(False)

                renderer.refresh()
                self.remote_connection_service.update_hostnames(self.docker_service.extract_node_hostnames())

                renderer.draw_text(self.rpi_service.get_current_time() + renderer.draw_pagination(), NULL_COORDS, RENDER_ALIGN_RIGHT)
                coords = renderer.draw_text(self.rpi_service.render_cluster_hat_status())
                coords = renderer.draw_new_section(coords)

                if self._is_busy():
                    logging.info("Docker or remote connection busy. Waiting for completion...")
                    renderer.draw_loading(coords)
                else:
                    if not self.rpi_service.is_cluster_hat_on():
                        self.draw_rpi_stats(renderer, coords)
                    else:
                        if current_drawing_page == 1:
                            self.draw_docker_stats_pag_1(renderer, rpi_stats_command_uuid, coords)
                        elif current_drawing_page == 2:
                            self.draw_docker_stats_pag_2(renderer, coords)
                        elif current_drawing_page == 3:
                            self.draw_docker_stats_pag_3(renderer, rpi_hdd_command_uuid, coords)
                        elif current_drawing_page == 4:
                            self.draw_docker_stats_pag_4(renderer, coords)
                        else:
                            logging.warning(f"Invalid drawing page: {current_drawing_page}")

                renderer.draw_apply()
                self._is_healthy = True
                time.sleep(DEFAULT_DISPLAY_UPDATE_INTERVAL_S)
            except KeyboardInterrupt as e:
                logging.warning("Monitor interrupted by user")
                self.__close__()
                raise e
            except Exception as e:
                logging.error(f"Error updating display: {e}")
                self._is_healthy = False
                time.sleep(DEFAULT_DISPLAY_UPDATE_INTERVAL_S)

    def __close__(self) -> None:
        logging.info("Closing Cluster Monitor")
        self.is_running = False
        self.rpi_service.set_cluster_hat_alert(False)
        self.renderer_manager.__close__()
        if self.rpi_service.is_cluster_hat_on():
            self.docker_service.__close__()
            self.remote_connection_service.__close__()
        logging.info("Cluster Monitor shut down")


    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, _) -> None:
        logging.info(f"Received signal {signum}. Initiating shutdown...")
        self.__close__()

    @staticmethod
    def get_context() -> Context:
        return ClusterMonitor.singleton.context
