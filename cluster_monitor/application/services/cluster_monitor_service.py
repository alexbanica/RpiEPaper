import logging
import signal
import threading
import time
from typing import Optional

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import (
    DockerServiceInterface,
    RemoteServiceInterface,
    RendererManagerInterface,
    RpiServiceInterface,
    SupervisorServiceInterface,
)
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
        renderer_manager: RendererManagerInterface,
    ):
        self.is_running = True
        self._is_healthy = True
        self.context = context
        self.rpi_service = rpi_service
        self.docker_service = docker_service
        self.supervisor_service = supervisor_service
        self.renderer_manager = renderer_manager
        self.remote_connection_service = remote_service
        self._frame_gate = threading.RLock()
        self._close_condition = threading.Condition()
        self._close_state = "open"
        self._close_owner = None
        self._close_error = None
        self._start_thread_id = None
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
        self._start_thread_id = threading.get_ident()
        try:
            renderer = self.renderer_manager.get_renderer()
            rpi_stats_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_status_command)
            rpi_hdd_uuid = self.remote_connection_service.attach_command(self.context.remote_ssh_rpi_hdd_status_command)
            self.remote_connection_service.execute_on_all_async(rpi_stats_uuid)
            self.remote_connection_service.execute_on_all_async(rpi_hdd_uuid)

            current_drawing_page = renderer.get_controller().get_current_page()
            while self.is_running:
                try:
                    with self._frame_gate:
                        if not self.is_running:
                            break
                        with renderer.frame_transaction():
                            next_page = renderer.get_controller().get_current_page()
                            page_changed = current_drawing_page != next_page
                            if page_changed:
                                current_drawing_page = next_page
                                renderer.hard_refresh()
                            else:
                                self.rpi_service.set_cluster_hat_alert(not self.is_healthy())
                                renderer.refresh()
                                self.remote_connection_service.update_hostnames(self.docker_service.extract_node_hostnames())
                                renderer.draw_text(self.rpi_service.get_current_time() + renderer.draw_pagination(), NULL_COORDS, RENDER_ALIGN_RIGHT)
                                coords = renderer.draw_text(self.rpi_service.render_cluster_hat_status())
                                coords = renderer.draw_new_section(coords)
                                if self._is_busy():
                                    renderer.draw_loading(coords)
                                elif not self.rpi_service.is_cluster_hat_on():
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
                    if page_changed:
                        time.sleep(0.5)
                        continue
                    self._is_healthy = True
                    time.sleep(self.context.display_update_interval_sec)
                except KeyboardInterrupt:
                    self.is_running = False
                    raise
                except Exception as error:
                    if not self.is_running:
                        break
                    logging.error("Error updating display: %s", error)
                    self._is_healthy = False
                    time.sleep(self.context.display_update_interval_sec)
        finally:
            self.is_running = False
            self._close_resources()

    def close(self) -> None:
        self.is_running = False
        # The run owner may be inside a frame. Its start() finally block owns
        # teardown after that frame unwinds.
        if self._start_thread_id == threading.get_ident():
            return
        self._close_resources()

    def _close_resources(self) -> None:
        # Serialize teardown with every application frame, including console frames
        # whose renderer transaction may be a no-op. RLock preserves safe reentry
        # when a cleanup callback closes the monitor on the teardown owner thread.
        with self._frame_gate:
            self._close_resources_under_frame_gate()

    def _close_resources_under_frame_gate(self) -> None:
        current = threading.get_ident()
        with self._close_condition:
            while self._close_state == "closing" and self._close_owner != current:
                self._close_condition.wait()
            if self._close_state == "closed":
                if self._close_error is not None:
                    raise self._close_error
                return
            if self._close_state == "closing":
                return
            self._close_state = "closing"
            self._close_owner = current

        failures = []
        for label, action in (
            ("cluster hat alert reset", lambda: self.rpi_service.set_cluster_hat_alert(False)),
            ("renderer", self.renderer_manager.close),
            ("supervisor", self.supervisor_service.close),
            ("Docker collection", self.docker_service.close),
            ("remote collection", self.remote_connection_service.close),
        ):
            try:
                action()
            except Exception as error:
                failures.append(error)
                logging.exception("Failed to close %s", label)
        with self._close_condition:
            self._close_error = failures[0] if failures else None
            self._close_state = "closed"
            self._close_owner = None
            self._close_condition.notify_all()
        if failures:
            raise failures[0]

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        _ = frame
        logging.info("Received signal %s. Initiating shutdown...", signum)
        self.is_running = False

    @staticmethod
    def get_context() -> ContextEntity:
        if ClusterMonitorService.singleton is None:
            raise RuntimeError("Cluster monitor singleton is not initialized")
        return ClusterMonitorService.singleton.context
