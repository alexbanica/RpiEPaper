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
        # Lock order: execution_lock may be acquired before lock, never the
        # reverse. lock protects snapshots and lifecycle state; execution_lock
        # serializes every client operation with reconciliation and cleanup.
        # Never call a client method or wait for a worker while holding lock.
        self.lock = threading.Lock()
        self.execution_lock = threading.Lock()
        self.clients: dict[str, paramiko.SSHClient] = {}
        self.async_commands = AsyncCommandsEntity()
        self.is_update_processing = False
        self._update_worker: Optional[threading.Thread] = None
        self._closed = False
        self._close_owner: Optional[int] = None
        self._close_complete = threading.Event()
        with self.execution_lock:
            self._connect_all(list(hostnames))
        with self.lock:
            client_count = len(self.clients)
        logging.info("Connected to %s remote hosts", client_count)

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
        """Remove a client while execution_lock excludes concurrent use."""
        with self.lock:
            client = self.clients.pop(hostname, None)
            for command in self.async_commands.values():
                command.results.pop(hostname, None)
        if client:
            try:
                client.close()
            except Exception as error:
                logging.error("Error closing connection to host %s: %s", hostname, error)

    def _connect_all(self, hostnames: list[str]) -> None:
        """Reconcile clients while holding execution_lock, never lock over I/O."""
        with self.lock:
            active_hostnames = list(self.clients.keys())
        for active_hostname in active_hostnames:
            if active_hostname not in hostnames:
                self._remove_client(active_hostname)

        for hostname in hostnames:
            with self.lock:
                client = self.clients.get(hostname)
            if client and self._is_ssh_client_closed(client):
                self._remove_client(hostname)

            with self.lock:
                needs_connection = hostname not in self.clients and not self._closed
            if needs_connection:
                try:
                    client = self._connect(hostname)
                    with self.lock:
                        if self._closed:
                            keep_client = False
                        else:
                            self.clients[hostname] = client
                            keep_client = True
                    if not keep_client:
                        client.close()
                except Exception as error:
                    logging.error("Error connecting to host %s: %s", hostname, error)

    def close(self) -> None:
        current_thread = threading.current_thread()
        current_ident = threading.get_ident()
        with self.lock:
            if self._closed:
                already_closing = True
                update_worker = self._update_worker
                command_threads = [command.thread for command in self.async_commands.values()]
                reentrant_close = self._close_owner == current_ident
            else:
                already_closing = False
                self._closed = True
                self._close_owner = current_ident
                update_worker = self._update_worker
                commands = list(self.async_commands.values())
                command_threads = [command.thread for command in commands]
                for command in commands:
                    command.running = False
                    command.mark_initial_collection_complete()

        if already_closing:
            # Neither a reentrant close callback nor a worker may wait for the
            # close operation that is currently waiting on it.
            if reentrant_close or current_thread is update_worker or current_thread in command_threads:
                return
            self._close_complete.wait()
            return

        if current_thread is update_worker or current_thread in command_threads:
            cleanup_worker = threading.Thread(
                target=self._complete_close_from_worker,
                args=(update_worker, command_threads),
                daemon=True,
            )
            cleanup_worker.start()
            return

        self._complete_close(update_worker, command_threads)

    def _complete_close_from_worker(
        self,
        update_worker: Optional[threading.Thread],
        command_threads: list[threading.Thread],
    ) -> None:
        try:
            self._complete_close(update_worker, command_threads)
        except Exception as error:
            logging.error("Error completing remote service close: %s", error)

    def _complete_close(
        self,
        update_worker: Optional[threading.Thread],
        command_threads: list[threading.Thread],
    ) -> None:
        # A close initiated by one of the service workers is completed by a
        # separate thread so that it can join that worker after it unwinds.
        current_thread = threading.current_thread()
        with self.lock:
            self._close_owner = threading.get_ident()
        failure = None
        try:
            if update_worker and update_worker is not current_thread:
                try:
                    update_worker.join()
                except Exception as error:
                    failure = error
            for worker in command_threads:
                # Commands can be attached before they are started. Joining an
                # unstarted thread raises RuntimeError; the current worker must
                # also never join itself.
                if worker is not current_thread and worker.ident is not None:
                    try:
                        worker.join()
                    except Exception as error:
                        if failure is None:
                            failure = error

            with self.execution_lock:
                with self.lock:
                    for command in self.async_commands.values():
                        command.results = {}
                    clients = list(self.clients.items())
                    self.clients.clear()
            # All workers have stopped and closure prevents new ones, so
            # cleanup runs without either service lock and cannot race use.
            for hostname, client in clients:
                try:
                    client.close()
                except Exception as error:
                    logging.error("Error closing connection to host %s: %s", hostname, error)
                    if failure is None:
                        failure = error
        finally:
            self._close_complete.set()
            with self.lock:
                self._close_owner = None

        if failure is not None:
            raise failure

    def _create_command_background_thread(self, command_uuid: str) -> threading.Thread:
        return threading.Thread(target=self._command_update_task, kwargs={"command_uuid": command_uuid}, daemon=True)

    def attach_command(self, command: str, command_uuid: Optional[str] = None) -> str:
        generated_uuid = command_uuid or str(uuid.uuid5(uuid.NAMESPACE_DNS, command))
        with self.lock:
            if self._closed:
                return generated_uuid
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
        try:
            exit_status = stdout.channel.recv_exit_status()
        except Exception as status_error:
            raise RuntimeError(f"Remote command exit status unavailable: {status_error}") from status_error

        if type(exit_status) is not int:
            raise RuntimeError(f"Remote command returned invalid exit status: {exit_status!r}")
        if exit_status != 0:
            detail = f": {error}" if error else ""
            raise RuntimeError(f"Remote command exited with status {exit_status}{detail}")
        if error:
            logging.warning("Remote command on host %s wrote to stderr: %s", hostname, error)
        return output

    def _execute_on_all(self, command: str) -> dict[str, str]:
        """Execute while holding execution_lock; failed hosts are removed."""
        results: dict[str, str] = {}
        with self.lock:
            hostnames = list(self.clients.keys())
        for hostname in hostnames:
            with self.lock:
                if self._closed:
                    break
                client = self.clients.get(hostname)
            if client is None:
                continue
            try:
                # _execute reads the client map; execution_lock guarantees this
                # client remains owned until the call finishes.
                results[hostname] = self._execute(hostname, command)
            except Exception as error:
                logging.error("Error executing command on host %s: %s", hostname, error)
                self._remove_client(hostname)
        return results

    def execute_on_all_async(self, command_uuid: str) -> None:
        with self.lock:
            command = self.async_commands[command_uuid]
            if not self._closed and command and command.thread.ident is None:
                command.thread.start()

    def get_async_results(self, command_uuid: Optional[str]) -> dict[str, str]:
        if not command_uuid:
            return {}
        with self.lock:
            if command_uuid not in self.async_commands:
                return {}
            command = self.async_commands[command_uuid]
            if not command:
                return {}
            return {key: command.results[key] for key in natsorted(command.results.keys())}

    def _command_update_task(self, command_uuid: str) -> None:
        with self.lock:
            command = self.async_commands[command_uuid]
        if not command:
            return

        first_attempt = True
        while True:
            try:
                with self.execution_lock:
                    with self.lock:
                        if self._closed or not command.running:
                            return
                    results = self._execute_on_all(command.command)
                    with self.lock:
                        if not self._closed and command_uuid in self.async_commands:
                            command.results = results
            except KeyboardInterrupt:
                with self.lock:
                    command.running = False
            finally:
                if first_attempt:
                    with self.lock:
                        command.mark_initial_collection_complete()
                    first_attempt = False
            time.sleep(EXTERNAL_UPDATE_INTERVAL_S)

    def _are_hostnames_changed(self, new_hostnames: list[str]) -> bool:
        if len(new_hostnames) != len(self.clients):
            return True
        return not all(hostname in self.clients for hostname in new_hostnames)

    def update_hostnames(self, hostnames: list[str]) -> None:
        snapshot = list(hostnames)
        with self.lock:
            if self._closed or not self._are_hostnames_changed(snapshot) or self.is_update_processing:
                return

            self.is_update_processing = True
            worker = threading.Thread(
                target=self._update_hostnames_task,
                kwargs={"hostnames": snapshot},
                daemon=True,
            )
            self._update_worker = worker
            try:
                worker.start()
            except Exception:
                self.is_update_processing = False
                self._update_worker = None
                raise

    def _update_hostnames_task(self, hostnames: list[str]) -> None:
        try:
            with self.execution_lock:
                with self.lock:
                    is_open = not self._closed
                if is_open:
                    self._connect_all(hostnames)
        finally:
            with self.lock:
                self.is_update_processing = False

    def is_busy(self, command_uuid: Optional[str] = None) -> bool:
        with self.lock:
            if command_uuid is None:
                return any(command.is_initially_busy for command in self.async_commands.values())

            command = self.async_commands[command_uuid] if command_uuid in self.async_commands else None
            if command is None:
                return False
            return command.is_initially_busy

    def is_healthy(self) -> bool:
        with self.lock:
            clients = list(self.clients.values())
        # Paramiko transport health checks are local state reads. Keeping them
        # outside lock preserves fresh health visibility without waiting for
        # command execution or hostname reconciliation.
        return all(not self._is_ssh_client_closed(client) for client in clients)
