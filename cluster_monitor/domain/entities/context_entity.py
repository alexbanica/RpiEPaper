from dataclasses import dataclass


@dataclass
class ContextEntity:
    default_page: int
    render_type: str
    remote_ssh_username: str = ""
    remote_ssh_key_path: str = ""
    remote_ssh_rpi_status_command: str = ""
    remote_ssh_rpi_hdd_status_command: str = ""
    is_monitor_client: bool = False
    show_hdd_stats: bool = False
    renderer_init_interval_sec: int = 2 * 60
    display_update_interval_sec: int = 5
    docker_node_down_threshold_sec: int = 60
