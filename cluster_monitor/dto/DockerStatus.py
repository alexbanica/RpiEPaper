#!/usr/bin/python
# -*- coding:utf-8 -*-

from _datetime import datetime
from dataclasses import dataclass
from typing import Any


@dataclass
class DockerStatus:
    name: str
    namespace: str
    id: str
    created: str
    updated: str
    mode: dict
    image: str
    ports: list
    replicas: int
    running_replicas: int
    deployed_to: list

    @property
    def name_short(self) -> str:
        return self.name.replace(f"{self.namespace}_", "") if self.namespace else self.name

    @property
    def image_short(self) -> str:
        return self.image.split('@')[0] if '@' in self.image else self.image

    @property
    def image_tag(self) -> str:
        return self.image_short.rsplit(':', 1)[-1] if ':' in self.image_short else '-'

    @property
    def image_tag_short(self) -> str:
        tag = self.image_tag
        return tag[:10] if len(tag) > 10 else tag

    @property
    def ports_short(self) -> list[str]:
        return [f"{port['published']}" for port in self.ports]

    @property
    def created_short(self) -> str:
        if not self.created:
            return ''
        dt = datetime.fromisoformat(self.created.replace('Z', '+00:00'))
        return dt.strftime('%m/%d %H:%M')

    def to_list(self) -> list:
        return [self.name, self.id, self.created, self.updated, self.mode, self.image, self.ports, self.replicas]

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name_short,
            'id': self.id,
            'created': self.created_short,
            'updated': self.updated,
            'mode': self.mode,
            'image': self.image_tag_short,
            'ports': self.ports_short,
            'deployed_to': self.deployed_to,
            'replicas': f"{self.running_replicas}/{self.replicas}"
        }
