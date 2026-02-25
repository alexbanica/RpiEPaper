from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DockerStatusEntity:
    name: str
    namespace: str
    id: str
    created: str
    updated: str
    mode: dict[str, Any]
    image: str
    ports: list[dict[str, Any]]
    replicas: int
    running_replicas: int
    deployed_to: list[str]

    @property
    def name_short(self) -> str:
        return (self.name.replace(f"{self.namespace}_", "") if self.namespace else self.name)[:9]

    @property
    def image_short(self) -> str:
        return self.image.split("@")[0] if "@" in self.image else self.image

    @property
    def image_tag(self) -> str:
        return self.image_short.rsplit(":", 1)[-1] if ":" in self.image_short else "-"

    @property
    def image_tag_short(self) -> str:
        tag = self.image_tag
        return tag[:10] if len(tag) > 10 else tag

    @property
    def ports_short(self) -> list[str]:
        return [f"{port['published']}" for port in self.ports if port.get("published")]

    @property
    def created_short(self) -> str:
        if not self.created:
            return ""
        value = datetime.fromisoformat(self.created.replace("Z", "+00:00"))
        return value.strftime("%m/%d %H:%M")

    def to_dict(self) -> dict[str, Any]:
        ports = ",".join(self.ports_short)
        if len(self.ports_short) > 2:
            ports = ",".join(self.ports_short[:2]) + "..."

        return {
            "name": self.name_short,
            "id": self.id,
            "created": self.created_short,
            "updated": self.updated,
            "mode": self.mode,
            "image": self.image_tag_short,
            "ports": ports,
            "deployed_to": "global" if "Global" in self.mode else ",".join(self.deployed_to),
            "replicas": f"{self.running_replicas}/{self.replicas}",
        }
