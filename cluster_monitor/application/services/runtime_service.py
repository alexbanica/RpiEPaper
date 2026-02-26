import logging
from logging.handlers import TimedRotatingFileHandler

from cluster_monitor.application.services.cluster_monitor_service import ClusterMonitorService
from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.infrastructure.parsers.yaml_config_parser import YamlConfigParser
from cluster_monitor.infrastructure.services.docker_service import DockerService
from cluster_monitor.infrastructure.services.remote_service import RemoteService
from cluster_monitor.infrastructure.services.rpi_service import RpiService
from cluster_monitor.infrastructure.services.supervisor_service import SupervisorService
from cluster_monitor.shared.constants import CONFIG_FILE_PATHS, RESOURCES_DIR


class RuntimeService:
    @staticmethod
    def setup_logging() -> None:
        file_handler = TimedRotatingFileHandler(
            "/var/log/cluster_monitor.log",
            when="midnight",
            interval=1,
            backupCount=5,
        )
        console_handler = logging.StreamHandler()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s",
            handlers=[file_handler, console_handler],
        )

    def run(self, context: ContextEntity) -> None:
        self.setup_logging()
        YamlConfigParser(RESOURCES_DIR).parse(context, CONFIG_FILE_PATHS)

        rpi_service = RpiService()
        docker_service = DockerService()
        remote_service = RemoteService([], context.remote_ssh_username, context.remote_ssh_key_path)
        supervisor_service = SupervisorService(context, docker_service, rpi_service)

        ClusterMonitorService(
            context=context,
            rpi_service=rpi_service,
            docker_service=docker_service,
            remote_service=remote_service,
            supervisor_service=supervisor_service,
        ).start()
