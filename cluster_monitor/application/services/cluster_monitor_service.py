import logging
import signal
import time
from typing import Optional

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import DockerServiceInterface, RemoteServiceInterface, RpiServiceInterface, SupervisorServiceInterface
from cluster_monitor.presentation.renderers.renderer_manager import RendererManager
from cluster_monitor.shared.constants import NULL_COORDS, RENDER_ALIGN_CENTER, RENDER_ALIGN_LEFT, RENDER_ALIGN_RIGHT


class ClusterMonitorService:
    singleton = None

    def __init__(
        self,
        context: ContextEntity,
        rpi_service: RpiServiceInterface,
        docker_service: DockerServiceInterface,
        remote_service: RemoteServiceInterface,
        supervisor_service: SupervisorServiceInterface,
    ):
        self.is_running = True
        self._is_healthy = True
        self.context = context
        self.rpi_service = rpi_service
        self.docker_service = docker_service
        self.supervisor_service = supervisor_service
        self.renderer_manager = RendererManager(self.context)
        self.remote_connection_service = remote_service
        ClusterMonitorService.singleton = self
        self._setup_signal_handlers()

    def draw_rpi_stats(self, renderer, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        coords = renderer.draw_text("RaspberryPI Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_new_subsection(coords)
        return renderer.draw_text(str(self.rpi_service.render_stats()), coords)

    def draw_docker_stats_page_1(
        self,
        renderer,
        command_uuid: Optional[str],
        prev_coords: tuple[int, int, int, int] = NULL_COORDS,
    ) -> tuple[int, int, int, int]:
        stats_coords = renderer.draw_text("Docker Swarm Resources Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_text(
            f"N: {self.docker_service.count_nodes_by_state()}/{self.docker_service.count_all_nodes()}"
            f" - S: #{self.docker_service.count_all_services()}"
            f" - P: #{len(self.docker_service.get_open_ports())}",
            stats_coords,
        )
        coords = renderer.draw_new_subsection(coords)

        results = self.remote_connection_service.get_async_results(command_uuid)
        for hostname, stats in results.items():
            suffix = " - (R)" if hostname != self.rpi_service.get_hostname() else ""
            coords = renderer.draw_text(f"{stats}{suffix}", coords, RENDER_ALIGN_LEFT)

        subsection_coords = renderer.draw_new_subsection(coords)
        host_ports = self.docker_service.extract_open_host_ports()
        coords = renderer.draw_text("P: ", subsection_coords)
        return renderer.draw_paragraph([f":{port}" for port in host_ports], (coords[0], coords[1], coords[2], subsection_coords[3]), "P: ")

    def draw_docker_stats_page_2(self, renderer, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        stats_coords = renderer.draw_text("Docker Swarm Services Stats", prev_coords, RENDER_ALIGN_CENTER)
        coords = renderer.draw_text(f"#{self.docker_service.count_all_services()}", stats_coords, RENDER_ALIGN_RIGHT)
        services = self.docker_service.extract_service_details()

        start_index = renderer.get_current_scroll_offset()
        end_index = min(start_index + renderer.get_current_scroll_step(), len(services))
        visible_services = services[start_index:end_index]

        return renderer.draw_table(
            {"name": "Name", "image": "Img", "deployed_to": "Nodes", "ports": "Ports", "replicas": "R"},
            [service.to_dict() for service in visible_services],
            coords,
        )

    def draw_docker_stats_page_3(
        self,
        renderer,
        command_uuid: Optional[str],
        prev_coords: tuple[int, int, int, int] = NULL_COORDS,
    ) -> tuple[int, int, int, int]:
        coords = prev_coords
        for disk_usage in self.rpi_service.get_disk_usages():
            coords = renderer.draw_text(f"{self.rpi_service.get_hostname()} - {disk_usage.render()}", coords, RENDER_ALIGN_LEFT)

        results = self.remote_connection_service.get_async_results(command_uuid)
        for hostname, stats in results.items():
            if hostname == self.rpi_service.get_hostname():
                continue
            coords = renderer.draw_text(f"{hostname} - {stats}", coords, RENDER_ALIGN_LEFT)

        return coords

    def draw_docker_stats_page_4(self, renderer, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        prev_coords = renderer.draw_text("Cluster Logs", prev_coords, RENDER_ALIGN_CENTER)
        prev_coords = renderer.draw_new_subsection(prev_coords)
        log_lines = self.rpi_service.render_logs(self.rpi_service.get_lines_from_file("/var/log/cluster_monitor.log"))

        for line in log_lines:
            prev_coords = renderer.draw_text(line, prev_coords, RENDER_ALIGN_LEFT)

        return prev_coords

    def _is_busy(self) -> bool:
        if not self.rpi_service.is_cluster_hat_on():
            return False
        return self.docker_service.is_busy() or self.remote_connection_service.is_busy()

    def is_healthy(self) -> bool:
        return (
            self._is_healthy
            and self.docker_service.is_healthy()
            and self.remote_connection_service.is_healthy()
            and self.supervisor_service.is_healthy()
            and self.rpi_service.is_healthy()
        )

    def start(self) -> None:
        renderer = self.renderer_manager.get_renderer()

        rpi_stats_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_status_command)
        rpi_hdd_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_hdd_status_command)
        self.remote_connection_service.execute_on_all_async(rpi_stats_uuid)
        self.remote_connection_service.execute_on_all_async(rpi_hdd_uuid)

        current_drawing_page = renderer.get_controller().get_current_page()

        while self.is_running:
            try:
                next_page = renderer.get_controller().get_current_page()
                if current_drawing_page != next_page:
                    current_drawing_page = next_page
                    renderer.hard_refresh()
                    time.sleep(0.5)
                    continue

                self.rpi_service.set_cluster_hat_alert(not self.is_healthy())

                renderer.refresh()
                self.remote_connection_service.update_hostnames(self.docker_service.extract_node_hostnames())

                renderer.draw_text(
                    self.rpi_service.get_current_time() + renderer.draw_pagination(),
                    NULL_COORDS,
                    RENDER_ALIGN_RIGHT,
                )
                coords = renderer.draw_text(self.rpi_service.render_cluster_hat_status())
                coords = renderer.draw_new_section(coords)

                if self._is_busy():
                    renderer.draw_loading(coords)
                else:
                    if not self.rpi_service.is_cluster_hat_on():
                        self.draw_rpi_stats(renderer, coords)
                    elif current_drawing_page == 1:
                        self.draw_docker_stats_page_1(renderer, rpi_stats_uuid, coords)
                    elif current_drawing_page == 2:
                        self.draw_docker_stats_page_2(renderer, coords)
                    elif current_drawing_page == 3:
                        self.draw_docker_stats_page_3(renderer, rpi_hdd_uuid, coords)
                    elif current_drawing_page == 4:
                        self.draw_docker_stats_page_4(renderer, coords)

                renderer.draw_apply()
                self._is_healthy = True
                time.sleep(self.context.display_update_interval_sec)
            except KeyboardInterrupt as error:
                self.close()
                raise error
            except Exception as error:
                logging.error("Error updating display: %s", error)
                self._is_healthy = False
                time.sleep(self.context.display_update_interval_sec)

    def close(self) -> None:
        self.is_running = False
        self.rpi_service.set_cluster_hat_alert(False)
        self.renderer_manager.close()
        self.supervisor_service.close()
        if self.rpi_service.is_cluster_hat_on():
            self.docker_service.close()
            self.remote_connection_service.close()

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        _ = frame
        logging.info("Received signal %s. Initiating shutdown...", signum)
        self.close()

    @staticmethod
    def get_context() -> ContextEntity:
        if ClusterMonitorService.singleton is None:
            raise RuntimeError("Cluster monitor singleton is not initialized")
        return ClusterMonitorService.singleton.context
