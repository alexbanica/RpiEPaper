from abc import ABC, abstractmethod
from typing import Optional


class RemoteServiceInterface(ABC):
    @abstractmethod
    def attach_command(self, command: str, command_uuid: Optional[str] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute_on_all_async(self, command_uuid: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_async_results(self, command_uuid: Optional[str]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def update_hostnames(self, hostnames: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_busy(self, command_uuid: Optional[str] = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
