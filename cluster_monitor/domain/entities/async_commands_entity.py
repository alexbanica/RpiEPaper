import logging
from typing import Optional

from cluster_monitor.domain.entities.async_command_cache_entity import AsyncCommandCacheEntity


class AsyncCommandsEntity:
    def __init__(self) -> None:
        self.commands: dict[str, AsyncCommandCacheEntity] = {}

    def __getitem__(self, uuid: str) -> Optional[AsyncCommandCacheEntity]:
        return self.commands.get(uuid)

    def __setitem__(self, uuid: str, value: AsyncCommandCacheEntity) -> None:
        self.commands[uuid] = value

    def __contains__(self, uuid: str) -> bool:
        return uuid in self.commands

    def values(self):
        return self.commands.values()

    def close(self) -> None:
        for command in self.commands.values():
            command.running = False
            command.results = {}
        for command in self.commands.values():
            command.thread.join()
            logging.info("Thread %s: finishing", command.thread.name)

    def remove_result(self, key: str) -> None:
        for command in self.commands.values():
            command.results.pop(key, None)
