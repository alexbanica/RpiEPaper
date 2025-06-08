#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from dataclasses import dataclass
from cluster_monitor.dto.AsyncCommandCache import AsyncCommandCache

@dataclass
class AsyncCommand:
    def __init__(self):
        self.commands = {}
    def __getitem__(self, uuid: str) -> AsyncCommandCache:
        return self.commands.get(uuid)
    def __setitem__(self, uuid: str, value: AsyncCommandCache):
        self.commands[uuid] = value
    def __delitem__(self, uuid: str):
        del self.commands[uuid]
    def __contains__(self, uuid: str):
        return uuid in self.commands
    def __len__(self):
        return len(self.commands)

    def keys(self):
        return self.commands.keys()

    def values(self):
        return self.commands.values()

    def close(self) -> None:
        for command in self.commands.values():
            command.running = False
            command.results = dict()
        for command in self.commands.values():
            command.thread.join()
            logging.info("Thread %s: finishing", command.thread.name)

    def remove_result(self, key: str) -> None:
        for command in self.values():
            if key not in command.results:
                continue
            command.results.pop(key)

    def __close__(self) -> None:
        logging.debug("Closing async commands update threads, stopping...")
        self.close()