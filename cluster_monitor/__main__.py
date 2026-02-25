import sys

from cluster_monitor.application.services.monitor_client_service import MonitorClientService
from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.infrastructure.services.rpi_service import RpiService
from cluster_monitor.presentation.controllers.command_line_controller import CommandLineController
from cluster_monitor.shared.constants import RENDERER_TYPE_EPAPER


def main() -> int:
    context = ContextEntity(default_page=1, render_type=RENDERER_TYPE_EPAPER)
    request = CommandLineController().parse()
    context = CommandLineController().apply_to_context(request, context)

    if context.is_monitor_client:
        MonitorClientService(RpiService()).render(context)
        return 0

    from cluster_monitor.application.services.runtime_service import RuntimeService

    RuntimeService().run(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
