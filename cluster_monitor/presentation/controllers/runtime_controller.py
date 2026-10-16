import logging
from logging.handlers import TimedRotatingFileHandler

from cluster_monitor.application.services.cluster_monitor_service import ClusterMonitorService
from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.infrastructure.parsers.yaml_config_parser import YamlConfigParser
from cluster_monitor.infrastructure.services.docker_service import DockerService
from cluster_monitor.infrastructure.services.remote_service import RemoteService
from cluster_monitor.infrastructure.services.rpi_service import RpiService
from cluster_monitor.infrastructure.services.supervisor_service import SupervisorService
from cluster_monitor.presentation.renderers.renderer_manager import RendererManager
from cluster_monitor.shared.constants import CONFIG_FILE_PATHS, RENDERER_TYPE_EPAPER, RESOURCES_DIR


class RuntimeController:
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
        YamlConfigParser.parse_runtime_config(context, RESOURCES_DIR, CONFIG_FILE_PATHS)

        if context.render_type == RENDERER_TYPE_EPAPER and not context.is_monitor_client:
            from cluster_monitor.infrastructure.services.raspberry_pi_gpio_service import (
                RaspberryPiGpioService,
            )

            RaspberryPiGpioService().initialize_for_epaper()

        # Until ClusterMonitorService is created, this controller owns the
        # resources and must release any that were constructed if composition
        # fails. Once constructed, the application service owns normal cleanup.
        rpi_service = None
        docker_service = None
        remote_service = None
        supervisor_service = None
        renderer_manager = None
        monitor_service = None
        try:
            rpi_service = RpiService()
            docker_service = DockerService()
            remote_service = RemoteService([], context.remote_ssh_username, context.remote_ssh_key_path)
            supervisor_service = SupervisorService(context, docker_service, rpi_service)
            renderer_manager = RendererManager(context)
            monitor_service = ClusterMonitorService(
                context=context,
                rpi_service=rpi_service,
                docker_service=docker_service,
                remote_service=remote_service,
                supervisor_service=supervisor_service,
                renderer_manager=renderer_manager,
            )
        except BaseException:
            self._close_composition_resources(
                rpi_service,
                renderer_manager,
                supervisor_service,
                docker_service,
                remote_service,
            )
            raise

        try:
            monitor_service.start()
        except BaseException:
            # start() normally performs its own G3 teardown. This also covers
            # failures before its protected frame/run section begins; close()
            # is idempotent for an already completed teardown.
            try:
                monitor_service.close()
            except BaseException:
                logging.exception("Failed to clean up after runtime startup failure")
            raise

    @staticmethod
    def _close_composition_resources(
        rpi_service,
        renderer_manager,
        supervisor_service,
        docker_service,
        remote_service,
    ) -> None:
        for label, action in (
            (
                "cluster hat alert reset",
                lambda: rpi_service.set_cluster_hat_alert(False) if rpi_service is not None else None,
            ),
            ("renderer", renderer_manager.close if renderer_manager is not None else None),
            ("supervisor", supervisor_service.close if supervisor_service is not None else None),
            ("Docker collection", docker_service.close if docker_service is not None else None),
            ("remote collection", remote_service.close if remote_service is not None else None),
        ):
            if action is None:
                continue
            try:
                action()
            except BaseException:
                logging.exception("Failed to close %s after runtime composition failure", label)
