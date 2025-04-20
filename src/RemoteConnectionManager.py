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

    def keys(self):
        return self.commands.keys()

    def values(self):
        return self.commands.values()

    def close(self, command_uuid: Optional[str] = None) -> None:
        if command_uuid is None:
            for command in self.commands.values():
                command.running = False
                command.results = {}
            return

        if command_uuid not in self.commands:
            return
        self.commands[command_uuid].running = False
        self.commands[command_uuid].command.results = {}


    def __close__(self) -> None:
        logging.debug("Closing async commands update threads, stopping...")
        self.close()

class RemoteConnectionManager:
    def __init__(self, hostnames:list[str], username: str = "alexbanica", ssh_key_path: str = "/home/alexbanica/.ssh/id_rsa"):
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.clients = {}
        self.lock = threading.Lock()
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
        if len(self.clients) > len(hostnames):
            for hostname in self.clients.keys():
                if hostname not in hostnames:
                    client = self.clients.pop(hostname)
                    client.close()
                    logging.info(f"Disconnected from %s",  hostname)
            return

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
            try:
                results[hostname] = self._execute(hostname, command)
            except Exception as e:
                logging.error(f"Error executing command on host %s: %s", hostname, e)
                del results[hostname]
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
                self.lock.acquire()
                self.async_commands[command_uuid].results = self._execute_on_all(command)
                logging.debug("Updated results for command %s", command)
            except KeyboardInterrupt:
                logging.warning("Update command results interrupted by user")
                self.async_commands[command_uuid].running = False
            finally:
                self.lock.release()
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
        self.lock.acquire()
        self._connect_all(hostnames)
        self.lock.release()
        logging.info(f"Connected to {len(self.clients)} remote hosts")

    def is_busy(self, command_uuid: Optional[str] = None) -> bool:
        if command_uuid is None:
            for command in self.async_commands.values():
                if command.running and len(command.results) == 0:
                    return True
            return False

        if command_uuid not in self.async_commands:
            logging.warning(f"Command [%s] not found in async commands cache", command_uuid)
            return False

        return self.async_commands[command_uuid].running and len(self.async_commands[command_uuid].results) == 0


