from typing import Any
from datetime import datetime
import docker
import logging
import threading
import time
from natsort import natsorted
from dataclasses import dataclass

DOCKER_UPDATE_INTERVAL_S = 1

@dataclass
class DockerServiceDetail:
    name: str
    id: str
    created: str
    updated: str
    mode: dict
    image: str
    ports: list
    replicas: int

    @property
    def image_short(self) -> str:
        return self.image.split('@')[0] if '@' in self.image else self.image

    @property
    def ports_short(self) -> list[str]:
        return [f"{port['published']}:{port['target']}" for port in self.ports]
    
    @property
    def created_short(self):
        if not self.created:
            return ''
        dt = datetime.fromisoformat(self.created.replace('Z', '+00:00'))
        return dt.strftime('%m/%d %H:%M')

    def to_list(self) -> list:
        return [self.name, self.id, self.created, self.updated, self.mode, self.image, self.ports, self.replicas]
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'id': self.id,
            'created': self.created_short,
            'updated': self.updated,
            'mode': self.mode,
            'image': self.image_short,
            'ports': self.ports_short,
            'replicas': self.replicas
        }

class DockerStats:
    def __init__(self):
        self.client = docker.from_env()
        self.services = []
        self.nodes = []
        logging.debug("Connecting to Docker daemon and performing initial update. This may take a while, please wait...")
        self._update()

        self.running = True
        self.thread = threading.Thread(target=self._docker_stats_update_task, daemon=True)
        self.thread.start()
        logging.info("DockerStats update thread [%s] started.", self.thread.name)

    def _update(self):
        try:
            self.nodes = self.client.nodes.list()
            self.services = self.client.services.list()
        except Exception as e:
            logging.error(f"Error pinging Docker daemon: {e}")
            self.nodes = []
            self.services = []

    def count_all_nodes(self) -> int:
        return len(self.nodes)

    def count_nodes_by_state(self, state: str = "ready") -> int:
        return len(self._get_nodes_by_state(state))

    def count_all_services(self) -> int:
        return len(self.services)

    def _get_nodes_by_state(self, state) -> list:
        if len(self.nodes) <= 0:
            return []
        return [node for node in self.nodes if node.attrs.get('Status', {}).get('State') == state]

    def extract_node_hostnames(self, node_state: str = "ready") -> list[Any]:
        return natsorted([node.attrs.get('Description', {}).get('Hostname') for node in self._get_nodes_by_state(node_state)])


    def extract_service_names_with_ports(self) -> list[str]:
        service_names = []
        for service in self.extract_service_details():
            ports = [f"{port['target']}" for port in service.ports]
            service_names.append(f"{service.name}:{ports}")

        return service_names

    def extract_service_details(self) -> list[DockerServiceDetail]:
        service_details = []
        for service in self.services:
            ports = []
            if 'Ports' in service.attrs.get('Endpoint', {}):
                for port in service.attrs['Endpoint']['Ports']:
                    ports.append({
                        'published': port.get('PublishedPort'),
                        'target': port.get('TargetPort'),
                        'protocol': port.get('Protocol')
                    })

            service_detail = DockerServiceDetail(
                name=service.name,
                id=service.id,
                created=service.attrs.get('CreatedAt', ''),
                updated=service.attrs.get('UpdatedAt', ''),
                mode=service.attrs.get('Spec', {}).get('Mode', {}),
                image=service.attrs.get('Spec', {}).get('TaskTemplate', {}).get('ContainerSpec', {}).get('Image', ''),
                ports=ports,
                replicas=service.attrs.get('Spec', {}).get('Mode', {}).get('Replicated', {}).get('Replicas', 0)
            )
            service_details.append(service_detail)

        return service_details

    def get_open_ports(self) -> list[int]:
        ports = []
        for service in self.services:
            if 'Ports' in service.attrs.get('Endpoint', {}):
                for port in service.attrs['Endpoint']['Ports']:
                    ports.append(port.get('PublishedPort'))
        return ports

    def _docker_stats_update_task(self):
        logging.debug("Docker update thread is starting up")
        while self.running:
            try:
                logging.debug("Updating Docker stats")
                self.nodes = self.client.nodes.list()
                self.services = self.client.services.list()
            except KeyboardInterrupt:
                logging.warning("Update interrupted by user")
                self.running = False
            except Exception as e:
                logging.error(f"Error pinging Docker daemon: %s", e)
            finally:
                time.sleep(DOCKER_UPDATE_INTERVAL_S)

    def is_busy(self) -> bool:
        if len(self.nodes) <= 0:
            return True
        if len(self.nodes) <= 0:
            return True

        return False

    def __close__(self):
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finishing", self.thread.name)
