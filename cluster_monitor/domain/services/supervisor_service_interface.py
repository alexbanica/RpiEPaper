from abc import ABC, abstractmethod


class SupervisorServiceInterface(ABC):
    @abstractmethod
    def is_healthy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
