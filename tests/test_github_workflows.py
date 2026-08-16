"""Deterministic contract checks for the GitHub Actions workflows."""

import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class GitHubWorkflowTests(unittest.TestCase):
    def _workflow(self, name):
        path = WORKFLOWS / name
        self.assertTrue(path.is_file(), f"missing workflow: {path}")
        return path.read_text(encoding="utf-8")

    def _upload_step(self, workflow: str) -> re.Match[str]:
        upload = re.search(
            r"(?is)- name:\s*upload release artifacts\n.*?(?=\n\s*- name:|\Z)",
            workflow,
        )
        self.assertIsNotNone(upload)
        return upload

    def test_ci_targets_pull_requests_and_pushes_to_main(self):
        workflow = self._workflow("ci.yml")

        self.assertRegex(workflow, r"(?m)^\s*pull_request:\s*$")
        self.assertRegex(workflow, r"(?m)^\s*push:\s*$")
        self.assertRegex(
            workflow,
            r"(?ms)^\s*pull_request:\s*\n(?:\s+.*\n)*?\s+branches:\s*\n\s+-\s+main\s*$",
        )
        self.assertRegex(
            workflow,
            r"(?ms)^\s*push:\s*\n(?:\s+.*\n)*?\s+branches:\s*\n\s+-\s+main\s*$",
        )

    def test_ci_has_stable_check_names_for_supported_pythons(self):
        workflow = self._workflow("ci.yml")

        self.assertRegex(workflow, r"(?mi)^\s*(name:\s*)?(lint|ruff)\b")
        self.assertIn("name: test (${{ matrix.python-version }})", workflow)
        self.assertRegex(workflow, r'(?ms)python-version:\s*\["3\.9",\s*"3\.12"\]')
        self.assertRegex(workflow, r"['\"]?3\.9['\"]?")
        self.assertRegex(workflow, r"['\"]?3\.12['\"]?")
        self.assertRegex(workflow, r"ruff\s+(check|format)\b")
        self.assertRegex(workflow, r"requirements/dev\.txt")
        self.assertRegex(workflow, r"python\s+-m\s+unittest\s+discover\s+-s\s+tests")

    def test_publish_test_job_has_stable_matrix_check_names(self):
        workflow = self._workflow("publish.yml")
        self.assertIn("name: test (${{ matrix.python-version }})", workflow)
        self.assertRegex(workflow, r'(?ms)python-version:\s*\["3\.9",\s*"3\.12"\]')

    def test_publish_has_coarse_numeric_tag_filter_and_least_permissions(self):
        workflow = self._workflow("publish.yml")

        self.assertIn("[0-9]*.[0-9]*.[0-9]*", workflow)
        permissions = re.search(r"(?ms)^permissions:\s*\n(.*?)(?=^\S|\Z)", workflow)
        self.assertIsNotNone(permissions)
        self.assertRegex(permissions.group(1), r"contents:\s*read")
        self.assertNotRegex(permissions.group(1), r"packages:\s*write|contents:\s*write")

    def test_publish_serializes_each_ref_without_cancellation(self):
        workflow = self._workflow("publish.yml")

        self.assertRegex(workflow, r"(?mi)^\s*concurrency:\s*$")
        self.assertRegex(workflow, r"(?i)group:.*(ref|ref_name)")
        self.assertRegex(workflow, r"(?mi)^\s*cancel-in-progress:\s*false\s*$")

    def test_publish_uses_public_endpoints(self):
        workflow = self._workflow("publish.yml")

        self.assertIn("https://forgejo.alexlab.nl/api/packages/public/pypi", workflow)
        self.assertIn("https://forgejo.alexlab.nl/api/packages/public/pypi/simple", workflow)

    def test_publish_gates_release_and_requests_exact_three_artifacts(self):
        workflow = self._workflow("publish.yml")

        self.assertRegex(workflow, r"(?i)needs:\s*\[[^\]]*lint[^\]]*test[^\]]*\]")
        self.assertIn("scripts.package_artifacts", workflow)
        self.assertIn("scripts.publish_forgejo", workflow)
        for artifact in (".tar.gz", "linux_armv7l.whl", "linux_aarch64.whl"):
            self.assertIn(artifact, workflow)
        self.assertNotIn("py3-none-any.whl", workflow)

    def test_publish_invokes_release_tag_validation_inside_package_artifacts(self):
        workflow = self._workflow("publish.yml")
        expected = 'python -m scripts.package_artifacts --release-tag "$GITHUB_REF_NAME"'
        self.assertIn(expected, workflow)
        self.assertNotIn("python -m scripts.release_version \"$GITHUB_REF_NAME\"", workflow)

    def test_publish_upload_uses_simple_index_and_no_cli_credentials(self):
        workflow = self._workflow("publish.yml")
        upload = self._upload_step(workflow)
        upload_text = upload.group(0)

        self.assertIn("--simple-index-url", upload_text)
        self.assertNotIn("--index-url", upload_text)
        self.assertNotIn("--repository-url", upload_text)
        self.assertNotIn("--username", upload_text)
        self.assertNotIn("--password", upload_text)

    def test_publish_credentials_are_upload_step_only_and_environment_scoped(self):
        workflow = self._workflow("publish.yml")
        upload = self._upload_step(workflow)
        upload_text = upload.group(0)
        before_upload = workflow[: upload.start()]

        self.assertIn("FORGEJO_PACKAGE_USERNAME", upload_text)
        self.assertIn("FORGEJO_PACKAGE_TOKEN", upload_text)
        self.assertNotIn("FORGEJO_PACKAGE_USERNAME", before_upload)
        self.assertNotIn("FORGEJO_PACKAGE_TOKEN", before_upload)
        self.assertNotIn("vars.FORGEJO_PACKAGE_USERNAME", before_upload)
        self.assertNotIn("secrets.FORGEJO_PACKAGE_TOKEN", before_upload)

    def test_publish_prevents_unsupported_password_cli_flag(self):
        workflow = self._workflow("publish.yml")
        self.assertNotIn("--password", workflow)
        self.assertNotIn("--index-url", workflow)

    def test_ruff_toml_has_standalone_top_level_syntax(self):
        path = ROOT / "ruff.toml"
        self.assertTrue(path.is_file(), f"missing ruff config: {path}")
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("tool", data)
        self.assertEqual(data["target-version"], "py39")
        self.assertEqual(data["line-length"], 100)
        self.assertIn("cluster_monitor", data["src"])


if __name__ == "__main__":
    unittest.main()
