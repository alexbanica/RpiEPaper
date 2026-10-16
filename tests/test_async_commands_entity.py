import threading
import unittest

from cluster_monitor.domain.entities.async_command_cache_entity import AsyncCommandCacheEntity
from cluster_monitor.domain.entities.async_commands_entity import AsyncCommandsEntity


def command() -> AsyncCommandCacheEntity:
    thread = threading.Thread(target=lambda: None)
    thread.start()
    thread.join()
    return AsyncCommandCacheEntity("id", "command", True, {}, thread)


class AsyncCommandsEntityTestCase(unittest.TestCase):
    def test_new_command_is_initially_busy_until_first_collection_completes(self) -> None:
        cache = command()

        self.assertTrue(cache.is_initially_busy)
        cache.mark_initial_collection_complete()
        self.assertFalse(cache.is_initially_busy)

    def test_completion_is_independent_of_empty_or_failed_result_maps(self) -> None:
        cache = command()

        cache.mark_initial_collection_complete()
        self.assertEqual({}, cache.results)
        self.assertFalse(cache.is_initially_busy)

        cache.results = {"host": ""}
        self.assertFalse(cache.is_initially_busy)

    def test_later_cycles_do_not_restore_initial_busy_state(self) -> None:
        cache = command()
        cache.mark_initial_collection_complete()

        cache.running = True
        cache.results = {}

        self.assertFalse(cache.is_initially_busy)

    def test_close_completes_initial_state_and_clears_running_and_results(self) -> None:
        cache = command()
        commands = AsyncCommandsEntity()
        commands[cache.uuid] = cache

        commands.close()

        self.assertFalse(cache.running)
        self.assertEqual({}, cache.results)
        self.assertTrue(cache.initial_collection_complete)
        self.assertFalse(cache.is_initially_busy)
