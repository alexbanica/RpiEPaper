import logging
from pathlib import Path

import yaml

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import ConfigParserInterface


class YamlConfigParser(ConfigParserInterface):
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir

    def parse(self, context: ContextEntity, config_file_names: list[str]) -> None:
        for config_file_name in config_file_names:
            file_path = self.config_dir / config_file_name
            if not file_path.exists():
                continue

            logging.info("Parsing config file: %s", file_path)
            with file_path.open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file)

            if not config:
                continue

            self._parse_remote_service_config(config, context)
            self._parse_renderer_config(config, context)
            self._parse_supervisor_config(config, context)

    def _parse_renderer_config(self, config: dict, context: ContextEntity) -> None:
        renderer_config = config.get("cluster_monitor", {}).get("renderer", {})
        context.renderer_init_interval_sec = renderer_config.get("init_interval_sec", 5 * 60)
        context.display_update_interval_sec = renderer_config.get("display_update_interval_sec", 5)

    def _parse_supervisor_config(self, config: dict, context: ContextEntity) -> None:
        supervisor_config = config.get("cluster_monitor", {}).get("supervisor", {})
        context.docker_node_down_threshold_sec = supervisor_config.get("docker_node_down_threshold_sec", 60)

    def _parse_remote_service_config(self, config: dict, context: ContextEntity) -> None:
        remote_config = config.get("cluster_monitor", {}).get("remote_service", {}).get("ssh", {})

        context.remote_ssh_username = remote_config.get("user", context.remote_ssh_username)
        context.remote_ssh_key_path = remote_config.get("key_path", context.remote_ssh_key_path)
        context.remote_ssh_rpi_status_command = remote_config.get(
            "command_rpi_status", context.remote_ssh_rpi_status_command
        )
        context.remote_ssh_rpi_hdd_status_command = remote_config.get(
            "command_rpi_hdd_status", context.remote_ssh_rpi_hdd_status_command
        )
