from cluster_monitor.application.services.monitor_client_service import MonitorClientService
from cluster_monitor.infrastructure.services.rpi_service import RpiService


class MonitorClient(MonitorClientService):
    def __init__(self):
        super().__init__(RpiService())
