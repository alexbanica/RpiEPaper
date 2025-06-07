#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
import uuid
import paramiko
import time
import threading
from natsort import natsorted
from dataclasses import dataclass
from typing import Optional

EXTERNAL_UPDATE_INTERVAL_S = 2

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

class RemoteService:
    def __init__(self, hostnames:list[str], username: str, ssh_key_path: str):
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.lock = threading.Lock()
        self.clients = dict()
        self._connect_all(hostnames)
        self.async_commands = AsyncCommands()
        self.is_update_processing = False
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

    def __remove_client(self, hostname: str) -> None:
        if hostname not in self.clients:
            return

        logging.debug(f"Disconnecting from %s...", hostname)
        client = self.clients.pop(hostname)
        client.close()
        self.async_commands.remove_result(hostname)
        logging.info(f"Disconnected from %s",  hostname)


    def _connect_all(self, hostnames: list[str]) -> None:
        if len(self.clients) > len(hostnames):
            logging.debug("Removing disconnected clients... %s, %s", self.clients.keys(), hostnames)
            active_client_hostnames = list(self.clients.keys())
            for active_client_hostname in active_client_hostnames:
                if active_client_hostname not in hostnames:
                    self.__remove_client(active_client_hostname)

        for active_client_hostname in hostnames:
            if active_client_hostname not in self.clients or self._is_ssh_client_closed(self.clients[active_client_hostname]):
                self.clients.setdefault(active_client_hostname, self._connect(active_client_hostname))

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
        active_client_hostnames = list(self.clients.keys())
        for hostname in active_client_hostnames:
            try:
                results[hostname] = self._execute(hostname, command)
            except Exception as e:
                logging.error(f"Error executing command on host %s: %s", hostname, e)
        return results

    def execute_on_all_async(self, command_uuid: str = None) -> None:
        self.async_commands[command_uuid].thread.start()

    def get_async_results(self, command_uuid: Optional[str]) -> dict[str, str]:
        if command_uuid not in self.async_commands:
            return {}

        results = self.async_commands[command_uuid].results
        return {k: results[k] for k in natsorted(results.keys())}

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
        if not self._are_hostnames_changed(hostnames) or self.is_update_processing:
            logging.debug("Hostnames are not changed [%s][%s]. Skipping update...", self._are_hostnames_changed(hostnames), self.is_update_processing)
            return

        self.is_update_processing = True
        thread = threading.Thread(target=self._update_hostnames_task, kwargs={'hostnames': hostnames}, daemon=True)
        thread.start()

    def _update_hostnames_task(self, hostnames: list[str]) -> None:
        logging.info(f"Reconnecting to remote hosts %s", hostnames)
        self._connect_all(hostnames)
        logging.info(f"Connected to {len(self.clients)} remote hosts")
        self.is_update_processing = False

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


