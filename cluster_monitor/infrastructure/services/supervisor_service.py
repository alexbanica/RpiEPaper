import logging
import threading
import time

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import DockerServiceInterface, RpiServiceInterface, SupervisorServiceInterface
from cluster_monitor.infrastructure.services.docker_service import DOCKER_NODE_STATE_DOWN

NODE_REVIVER_THREAD_CHECK_S = 2


class SupervisorService(SupervisorServiceInterface):
    def __init__(self, context: ContextEntity, docker_service: DockerServiceInterface, rpi_service: RpiServiceInterface):
        self.running = True
        self._is_healthy = True
        self.context = context
        self.docker_service = docker_service
        self.rpi_service = rpi_service
        self.node_down_times: dict[str, float] = {}

        self.thread_down_node_reviver = threading.Thread(target=self._down_node_reviver, daemon=True)
        self.thread_down_node_reviver.start()
        logging.info("Thread [%s] started.", self.thread_down_node_reviver.name)

    def _down_node_reviver(self) -> None:
        while self.running:
            try:
                self._update_node_down_times()
                self.rpi_service.restart_nodes(self._get_down_nodes())
                self._is_healthy = True
            except KeyboardInterrupt:
                self.running = False
            except Exception as error:
                logging.error("Error on supervisor node reviver: %s", error)
                self._is_healthy = False
            finally:
                time.sleep(NODE_REVIVER_THREAD_CHECK_S)

    def _update_node_down_times(self) -> None:
        current_time = time.time()
        down_nodes = self.docker_service.get_nodes_by_state(DOCKER_NODE_STATE_DOWN)
        down_hostnames = {node.attrs.get("Description", {}).get("Hostname") for node in down_nodes}

        for node in down_nodes:
            hostname = node.attrs.get("Description", {}).get("Hostname")
            if hostname and hostname not in self.node_down_times:
                self.node_down_times[hostname] = current_time

        self.node_down_times = {
            hostname: timestamp
            for hostname, timestamp in self.node_down_times.items()
            if hostname in down_hostnames
        }

    def _get_down_nodes(self) -> list[str]:
        current_time = time.time()
        hostnames = [
            hostname
            for hostname, down_time in self.node_down_times.items()
            if (current_time - down_time) > self.context.docker_node_down_threshold_sec
        ]

        for hostname in hostnames:
            self.node_down_times.pop(hostname, None)

        return hostnames

    def close(self) -> None:
        self.running = False
        self.thread_down_node_reviver.join()
        logging.info("Thread %s: finishing", self.thread_down_node_reviver.name)

    def is_healthy(self) -> bool:
        if not self._is_healthy:
            logging.error("Supervisor is not healthy. Please check logs.")
        return self._is_healthy
