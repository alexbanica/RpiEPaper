from dataclasses import dataclass


@dataclass
class CommandLineArgumentsRequest:
    renderer: str
    page: int
    monitor_client: bool
    monitor_client_hdd_stats: bool
