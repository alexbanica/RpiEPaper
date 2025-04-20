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

    def get_keys(self):
        return self.commands.keys()

    def __close__(self) -> None:
        logging.debug("Closing async commands update threads, stopping...")
        for command in self.commands.values():
            command.running = False

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

    def _is_ssh_client_closed(self, ssh_client: paramiko.SSHClient) -> bool:
        transport = ssh_client.get_transport()
        return not (transport and transport.is_active())


    def _connect_all(self, hostnames: list[str]) -> None:
        for hostname in hostnames:
            if hostname not in self.clients or self._is_ssh_client_closed(self.clients[hostname]):
                self.clients.setdefault(hostname, self._connect(hostname))

    def __close__(self) -> None:
        self.async_commands.__close__()
        logging.debug("Closing SSH connections...")
        for client in self.clients.values():
            client.close()

    def __create_command_background_thread(self, command_uuid: str) -> threading.Thread:
        return threading.Thread(target=self._command_update_task, kwargs={'command_uuid': command_uuid}, daemon=True)

    def attach_command(self, command: str, command_uuid: Optional[str] = None) -> str:
        command_uuid = command_uuid if command_uuid is not None else str(uuid.uuid5(uuid.NAMESPACE_DNS, command))
        self.async_commands[command_uuid] = AsyncCommandCacheDto(
            command_uuid,
            command,
            True,
            {},
           self.__create_command_background_thread(command_uuid)
        )
        logging.debug(f"Attached command %s [%s] to async commands cache", command, command_uuid)
        return command_uuid

    def _execute(self, hostname: str, command: str) -> str:
        stdin, stdout, stderr = self.clients[hostname].exec_command(command)
        output = stdout.read().decode().strip()  # Decode and clean output
        error = stderr.read().decode().strip()  # Capture errors (if any)

        if error:
            raise Exception(f"Error executing command: {error}")
        return output

    def _execute_on_all(self, command: str) -> dict[str, str]:
        results = {}
        for hostname in self.clients.keys():
            results[hostname] = self._execute(hostname, command)
        return results

    def execute_on_all_async(self, command_uuid: str = None) -> str:
        self.async_commands[command_uuid].thread.start()

    def get_async_results(self, uuid: Optional[str]) -> dict[str, str]:
        if uuid not in self.async_commands:
            return {}

        return self.async_commands[uuid].results

    def _command_update_task(self, command_uuid) -> None:
        if command_uuid not in self.async_commands:
            raise Exception(f"Command update thread for command [%s] not found in async commands cache", uuid)

        command = self.async_commands[command_uuid].command
        logging.debug(f"Command %s [%s] results update thread is starting", command, uuid)
        while self.async_commands[command_uuid].running:
            try:
                self.async_commands[command_uuid].results = self._execute_on_all(command)
                logging.debug("Updated results for command %s", command)
            except KeyboardInterrupt:
                logging.warning("Update command results interrupted by user")
                self.async_commands[command_uuid].running = False
            except Exception as e:
                logging.error(f"Error gathering results for command %s: %s", command, e)
            finally:
                time.sleep(EXTERNAL_UPDATE_INTERVAL_S)
        logging.debug(f"Command %s [%s] results update thread has finished", command, command_uuid)

    def _are_hostnames_changed(self, new_hostnames: list[str]) -> bool:
        if len(new_hostnames) != len(self.clients):
            return True
        return not all(hostname in self.clients for hostname in new_hostnames)

    def update_hostnames(self, hostnames: list[str]) -> None:
        if not self._are_hostnames_changed(hostnames):
            return

        logging.info(f"Reconnecting to remote hosts %s", hostnames)
        self.async_commands.__close__()
        self._connect_all(hostnames)
        for key in self.async_commands.get_keys():
            self.attach_command(self.async_commands[key].command, key)
            self.execute_on_all_async(key)

        logging.info(f"Connected to {len(self.clients)} remote hosts")


