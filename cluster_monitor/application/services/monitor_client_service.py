from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.domain.services import RpiServiceInterface


class MonitorClientService:
    def __init__(self, rpi_service: RpiServiceInterface):
        self.rpi_service = rpi_service

    def render_rpi_stats(self) -> None:
        print(self.rpi_service.render_stats())

    def render_disk_stats(self) -> None:
        for disk_usage in self.rpi_service.get_disk_usages(["/"]):
            print(disk_usage.render())

    def render(self, context: ContextEntity) -> None:
        if context.show_hdd_stats:
            self.render_disk_stats()
            return

        self.render_rpi_stats()
