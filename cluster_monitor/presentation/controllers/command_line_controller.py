import argparse

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.presentation.controllers.requests.command_line_arguments_request import CommandLineArgumentsRequest
from cluster_monitor.shared.constants import ARG_PAGE_CHOICES, ARG_RENDERER_CHOICES, RENDERER_TYPE_EPAPER


class CommandLineController:
    def parse(self) -> CommandLineArgumentsRequest:
        parser = argparse.ArgumentParser(description="Server Status Display")
        parser.add_argument("-r", "--renderer", choices=ARG_RENDERER_CHOICES, default=RENDERER_TYPE_EPAPER)
        parser.add_argument("-p", "--page", choices=ARG_PAGE_CHOICES, default="1")
        parser.add_argument("-mc", "--monitor-client", action="store_true", default=False)
        parser.add_argument("-mc-hdd", "--monitor-client-hdd-stats", action="store_true", default=False)

        args = parser.parse_args()
        return CommandLineArgumentsRequest(
            renderer=args.renderer,
            page=int(args.page),
            monitor_client=args.monitor_client,
            monitor_client_hdd_stats=args.monitor_client_hdd_stats,
        )

    def apply_to_context(self, request: CommandLineArgumentsRequest, context: ContextEntity) -> ContextEntity:
        context.default_page = request.page
        context.render_type = request.renderer
        context.is_monitor_client = request.monitor_client
        if request.monitor_client_hdd_stats:
            context.is_monitor_client = True
            context.show_hdd_stats = True
        return context
