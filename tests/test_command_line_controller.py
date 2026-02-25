import unittest

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.presentation.controllers.requests import CommandLineArgumentsRequest
from cluster_monitor.presentation.controllers.command_line_controller import CommandLineController


class CommandLineControllerTestCase(unittest.TestCase):
    def test_apply_to_context_for_hdd_monitor_client(self):
        context = ContextEntity(default_page=1, render_type="epaper")
        request = CommandLineArgumentsRequest(
            renderer="console",
            page=3,
            monitor_client=False,
            monitor_client_hdd_stats=True,
        )

        updated_context = CommandLineController().apply_to_context(request, context)

        self.assertEqual("console", updated_context.render_type)
        self.assertEqual(3, updated_context.default_page)
        self.assertTrue(updated_context.is_monitor_client)
        self.assertTrue(updated_context.show_hdd_stats)


if __name__ == "__main__":
    unittest.main()
