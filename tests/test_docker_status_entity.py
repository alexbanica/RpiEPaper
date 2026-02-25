import unittest

from cluster_monitor.domain.entities import DockerStatusEntity


class DockerStatusEntityTestCase(unittest.TestCase):
    def test_to_dict_truncates_ports_and_formats_replicas(self):
        subject = DockerStatusEntity(
            name="stack_service",
            namespace="stack",
            id="svc-id",
            created="2026-01-01T10:00:00Z",
            updated="",
            mode={"Replicated": {"Replicas": 3}},
            image="registry.local/app:abc123456789",
            ports=[
                {"published": 80, "target": 80, "protocol": "tcp"},
                {"published": 443, "target": 443, "protocol": "tcp"},
                {"published": 9000, "target": 9000, "protocol": "tcp"},
            ],
            replicas=3,
            running_replicas=2,
            deployed_to=["node1", "node2"],
        )

        result = subject.to_dict()

        self.assertEqual("service", result["name"])
        self.assertEqual("abc1234567", result["image"])
        self.assertEqual("80,443...", result["ports"])
        self.assertEqual("2/3", result["replicas"])


if __name__ == "__main__":
    unittest.main()
