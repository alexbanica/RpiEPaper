#!/usr/bin/python
# -*- coding:utf-8 -*-
from asyncio import tasks

import docker
import logging
import threading
import time

from natsort import natsorted
from typing import Any
from cluster_monitor.dto import DockerStatus

DOCKER_UPDATE_INTERVAL_S = 2
NODE_DOWN_THRESHOLD_S = 300  # 5 minutes


class DockerService:
    def __init__(self):
        self.client = docker.from_env()
        self.low_level_client = docker.APIClient()
        self.services = []
        self.nodes = []
        self.node_down_times = {}
        logging.debug("Connecting to Docker daemon and performing initial update. This may take a while, please wait...")
        self._update()

        self.running = True
        self._is_healthy = True
        self.thread = threading.Thread(target=self._docker_stats_update_task, daemon=True)
        self.thread.start()
        logging.info("Docker update thread [%s] started.", self.thread.name)

    def _update(self) -> None:
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


    def extract_service_names(self) -> list[str]:
        service_names = []
        for service in self.extract_service_details():
            service_names.append(f"{service.name_short[:3]}")

        return service_names
    def extract_open_host_ports(self) -> list[int]:
        ports = []
        for service in self.extract_service_details():
            ports.extend(service.ports_short)
        return natsorted(ports)

    def extract_service_details(self) -> list[DockerStatus]:
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

            tasks = self.get_tasks_for_service(service.id)
            node_hostnames = [node.attrs.get('Description', {}).get('Hostname', '') for node in self._get_nodes_for_service(service.id)]

            service_detail = DockerStatus(
                name=service.name,
                namespace=service.attrs.get('Spec', {}).get('Labels', {}).get('com.docker.stack.namespace', ''),
                id=service.id,
                created=service.attrs.get('CreatedAt', ''),
                updated=service.attrs.get('UpdatedAt', ''),
                mode=service.attrs.get('Spec', {}).get('Mode', {}),
                image=service.attrs.get('Spec', {}).get('TaskTemplate', {}).get('ContainerSpec', {}).get('Image', ''),
                ports=ports,
                replicas=service.attrs.get('Spec', {}).get('Mode', {}).get('Replicated', {}).get('Replicas', 5),
                running_replicas=sum(1 for task in tasks if task['Status']['State'] == 'running'),
                deployed_to=node_hostnames
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

    def _docker_stats_update_task(self) -> None:
        logging.debug("Docker update thread is starting up")
        while self.running:
            try:
                logging.debug("Updating Docker stats")
                self.nodes = self.client.nodes.list()
                self.services = self.client.services.list()
                self._update_node_down_times()
                self._is_healthy = True
            except KeyboardInterrupt:
                logging.warning("Update interrupted by user")
                self.running = False
            except Exception as e:
                logging.error(f"Error pinging Docker daemon: %s", e)
                self._is_healthy = False
            finally:
                time.sleep(DOCKER_UPDATE_INTERVAL_S)

    def is_busy(self) -> bool:
        if len(self.nodes) <= 0:
            return True
        if len(self.nodes) <= 0:
            return True

        return False

    def __close__(self) -> None:
        logging.debug("Closing DockerStats update thread")
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finishing", self.thread.name)

    def get_tasks_for_service(self, service_id: str) -> list:
        return self.low_level_client.tasks(filters={"service": service_id})

    def _get_nodes_for_service(self, service_id: str) -> list:
        service_tasks = self.get_tasks_for_service(service_id)
        nodes = []
        node_ids = []
        for task in service_tasks:
            if task['Status']['State'] != 'running':
                continue
            node_ids.append(task.get('NodeID'))

        for node in self.nodes:
            if node.id not in node_ids:
                continue
            nodes.append(node)

        return nodes

    def is_healthy(self) -> bool:
        if not self._is_healthy:
            logging.error("Docker daemon is not healthy. Please check the logs for more details.")
        return self._is_healthy

    def _update_node_down_times(self) -> None:
        current_time = time.time()
        down_nodes = self._get_nodes_by_state('down')
        down_hostnames = {node.attrs.get('Description', {}).get('Hostname') for node in down_nodes}

        for node in down_nodes:
            hostname = node.attrs.get('Description', {}).get('Hostname')
            if hostname not in self.node_down_times:
                self.node_down_times[hostname] = current_time

        self.node_down_times = {hostname: timestamp
                                for hostname, timestamp in self.node_down_times.items()
                                if hostname in down_hostnames}
        logging.debug("Node down times: %s", self.node_down_times)

    def get_long_down_node_hostnames(self) -> list[str]:
        current_time = time.time()
        return [hostname for hostname, down_time in self.node_down_times.items()
                if (current_time - down_time) > NODE_DOWN_THRESHOLD_S]
