from pathlib import Path

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.infrastructure.parsers.yaml_config_parser import YamlConfigParser


class YamlHelper:
    def __init__(self, config_base_dir: str):
        self.parser = YamlConfigParser(Path(config_base_dir))

    def parse_config(self, context: ContextEntity, config_file_names: list[str]) -> None:
        self.parser.parse(context, config_file_names)
