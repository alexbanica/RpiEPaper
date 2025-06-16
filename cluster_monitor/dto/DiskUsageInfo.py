#!/usr/bin/python
# -*- coding:utf-8 -*-

from dataclasses import dataclass

@dataclass
class DiskUsageInfo:
    path: str
    total_size: float
    used_size: float
    free_size: float
    used_percentage: float

    @property
    def total_size_human(self) -> str:
        return f"{self.total_size / (1024 ** 3):5.2f} GB"
    @property
    def used_size_human(self) -> str:
        return f"{self.used_size / (1024 ** 3):5.2f} GB"
    @property
    def free_size_human(self) -> str:
        return f"{self.free_size / (1024 ** 3):5.2f} GB"
    @property
    def used_percentage_human(self) -> str:
        return f"{self.used_percentage:3.1f}%"

    def render(self):
        return f"{self.path}: {self.used_size_human} / {self.total_size_human} - {self.used_percentage_human}"