import unittest

from cluster_monitor.domain.entities import DockerStatusEntity


class DockerStatusEntityTestCase(unittest.TestCase):
    def _subject(self, image="registry.local/app:abc123456789", mode=None, replicas=3, running_replicas=2):
        subject = DockerStatusEntity(
            name="stack_service",
            namespace="stack",
            id="svc-id",
            created="2026-01-01T10:00:00Z",
            updated="",
            mode=mode or {"Replicated": {"Replicas": replicas}},
            image=image,
            ports=[
                {"published": 80, "target": 80, "protocol": "tcp"},
                {"published": 443, "target": 443, "protocol": "tcp"},
                {"published": 9000, "target": 9000, "protocol": "tcp"},
            ],
            replicas=replicas,
            running_replicas=running_replicas,
            deployed_to=["node1", "node2"],
        )
        return subject

    def test_to_dict_truncates_ports_and_formats_replicas(self):
        subject = self._subject()

        result = subject.to_dict()

        self.assertEqual("service", result["name"])
        self.assertEqual("abc1234567", result["image"])
        self.assertEqual("80,443...", result["ports"])
        self.assertEqual("2/3", result["replicas"])

    def test_image_tag_uses_final_path_component_and_strips_digest(self):
        subject = self._subject(image="registry.local:5000/team/app:release-123@sha256:deadbeef")

        self.assertEqual("release-123", subject.image_tag)
        self.assertEqual("release-12", subject.image_tag_short)

    def test_registry_port_without_image_tag_is_not_a_tag(self):
        subject = self._subject(image="registry.local:5000/team/app")

        self.assertEqual("-", subject.image_tag)

    def test_untagged_digest_image_has_no_tag(self):
        subject = self._subject(image="registry.local:5000/team/app@sha256:deadbeef")

        self.assertEqual("-", subject.image_tag)

    def test_global_replicas_show_unavailable_target_including_zero(self):
        for running_replicas, expected in ((4, "4/-"), (0, "0/-")):
            with self.subTest(running_replicas=running_replicas):
                subject = self._subject(
                    mode={"Global": {}},
                    replicas=None,
                    running_replicas=running_replicas,
                )

                result = subject.to_dict()

                self.assertEqual(expected, result["replicas"])
                self.assertEqual("global", result["deployed_to"])

    def test_replicated_explicit_zero_is_preserved(self):
        subject = self._subject(replicas=0, running_replicas=0)

        self.assertEqual("0/0", subject.to_dict()["replicas"])


if __name__ == "__main__":
    unittest.main()
