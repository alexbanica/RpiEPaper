import logging

import paramiko

class RemoteConnectionManager:
    def __init__(self, hostnames:[str], username: str = "alexbanica", ssh_key_path: str = "/home/alexbanica/.ssh/id_rsa"):
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.clients = {}
        self._connect_all(hostnames)
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

    def _connect_all(self, hostnames: [str]) -> None:
        for hostname in hostnames:
            self.clients.setdefault(hostname, self._connect(hostname))

    def __close__(self) -> None:
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
