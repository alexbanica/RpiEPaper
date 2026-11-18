import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


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
    replicas: Optional[int]
    running_replicas: int
    deployed_to: list[str]

    @property
    def display_name(self) -> str:
        return self.name.replace(f"{self.namespace}_", "") if self.namespace else self.name

    @property
    def image_short(self) -> str:
        return self.image.split("@")[0] if "@" in self.image else self.image

    @property
    def image_tag(self) -> str:
        image_name = self.image_short.rsplit("/", 1)[-1]
        return image_name.rsplit(":", 1)[-1] if ":" in image_name else "-"

    @property
    def image_release_version(self) -> str:
        match = re.match(r"^v?(\d+(?:\.\d+)+(?:-(?:alpha|beta|rc)\d+)?)(?:-|$)", self.image_tag)
        return match.group(1) if match else "-"

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
        return {
            "name": self.display_name,
            "id": self.id,
            "created": self.created_short,
            "updated": self.updated,
            "mode": self.mode,
            "image": self.image_release_version,
            "replicas": f"{self.running_replicas}/{self.replicas if self.replicas is not None else '-'}",
        }
