from abc import ABC, abstractmethod
from typing import Any

from cluster_monitor.domain.entities import DockerStatusEntity


class DockerServiceInterface(ABC):
    @abstractmethod
    def count_all_nodes(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_nodes_by_state(self, state: str = "ready") -> int:
        raise NotImplementedError

    @abstractmethod
    def count_all_services(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_nodes_by_state(self, state: str) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    def extract_node_hostnames(self, node_state: str = "ready") -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def extract_open_host_ports(self) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def extract_service_details(self) -> list[DockerStatusEntity]:
        raise NotImplementedError

    @abstractmethod
    def get_open_ports(self) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def is_busy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
