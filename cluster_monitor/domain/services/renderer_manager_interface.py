from abc import ABC, abstractmethod

from cluster_monitor.domain.services.renderer_interface import RendererInterface


class RendererManagerInterface(ABC):
    @abstractmethod
    def get_renderer(self) -> RendererInterface:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
