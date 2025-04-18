import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import paramiko
import time
import threading

EXTERNAL_UPDATE_INTERVAL_S = 5

@dataclass
class AsyncCommandCacheDto:
    uuid: str
    command: str
    running: bool
    results: dict[str, str]
    thread: threading.Thread

@dataclass
class AsyncCommands:
    def __init__(self):
        self.commands = {}

    def __getitem__(self, uuid: str) -> AsyncCommandCacheDto:
        return self.commands.get(uuid)
    def __setitem__(self, uuid: str, value: AsyncCommandCacheDto):
        self.commands[uuid] = value
    def __delitem__(self, uuid: str):
        del self.commands[uuid]
    def __contains__(self, uuid: str):
        return uuid in self.commands
    def __len__(self):
        return len(self.commands)

    def __close__(self) -> None:
        logging.debug("Closing async commands update threads...")
        for command in self.commands.values():
            command.running = False

        for command in self.commands.values():
            command.thread.join()
            logging.info("Command %s having update thread %s: finishing", command.uuid, command.thread.name)

class RemoteConnectionManager:
    def __init__(self, hostnames:list[str], username: str = "alexbanica", ssh_key_path: str = "/home/alexbanica/.ssh/id_rsa"):
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.clients = {}
        self._connect_all(hostnames)
        self.async_commands = AsyncCommands()
        logging.info(f"Connected to {len(self.clients)} remote hosts")

    def _connect(self, hostname: str) -> paramiko.SSHClient:
        logging.debug(f"Connecting to {hostname}...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Use the provided SSH key for authentication
        ssh_client.connect(
            hostname,
            username=self.username,
            key_filename=self.ssh_key_path
        )
        logging.debug(f"Connected to {hostname}")

        return ssh_client

    def _connect_all(self, hostnames: list[str]) -> None:
        for hostname in hostnames:
            self.clients.setdefault(hostname, self._connect(hostname))

    def __close__(self) -> None:
        self.async_commands.__close__()
        logging.debug("Closing SSH connections...")
        for client in self.clients.values():
            client.close()


    def execute(self, hostname: str, command: str) -> str:
        stdin, stdout, stderr = self.clients[hostname].exec_command(command)
        output = stdout.read().decode().strip()  # Decode and clean output
        error = stderr.read().decode().strip()  # Capture errors (if any)

        if error:
            raise Exception(f"Error executing command: {error}")
        return output

    def execute_on_all(self, command: str) -> dict[str, str]:
        results = {}
        for hostname in self.clients.keys():
            results[hostname] = self.execute(hostname, command)
        return results

    def execute_on_all_async(self, command: str, command_uuid: str = None) -> str:
        command_uuid = command_uuid if command_uuid is not None else str(uuid.uuid5(uuid.NAMESPACE_DNS, command))
        self.async_commands[command_uuid] = AsyncCommandCacheDto(
            command_uuid,
            command,
            True,
            {},
            threading.Thread(target=self._command_update_task, args=(command_uuid, command, None))
        )
        self.async_commands[command_uuid].thread.start()

        return command_uuid

    def get_async_results(self, uuid: Optional[str]) -> dict[str, str]:
        if uuid not in self.async_commands:
            return {}

        return self.async_commands[uuid].results

    def _command_update_task(self, uuid: str, command: str, args) -> None:
        logging.debug(f"Command %s [%s] results update thread is starting", command, uuid)

        while self.async_commands[uuid].running:
            try:
                self.async_commands[uuid].results = self.execute_on_all(command)
                logging.debug("Updated results for command %s", command)
            except KeyboardInterrupt:
                logging.warning("Update command results interrupted by user")
                self.async_commands[uuid].running = False
            except Exception as e:
                logging.error(f"Error gathering results for command %s: %s", command, e)
            finally:
                time.sleep(EXTERNAL_UPDATE_INTERVAL_S)

    def _are_hostnames_changed(self, new_hostnames: list[str]) -> bool:
        if len(new_hostnames) != len(self.clients):
            return True
        return not all(hostname in self.clients for hostname in new_hostnames)

    def update_hostnames(self, hostnames: list[str]) -> bool:
        if not self._are_hostnames_changed(hostnames):
            return True

        logging.info(f"Reconnecting to remote hosts %s", hostnames)
        self.async_commands.__close__()
        self._connect_all(hostnames)
        old_commands = self.async_commands
        self.async_commands = AsyncCommands()
        if old_commands.__len__() == 0:
            return False

        for command in old_commands:
            self.execute_on_all_async(command.command, command.uuid)

        logging.info(f"Connected to {len(self.clients)} remote hosts")

        #         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # File "/mnt/data/ePaperHat/src/RemoteConnectionManager.py", line 147, in update_hostnames
        # self.execute_on_all_async(command.command, command.uuid)
        # ^^^^^^^^^^^^^^^
        # AttributeError: 'NoneType' object has no attribute 'command'
        return True


