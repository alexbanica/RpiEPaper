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

    def test_to_dict_preserves_full_name_and_formats_replicas(self):
        subject = self._subject()

        result = subject.to_dict()

        self.assertEqual("service", result["name"])
        self.assertEqual("-", result["image"])
        self.assertEqual([80, 443, 9000], [port["published"] for port in subject.ports])
        self.assertNotIn("ports", result)
        self.assertNotIn("deployed_to", result)
        self.assertEqual("2/3", result["replicas"])

    def test_image_tag_uses_final_path_component_and_strips_digest(self):
        subject = self._subject(image="registry.local:5000/team/app:release-123@sha256:deadbeef")

        self.assertEqual("release-123", subject.image_tag)
        self.assertEqual("-", subject.image_release_version)

    def test_compact_image_release_examples(self):
        examples = {
            "1.0.3-7.1.3-8.5.12-fpm-alpine3.24": "1.0.3",
            "1.0.2-11.7": "1.0.2",
            "16.0.1-rootless": "16.0.1",
            "2.9": "2.9",
            "1.0.1-node24-alpine": "1.0.1",
            "2.45.3-alpine": "2.45.3",
            "2.0.0-beta5-node24-alpine": "2.0.0-beta5",
            "v1.2.3-rc1-alpine": "1.2.3-rc1",
            "v1.2.3-alpha12-build": "1.2.3-alpha12",
            "latest": "-",
            "app-1.2.3": "-",
            "1.2.3-beta5x-alpine": "1.2.3",
            "1.2.3-BETA5": "1.2.3",
        }
        for tag, expected in examples.items():
            with self.subTest(tag=tag):
                self.assertEqual(expected, self._subject(image=f"registry.local/app:{tag}").image_release_version)

    def test_release_uses_final_path_tag_and_keeps_raw_image_and_ports(self):
        raw = "registry.local:5000/team/app:v2.45.3-beta2-alpine@sha256:deadbeef"
        subject = self._subject(image=raw)

        self.assertEqual("2.45.3-beta2", subject.image_release_version)
        self.assertEqual(raw, subject.image)
        self.assertEqual("v2.45.3-beta2-alpine", subject.image_tag)
        self.assertEqual([80, 443, 9000], [p["published"] for p in subject.ports])

    def test_display_name_preserves_existing_namespace_removal(self):
        subject = self._subject()
        subject.name = "stack_stack_service"

        self.assertEqual("service", subject.display_name)
        self.assertEqual("service", subject.to_dict()["name"])

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
                self.assertEqual(["node1", "node2"], subject.deployed_to)
                self.assertNotIn("deployed_to", result)

    def test_replicated_explicit_zero_is_preserved(self):
        subject = self._subject(replicas=0, running_replicas=0)

        self.assertEqual("0/0", subject.to_dict()["replicas"])


if __name__ == "__main__":
    unittest.main()
