from dataclasses import dataclass
import threading


@dataclass
class AsyncCommandCacheEntity:
    uuid: str
    command: str
    running: bool
    results: dict[str, str]
    thread: threading.Thread
