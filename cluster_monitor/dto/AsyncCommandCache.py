#!/usr/bin/python
# -*- coding:utf-8 -*-

import threading
from dataclasses import dataclass

@dataclass
class AsyncCommandCache:
    uuid: str
    command: str
    running: bool
    results: dict[str, str]
    thread: threading.Thread