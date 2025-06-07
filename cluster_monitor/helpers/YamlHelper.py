import logging

import yaml
import os

from cluster_monitor.dto import Context

class YamlHelper:
    def __init__(self, config_base_dir: str):
        self.config_dir = config_base_dir

    def parse_config(self, context: Context, config_file_names: list[str]) -> None:
        for config_file in config_file_names:
            config = None
            file_path = os.path.join(self.config_dir, config_file)
            if not os.path.exists(file_path):
                continue

            logging.info(f"Parsing config file: {file_path}")
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file)

            if config is None:
                continue

            self.__parse_remote_service_config(config, context)

    def __parse_remote_service_config(self, config: dict, context: Context) -> None:
        remote_config = config.get('cluster_monitor', {}).get('remote_service', {}).get('ssh', {})
        ssh_user = remote_config.get('user', "")
        ssh_key_path = remote_config.get('key_path', "")
        ssh_command = remote_config.get('command', "")

        if ssh_user:
            context.remote_ssh_username = ssh_user

        if ssh_key_path:
            context.remote_ssh_key_path = ssh_key_path

        if ssh_command:
            context.remote_ssh_command = ssh_command
