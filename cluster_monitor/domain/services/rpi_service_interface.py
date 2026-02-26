from abc import ABC, abstractmethod
from typing import Optional

from cluster_monitor.domain.entities import ClusterHatStatusEntity, DiskUsageInfoEntity


class RpiServiceInterface(ABC):
    @abstractmethod
    def get_current_time(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_hostname(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_clusterhat_status(self) -> ClusterHatStatusEntity:
        raise NotImplementedError

    @abstractmethod
    def is_cluster_hat_on(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_disk_usages(self, disks: Optional[list[str]] = None) -> list[DiskUsageInfoEntity]:
        raise NotImplementedError

    @abstractmethod
    def render_cluster_hat_status(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def render_stats(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_lines_from_file(self, filename: str, nr_lines: int = 10) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def render_logs(self, lines: list[str]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def restart_nodes(self, hostnames: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_cluster_hat_alert(self, enable: bool) -> None:
        raise NotImplementedError
