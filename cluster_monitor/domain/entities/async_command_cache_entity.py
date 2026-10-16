from dataclasses import dataclass
import threading


@dataclass
class AsyncCommandCacheEntity:
    uuid: str
    command: str
    running: bool
    results: dict[str, str]
    thread: threading.Thread
    initial_collection_complete: bool = False

    @property
    def is_initially_busy(self) -> bool:
        """Whether the first collection is still pending while the worker runs."""
        return self.running and not self.initial_collection_complete

    def mark_initial_collection_complete(self) -> None:
        """Record the first collection attempt, independent of its results."""
        self.initial_collection_complete = True
