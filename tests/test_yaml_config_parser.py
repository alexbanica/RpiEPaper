import tempfile
import unittest
from pathlib import Path

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.infrastructure.parsers import YamlConfigParser


class YamlConfigParserTestCase(unittest.TestCase):
    def test_parse_updates_context_from_yaml(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.yml"
            config_path.write_text(
                """
cluster_monitor:
  supervisor:
    docker_node_down_threshold_sec: 10
  renderer:
    init_interval_sec: 120
    display_update_interval_sec: 7
  remote_service:
    ssh:
      user: test
      key_path: /tmp/key
      command_rpi_status: cmd-status
      command_rpi_hdd_status: cmd-hdd
""".strip(),
                encoding="utf-8",
            )

            context = ContextEntity(default_page=1, render_type="console")
            YamlConfigParser(Path(tmp_dir)).parse(context, ["config.yml"])

            self.assertEqual(10, context.docker_node_down_threshold_sec)
            self.assertEqual(120, context.renderer_init_interval_sec)
            self.assertEqual(7, context.display_update_interval_sec)
            self.assertEqual("test", context.remote_ssh_username)
            self.assertEqual("/tmp/key", context.remote_ssh_key_path)
            self.assertEqual("cmd-status", context.remote_ssh_rpi_status_command)
            self.assertEqual("cmd-hdd", context.remote_ssh_rpi_hdd_status_command)


if __name__ == "__main__":
    unittest.main()
