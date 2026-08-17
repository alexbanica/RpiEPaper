import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class PublishForgejoTestCase(unittest.TestCase):
    """Deterministic contract tests for the release publisher.

    The publisher is deliberately driven with temporary artifacts and fake
    executables: no registry, credentials, or host package manager is used.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.artifacts = self.root / "dist"
        self.artifacts.mkdir()
        self.version = "1.2.3b4"
        self._write_artifacts()
        self.commands = []

    def tearDown(self):
        self.tmp.cleanup()

    def _write_artifacts(self):
        (self.artifacts / f"cluster_monitor-{self.version}.tar.gz").write_bytes(b"sdist")
        (self.artifacts / f"cluster_monitor-{self.version}-py3-none-linux_armv7l.whl").write_bytes(b"armv7")
        (self.artifacts / f"cluster_monitor-{self.version}-py3-none-linux_aarch64.whl").write_bytes(b"aarch64")

    def _fake_executable(self, name, body="#!/bin/sh\nexit 0\n"):
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def _run(self, command, env, **kwargs):
        self.commands.append((list(command), dict(env or {})))

        if "pip" in command and "install" in command:
            target_index = command.index("--target") + 1
            package = Path(command[target_index])
            version_token = next(
                arg for arg in command if arg.startswith("cluster-monitor==")
            )
            version = version_token.split("==", 1)[1]
            self._write_install_payload(package_root=package, version=version)
            return mock.Mock(returncode=0)

        if "-I" in command and "-c" in command:
            return mock.Mock(returncode=0)

        return mock.Mock(returncode=0)

    def _write_install_payload(self, package_root: Path, version: str):
        from scripts import publish_forgejo

        waveshare_root = package_root / "waveshare_epd"
        waveshare_root.mkdir(parents=True, exist_ok=True)

        for name in publish_forgejo.REQUIRED_LIBRARY_FILES:
            source_library = publish_forgejo.LIBRARY_SOURCE_DIR / name
            (waveshare_root / name).write_bytes(source_library.read_bytes())

        dist_info = package_root / f"cluster_monitor-{version}.dist-info"
        dist_info.mkdir(parents=True, exist_ok=True)
        (dist_info / "METADATA").write_text(
            f"Name: cluster-monitor\nVersion: {version}\n", encoding="utf-8"
        )

        runtime = package_root / publish_forgejo.PROJECT_NAME / "__init__.py"
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text(f"__version__ = '{version}'\n", encoding="utf-8")

    def _write_required_install_target(self, target_root: Path, version: str):
        from scripts import publish_forgejo

        for name in publish_forgejo.REQUIRED_LIBRARY_FILES:
            source_library = publish_forgejo.LIBRARY_SOURCE_DIR / name
            target_library = target_root / "waveshare_epd" / name
            target_library.parent.mkdir(parents=True, exist_ok=True)
            target_library.write_bytes(source_library.read_bytes())

        dist_info = target_root / f"cluster_monitor-{version}.dist-info"
        dist_info.mkdir(parents=True, exist_ok=True)
        (dist_info / "METADATA").write_bytes(
            f"Name: cluster-monitor\nVersion: {version}\n".encode("utf-8")
        )

        runtime = target_root / publish_forgejo.PROJECT_NAME / "__init__.py"
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_bytes(f"__version__ = '{version}'\n".encode("utf-8"))

    def test_only_validated_three_artifacts_are_uploaded_and_credentials_are_upload_only(self):
        from scripts import publish_forgejo

        # A stale/unrelated file must not be uploaded or silently accepted.
        (self.artifacts / "README.txt").write_text("stale", encoding="utf-8")
        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=self._run):
            result = publish_forgejo.publish(
                artifact_dir=self.artifacts,
                version=self.version,
                username="forgejo-user",
                token="secret-token",
                repository_url="https://forgejo.example/api/packages/public/pypi",
                simple_index_url="https://forgejo.example/api/packages/public/pypi/simple",
            )

        self.assertTrue(result)
        upload = [x for x in self.commands if "upload" in x[0]][-1]
        self.assertEqual("forgejo-user", upload[1]["TWINE_USERNAME"])
        self.assertEqual("secret-token", upload[1]["TWINE_PASSWORD"])
        for command, env in self.commands:
            if command != upload[0]:
                self.assertNotIn("TWINE_USERNAME", env)
                self.assertNotIn("TWINE_PASSWORD", env)
        uploaded = [arg for arg in upload[0] if str(arg).endswith((".tar.gz", ".whl"))]
        self.assertEqual(
            sorted(path.name for path in self.artifacts.iterdir() if path.suffix in {".whl", ".gz"}),
            sorted(Path(arg).name for arg in uploaded),
        )

    def test_artifact_set_conflict_and_immutable_upload_failure_clean_up(self):
        from scripts import publish_forgejo

        (self.artifacts / "cluster_monitor-9.9.9-py3-none-linux_armv7l.whl").write_bytes(b"wrong")
        with self.assertRaises(publish_forgejo.ArtifactValidationError):
            publish_forgejo.validate_artifacts(self.artifacts, self.version)

        (self.artifacts / "cluster_monitor-9.9.9-py3-none-linux_armv7l.whl").unlink()
        work = self.root / "publish-work"
        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=self._run) as run:
            run.side_effect = [mock.Mock(returncode=0), mock.Mock(returncode=1)]
            with self.assertRaises(publish_forgejo.PublishError):
                publish_forgejo.publish(
                    artifact_dir=self.artifacts, version=self.version,
                    username="u", token="t", repository_url="https://forgejo.example/pypi",
                    simple_index_url="https://forgejo.example/simple",
                    work_dir=work,
                )
        self.assertFalse(work.exists())

    def test_validate_artifacts_rejects_unexpected_cluster_monitor_distributions(self):
        from scripts import publish_forgejo

        (self.artifacts / "README.txt").write_text("ignored", encoding="utf-8")
        (self.artifacts / "cluster_monitor-1.2.3-py3-none-any.whl").write_bytes(b"unexpected")
        with self.assertRaises(publish_forgejo.ArtifactValidationError):
            publish_forgejo.validate_artifacts(self.artifacts, self.version)

    def test_target_platform_installs_are_exact_version_and_credential_free(self):
        from scripts import publish_forgejo

        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=self._run):
            publish_forgejo.verify_installations(
                version=self.version,
                simple_index_url="https://forgejo.example/api/packages/public/pypi/simple",
                targets=("linux_armv7l", "linux_aarch64"),
                install_root=self.root / "installs",
            )

        pip_commands = [x for x in self.commands if "pip" in Path(x[0][0]).name or "pip" in x[0]]
        self.assertEqual(2, len(pip_commands))
        for command, env in pip_commands:
            self.assertIn(f"cluster-monitor=={self.version}", command)
            self.assertIn("--no-deps", command)
            self.assertIn("--index-url", command)
            self.assertIn("--isolated", command)
            self.assertIn("--no-input", command)
            self.assertIn("--no-cache-dir", command)
            self.assertNotIn("TWINE_PASSWORD", env)
            self.assertNotIn("TWINE_USERNAME", env)
            self.assertNotIn("FORGEJO_PACKAGE_USERNAME", env)
            self.assertNotIn("FORGEJO_PACKAGE_TOKEN", env)
            self.assertEqual("1", env.get("PIP_NO_INPUT"))
            self.assertEqual("1", env.get("PIP_DISABLE_PIP_VERSION_CHECK"))
            self.assertEqual(os.devnull, env.get("PIP_CONFIG_FILE"))
            self.assertEqual("1", env.get("PIP_NO_CACHE_DIR"))

    def test_target_platform_installs_validate_cluster_monitor_imports_for_each_target(self):
        from scripts import publish_forgejo

        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=self._run):
            publish_forgejo.verify_installations(
                version=self.version,
                simple_index_url="https://forgejo.example/api/packages/public/pypi/simple",
                targets=("linux_armv7l", "linux_aarch64"),
                install_root=self.root / "installs",
            )

        import_commands = [x for x in self.commands if len(x[0]) > 1 and x[0][1] == "-I"]
        self.assertEqual(2, len(import_commands))
        for command, env in import_commands:
            self.assertEqual("-I", command[1])
            self.assertIn("-c", command)
            self.assertIn("sys.path.insert(0, str(target))", command[3])
            self.assertNotIn("FORGEJO_PACKAGE_USERNAME", env)
            self.assertNotIn("FORGEJO_PACKAGE_TOKEN", env)
            self.assertEqual("1", env.get("PIP_NO_INPUT"))
            self.assertEqual("1", env.get("PIP_DISABLE_PIP_VERSION_CHECK"))
            self.assertNotIn("PYTHONPATH", env)

    def test_validate_imported_cluster_monitor_uses_target_sys_path_in_real_subprocess(self):
        from scripts import publish_forgejo

        target = self.root / "installs" / "real"
        target.mkdir(parents=True, exist_ok=True)
        runtime = target / publish_forgejo.PROJECT_NAME / "__init__.py"
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text(f"__version__ = '{self.version}'\n", encoding="utf-8")

        shadow_root = self.root / "shadow-source"
        shadow_target = shadow_root / publish_forgejo.PROJECT_NAME
        shadow_target.mkdir(parents=True, exist_ok=True)
        (shadow_target / "__init__.py").write_text(
            "__version__ = '0.0.0'\n", encoding="utf-8"
        )

        cwd = Path.cwd()
        os.chdir(shadow_root)
        try:
            with mock.patch.dict(os.environ, {"PYTHONPATH": str(shadow_root)}):
                publish_forgejo._validate_imported_cluster_monitor(
                    version=self.version,
                    target_root=target,
                )
        finally:
            os.chdir(cwd)

    def test_target_platform_installs_fail_when_imported_cluster_monitor_version_check_fails(self):
        from scripts import publish_forgejo

        def run_with_import_version_mismatch(command, env, **kwargs):
            self.commands.append((list(command), dict(env or {})))

            if "pip" in command and "install" in command:
                target_index = command.index("--target") + 1
                package = Path(command[target_index])
                version_token = next(
                    arg for arg in command if arg.startswith("cluster-monitor==")
                )
                version = version_token.split("==", 1)[1]
                self._write_install_payload(package_root=package, version=version)
                return mock.Mock(returncode=0)

            if "-I" in command and "-c" in command:
                return mock.Mock(returncode=1)

            return mock.Mock(returncode=0)

        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=run_with_import_version_mismatch):
            with self.assertRaises(publish_forgejo.PublishError):
                publish_forgejo.verify_installations(
                    version=self.version,
                    simple_index_url="https://forgejo.example/api/packages/public/pypi/simple",
                    targets=("linux_armv7l", "linux_aarch64"),
                    install_root=self.root / "installs",
                )

    def test_publish_validation_rejects_validation_failures_without_leaving_work_dir(self):
        from scripts import publish_forgejo

        (self.artifacts / "cluster_monitor-1.2.3.tar.gz").write_bytes(b"wrong-version")
        work = self.root / "publish-work"
        with self.assertRaises(publish_forgejo.ArtifactValidationError):
            publish_forgejo.publish(
                artifact_dir=self.artifacts,
                version="1.2.3b4",
                username="u",
                token="t",
                repository_url="https://forgejo.example/pypi",
                simple_index_url="https://forgejo.example/simple",
                work_dir=work,
            )
        self.assertFalse(work.exists())

    def test_publish_rejects_preexisting_work_dir(self):
        from scripts import publish_forgejo

        work = self.root / "publish-work"
        work.mkdir()
        with self.assertRaises(publish_forgejo.PublishError):
            publish_forgejo.publish(
                artifact_dir=self.artifacts,
                version=self.version,
                username="u",
                token="t",
                repository_url="https://forgejo.example/pypi",
                simple_index_url="https://forgejo.example/simple",
                work_dir=work,
            )
        self.assertTrue(work.exists())

    def test_validate_installation_enforces_all_libraries_and_runtime_metadata(self):
        from scripts import publish_forgejo

        target = self.root / "target"
        self._write_required_install_target(target, self.version)
        publish_forgejo.validate_installation(
            target,
            [target / "waveshare_epd" / name for name in publish_forgejo.REQUIRED_LIBRARY_FILES],
            self.version,
            target / "cluster_monitor" / "__init__.py",
        )

        (target / "waveshare_epd" / "sysfs_gpio.so").write_bytes(b"")
        with self.assertRaises(publish_forgejo.PublishError):
            publish_forgejo.validate_installation(
                target,
                [target / "waveshare_epd" / name for name in publish_forgejo.REQUIRED_LIBRARY_FILES],
                self.version,
                target / "cluster_monitor" / "__init__.py",
            )

    def test_validate_installation_rejects_missing_nonstandard_and_conflicting_dist_info(self):
        from scripts import publish_forgejo

        target = self.root / "target"
        self._write_required_install_target(target, self.version)
        (target / "cluster_monitor-1.2.3b4.dist-info" / "METADATA").unlink()
        (target / "cluster_monitor-1.2.3b4.dist-info").rmdir()
        with self.assertRaises(publish_forgejo.PublishError):
            publish_forgejo.validate_installation(
                target,
                [target / "waveshare_epd" / name for name in publish_forgejo.REQUIRED_LIBRARY_FILES],
                self.version,
                target / "cluster_monitor" / "__init__.py",
            )

        self._write_required_install_target(target, self.version)
        dist_dir = target / "cluster-monitor-1.2.3b4.dist-info"
        dist_dir.mkdir(parents=True)
        (dist_dir / "METADATA").write_text(
            "Name: cluster-monitor\nVersion: 1.2.3b4\n", encoding="utf-8"
        )
        with self.assertRaises(publish_forgejo.PublishError):
            publish_forgejo.validate_installation(
                target,
                [target / "waveshare_epd" / name for name in publish_forgejo.REQUIRED_LIBRARY_FILES],
                self.version,
                target / "cluster_monitor" / "__init__.py",
            )

        extra = target / "cluster_monitor-9.9.9.dist-info"
        self._write_required_install_target(target, self.version)
        extra.mkdir(parents=True)
        (extra / "METADATA").write_text("Name: cluster-monitor\nVersion: 9.9.9\n", encoding="utf-8")
        with self.assertRaises(publish_forgejo.PublishError):
            publish_forgejo.validate_installation(
                target,
                [target / "waveshare_epd" / name for name in publish_forgejo.REQUIRED_LIBRARY_FILES],
                self.version,
                target / "cluster_monitor" / "__init__.py",
            )

    def test_success_removes_temporary_installation_state(self):
        from scripts import publish_forgejo

        work = self.root / "publish-work"
        with mock.patch.object(publish_forgejo.subprocess, "run", side_effect=self._run):
            publish_forgejo.publish(
                artifact_dir=self.artifacts, version=self.version, username="u", token="t",
                repository_url="https://forgejo.example/pypi", simple_index_url="https://forgejo.example/simple",
                work_dir=work,
            )
        self.assertFalse(work.exists())


if __name__ == "__main__":
    unittest.main()
