#!/usr/bin/python
# -*- coding:utf-8 -*-

from dataclasses import dataclass

@dataclass
class Context:
    default_page: int
    render_type: str
    remote_ssh_username: str = ''
    remote_ssh_key_path: str = ''
    remote_ssh_rpi_status_command: str = ''
    remote_ssh_rpi_hdd_status_command: str = ''
    is_monitor_client: bool = False
    show_hdd_stats: bool = False
    renderer_init_interval_sec: int = 2 * 60
    display_update_interval_sec: int = 5
    docker_node_down_threshold_sec: int = 60

    def __str__(self):
        return (f"Context(default_page={self.default_page}, "
                f"render_type={self.render_type}, "
                f"remote_ssh_username={self.remote_ssh_username}, "
                f"remote_ssh_key_path={self.remote_ssh_key_path}, "
                f"remote_ssh_rpi_status_command={self.remote_ssh_rpi_status_command}, "
                f"remote_ssh_rpi_hdd_status_command={self.remote_ssh_rpi_hdd_status_command}, "
                f"is_monitor_client={self.is_monitor_client}, "
                f"show_hdd_stats={self.show_hdd_stats}, "
                f"renderer_init_interval_sec={self.renderer_init_interval_sec}, "
                f"display_update_interval_sec={self.display_update_interval_sec}, "
                f"docker_node_down_threshold_sec={self.docker_node_down_threshold_sec})")
