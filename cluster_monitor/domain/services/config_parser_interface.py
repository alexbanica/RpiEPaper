from abc import ABC, abstractmethod

from cluster_monitor.domain.entities import ContextEntity


class ConfigParserInterface(ABC):
    @abstractmethod
    def parse(self, context: ContextEntity, config_file_names: list[str]) -> None:
        raise NotImplementedError
