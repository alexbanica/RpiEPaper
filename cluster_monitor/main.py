from cluster_monitor.application.services.runtime_service import RuntimeService
from cluster_monitor.domain.entities import ContextEntity


def main(context: ContextEntity) -> None:
    RuntimeService().run(context)
