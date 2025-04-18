import docker
import logging
import threading
import time
from natsort import natsorted

DOCKER_UPDATE_INTERVAL_S = 5
class DockerStats:
    def __init__(self):
        self.client = docker.from_env()
        self._update()

        self.running = True
        self.thread = threading.Thread(target=self.run_task, daemon=True)
        self.thread.start()
        logging.info("DockerStats thread started. Waiting for Docker daemon to start...")

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
            return [node for node in self.nodes if node.attrs.get('Status', {}).get('State') == state]

    def extract_node_hostnames(self, node_state: str = "ready") -> list[str]:
        return [node.attrs.get('Description', {}).get('Hostname') for node in self._get_nodes_by_state(node_state)]

    def extract_service_names(self) -> list[str]:
        return natsorted([service.name for service in self.services])

    def run_task(self):
        logging.debug("Update thread is starting")
        while self.running:
            try:
                logging.debug("Updating Docker stats")
                self.nodes = self.client.nodes.list()
                self.services = self.client.services.list()
            except KeyboardInterrupt:
                logging.warning("Update interrupted by user")
                self.running = False
                raise
            except Exception as e:
                logging.error(f"Error pinging Docker daemon: {e}")
            time.sleep(DOCKER_UPDATE_INTERVAL_S)

    def __close__(self):
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finishing", self.thread.name)
