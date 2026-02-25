import logging
import threading
import time
import uuid
from typing import Optional

import paramiko
from natsort import natsorted

from cluster_monitor.domain.entities import AsyncCommandCacheEntity, AsyncCommandsEntity
from cluster_monitor.domain.services import RemoteServiceInterface

EXTERNAL_UPDATE_INTERVAL_S = 2


class RemoteService(RemoteServiceInterface):
    def __init__(self, hostnames: list[str], username: str, ssh_key_path: str):
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.lock = threading.Lock()
        self.clients: dict[str, paramiko.SSHClient] = {}
        self.async_commands = AsyncCommandsEntity()
        self.is_update_processing = False
        self._connect_all(hostnames)
        logging.info("Connected to %s remote hosts", len(self.clients))

    def _connect(self, hostname: str) -> paramiko.SSHClient:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=self.username, key_filename=self.ssh_key_path, timeout=10)
        ssh_client.get_transport().set_keepalive(30)
        return ssh_client

    def _is_ssh_client_closed(self, ssh_client: paramiko.SSHClient) -> bool:
        transport = ssh_client.get_transport()
        return not (transport and transport.is_active())

    def _remove_client(self, hostname: str) -> None:
        client = self.clients.pop(hostname, None)
        if client:
            client.close()
        self.async_commands.remove_result(hostname)

    def _connect_all(self, hostnames: list[str]) -> None:
        for active_hostname in list(self.clients.keys()):
            if active_hostname not in hostnames:
                self._remove_client(active_hostname)

        for hostname in hostnames:
            if hostname in self.clients and self._is_ssh_client_closed(self.clients[hostname]):
                self._remove_client(hostname)

            if hostname not in self.clients:
                try:
                    self.clients[hostname] = self._connect(hostname)
                except Exception as error:
                    logging.error("Error connecting to host %s: %s", hostname, error)

    def close(self) -> None:
        self.async_commands.close()
        for client in self.clients.values():
            client.close()

    def _create_command_background_thread(self, command_uuid: str) -> threading.Thread:
        return threading.Thread(target=self._command_update_task, kwargs={"command_uuid": command_uuid}, daemon=True)

    def attach_command(self, command: str, command_uuid: Optional[str] = None) -> str:
        generated_uuid = command_uuid or str(uuid.uuid5(uuid.NAMESPACE_DNS, command))
        self.async_commands[generated_uuid] = AsyncCommandCacheEntity(
            uuid=generated_uuid,
            command=command,
            running=True,
            results={},
            thread=self._create_command_background_thread(generated_uuid),
        )
        return generated_uuid

    def _execute(self, hostname: str, command: str) -> str:
        _, stdout, stderr = self.clients[hostname].exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if error:
            raise RuntimeError(error)
        return output

    def _execute_on_all(self, command: str) -> dict[str, str]:
        results: dict[str, str] = {}
        for hostname in list(self.clients.keys()):
            try:
                results[hostname] = self._execute(hostname, command)
            except Exception as error:
                logging.error("Error executing command on host %s: %s", hostname, error)
                self._remove_client(hostname)
        return results

    def execute_on_all_async(self, command_uuid: str) -> None:
        command = self.async_commands[command_uuid]
        if command:
            command.thread.start()

    def get_async_results(self, command_uuid: Optional[str]) -> dict[str, str]:
        if not command_uuid or command_uuid not in self.async_commands:
            return {}
        command = self.async_commands[command_uuid]
        if not command:
            return {}
        return {key: command.results[key] for key in natsorted(command.results.keys())}

    def _command_update_task(self, command_uuid: str) -> None:
        command = self.async_commands[command_uuid]
        if not command:
            return

        while command.running:
            try:
                with self.lock:
                    command.results = self._execute_on_all(command.command)
            except KeyboardInterrupt:
                command.running = False
            finally:
                time.sleep(EXTERNAL_UPDATE_INTERVAL_S)

    def _are_hostnames_changed(self, new_hostnames: list[str]) -> bool:
        if len(new_hostnames) != len(self.clients):
            return True
        return not all(hostname in self.clients for hostname in new_hostnames)

    def update_hostnames(self, hostnames: list[str]) -> None:
        if not self._are_hostnames_changed(hostnames) or self.is_update_processing:
            return

        self.is_update_processing = True
        thread = threading.Thread(target=self._update_hostnames_task, kwargs={"hostnames": hostnames}, daemon=True)
        thread.start()

    def _update_hostnames_task(self, hostnames: list[str]) -> None:
        self._connect_all(hostnames)
        self.is_update_processing = False

    def is_busy(self, command_uuid: Optional[str] = None) -> bool:
        if command_uuid is None:
            return any(command.running and len(command.results) == 0 for command in self.async_commands.values())

        command = self.async_commands[command_uuid] if command_uuid in self.async_commands else None
        if command is None:
            return False
        return command.running and len(command.results) == 0

    def is_healthy(self) -> bool:
        return all(not self._is_ssh_client_closed(client) for client in self.clients.values())
