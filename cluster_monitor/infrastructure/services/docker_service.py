import logging
import threading
import time
from typing import Any

import docker
from natsort import natsorted

from cluster_monitor.domain.entities import DockerStatusEntity
from cluster_monitor.domain.services import DockerServiceInterface

DOCKER_UPDATE_INTERVAL_S = 2
DOCKER_NODE_STATE_READY = "ready"
DOCKER_NODE_STATE_DOWN = "down"


class DockerService(DockerServiceInterface):
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.low_level_client = docker.APIClient()
        self.services: list[Any] = []
        self.nodes: list[Any] = []
        self.running = True
        self._is_healthy = True

        self._update()
        self.thread = threading.Thread(target=self._docker_stats_update_task, daemon=True)
        self.thread.start()
        logging.info("Docker update thread [%s] started.", self.thread.name)

    def _update(self) -> None:
        try:
            self.nodes = self.client.nodes.list()
            self.services = self.client.services.list()
        except Exception as error:
            logging.error("Error pinging Docker daemon: %s", error)
            self.nodes = []
            self.services = []

    def count_all_nodes(self) -> int:
        return len(self.nodes)

    def count_nodes_by_state(self, state: str = DOCKER_NODE_STATE_READY) -> int:
        return len(self.get_nodes_by_state(state))

    def count_all_services(self) -> int:
        return len(self.services)

    def get_nodes_by_state(self, state: str) -> list[Any]:
        if not self.nodes:
            return []
        return [node for node in self.nodes if node.attrs.get("Status", {}).get("State") == state]

    def extract_node_hostnames(self, node_state: str = DOCKER_NODE_STATE_READY) -> list[str]:
        hostnames = [node.attrs.get("Description", {}).get("Hostname", "") for node in self.get_nodes_by_state(node_state)]
        return natsorted([hostname for hostname in hostnames if hostname])

    def extract_open_host_ports(self) -> list[int]:
        ports: list[int] = []
        for service in self.extract_service_details():
            ports.extend([int(port) for port in service.ports_short if str(port).isdigit()])
        return natsorted(ports)

    def extract_service_details(self) -> list[DockerStatusEntity]:
        service_details: list[DockerStatusEntity] = []
        for service in self.services:
            ports: list[dict[str, Any]] = []
            if "Ports" in service.attrs.get("Endpoint", {}):
                for port in service.attrs["Endpoint"]["Ports"]:
                    ports.append(
                        {
                            "published": port.get("PublishedPort"),
                            "target": port.get("TargetPort"),
                            "protocol": port.get("Protocol"),
                        }
                    )

            tasks = self.get_tasks_for_service(service.id)
            node_hostnames = [
                node.attrs.get("Description", {}).get("Hostname", "")
                for node in self._get_nodes_for_service(service.id)
            ]

            service_details.append(
                DockerStatusEntity(
                    name=service.name,
                    namespace=service.attrs.get("Spec", {}).get("Labels", {}).get("com.docker.stack.namespace", ""),
                    id=service.id,
                    created=service.attrs.get("CreatedAt", ""),
                    updated=service.attrs.get("UpdatedAt", ""),
                    mode=service.attrs.get("Spec", {}).get("Mode", {}),
                    image=service.attrs.get("Spec", {}).get("TaskTemplate", {}).get("ContainerSpec", {}).get("Image", ""),
                    ports=ports,
                    replicas=service.attrs.get("Spec", {}).get("Mode", {}).get("Replicated", {}).get("Replicas", 5),
                    running_replicas=sum(1 for task in tasks if task.get("Status", {}).get("State") == "running"),
                    deployed_to=node_hostnames,
                )
            )

        return service_details

    def get_open_ports(self) -> list[int]:
        ports: list[int] = []
        for service in self.services:
            if "Ports" in service.attrs.get("Endpoint", {}):
                for port in service.attrs["Endpoint"]["Ports"]:
                    published_port = port.get("PublishedPort")
                    if published_port is not None:
                        ports.append(published_port)
        return ports

    def _docker_stats_update_task(self) -> None:
        while self.running:
            try:
                self.nodes = self.client.nodes.list()
                self.services = self.client.services.list()
                self._is_healthy = True
            except KeyboardInterrupt:
                self.running = False
            except Exception as error:
                logging.error("Error pinging Docker daemon: %s", error)
                self._is_healthy = False
            finally:
                time.sleep(DOCKER_UPDATE_INTERVAL_S)

    def is_busy(self) -> bool:
        return len(self.nodes) <= 0

    def close(self) -> None:
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finishing", self.thread.name)

    def get_tasks_for_service(self, service_id: str) -> list[dict[str, Any]]:
        return self.low_level_client.tasks(filters={"service": service_id})

    def _get_nodes_for_service(self, service_id: str) -> list[Any]:
        service_tasks = self.get_tasks_for_service(service_id)
        node_ids = [task.get("NodeID") for task in service_tasks if task.get("Status", {}).get("State") == "running"]
        return [node for node in self.nodes if node.id in node_ids]

    def is_healthy(self) -> bool:
        if not self._is_healthy:
            logging.error("Docker daemon is not healthy. Please check logs.")
        return self._is_healthy
