from dataclasses import dataclass


@dataclass
class ClusterHatStatusEntity:
    is_on: bool
    has_alert: bool
    active_node_count: int
