"""Deterministic checks for the three release distributions."""

import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = {
    "waveshare_epd/DEV_Config_32.so": (1, 40),
    "waveshare_epd/DEV_Config_64.so": (2, 183),
    "waveshare_epd/sysfs_gpio.so": (2, 183),
    "waveshare_epd/sysfs_software_spi.so": (2, 183),
}
PACKAGE_FILES = {
    "cluster_monitor/__init__.py",
    "cluster_monitor/__main__.py",
    "waveshare_epd/__init__.py",
}
REQUIRED_PACKAGE_PREFIXES = ("cluster_monitor/", "waveshare_epd/")


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _normalize_member_path(path: str) -> str:
    marker = ".data/purelib/"
    if marker in path:
        return path.split(marker, 1)[1]
    if path.startswith("lib/"):
        return path[len("lib/") :]
    return path


def _source_hashes():
    return {
        name: hashlib.sha256((ROOT / "lib" / name).read_bytes()).hexdigest()
        for name in LIBRARIES
    }


def _run_builder(output_dir, *extra):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.package_artifacts",
            "--output-dir",
            str(output_dir),
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _run_local_install_no_deps(target: Path) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temporary:
        source_root = Path(temporary) / "source"
        shutil.copytree(
            ROOT,
            source_root,
            ignore=shutil.ignore_patterns(
                ".git",
                "build",
                "dist",
                "*.egg-info",
                ".mypy_cache",
                ".ruff_cache",
                ".pytest_cache",
                "__pycache__",
                ".cache",
            ),
        )
        environment = os.environ.copy()
        environment["PIP_NO_CACHE_DIR"] = "off"
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                ".",
                "--no-deps",
                "--no-build-isolation",
                "--no-cache-dir",
                "--target",
                str(target),
            ],
            cwd=source_root,
            capture_output=True,
            text=True,
            env=environment,
        )


def _members(artifact):
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            return {
                name: archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }
    with tarfile.open(artifact, "r:gz") as archive:
        return {
            member.name.split("/", 1)[1]: archive.extractfile(member).read()
            for member in archive.getmembers()
            if member.isfile() and "/" in member.name
        }


def _normalized_members(artifact):
    return {_normalize_member_path(name): payload for name, payload in _members(artifact).items()}


def _metadata_field(payload: bytes, field: str) -> str:
    for line in payload.decode("utf-8").splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing metadata field: {field}")


def _replace_in_metadata(
    artifact: Path,
    payload_map: dict[str, str],
) -> Path:
    target = Path(tempfile.mkdtemp(dir=artifact.parent)) / artifact.name
    with zipfile.ZipFile(artifact) as source, zipfile.ZipFile(target, "w") as destination:
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename.endswith("dist-info/METADATA"):
                metadata = payload.decode("utf-8")
                for old, new in payload_map.items():
                    metadata = metadata.replace(old, new)
                payload = metadata.encode("utf-8")
            destination.writestr(info, payload)
    return target


def _replace_wheel_tag(artifact: Path, old: str, new: str) -> Path:
    target = Path(tempfile.mkdtemp(dir=artifact.parent)) / artifact.name
    with zipfile.ZipFile(artifact) as source, zipfile.ZipFile(target, "w") as destination:
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename.endswith("dist-info/WHEEL"):
                payload = payload.replace(old.encode("utf-8"), new.encode("utf-8"))
            destination.writestr(info, payload)
    return target


def _replace_record_hash(artifact: Path, member: str) -> Path:
    target = Path(tempfile.mkdtemp(dir=artifact.parent)) / artifact.name
    with zipfile.ZipFile(artifact) as source, zipfile.ZipFile(target, "w") as destination:
        record_name = next(name for name in source.namelist() if name.endswith("dist-info/RECORD"))
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename == record_name:
                rows = list(csv.reader(payload.decode("utf-8").splitlines()))
                replaced = False
                updated = []
                for row in rows:
                    if len(row) == 3 and _normalize_member_path(row[0]) == member:
                        row[1] = "sha256=AAAA"
                        replaced = True
                    updated.append(row)
                if not replaced:
                    raise AssertionError(f"record row not found: {member}")
                payload = ("\n".join(",".join(row) for row in updated) + "\n").encode("utf-8")
            destination.writestr(info, payload)
    return target


class PackageArtifactsTests(unittest.TestCase):
    def test_builds_exact_sdist_and_two_non_pure_platform_wheels(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            artifacts = sorted(Path(temporary).iterdir())
            self.assertEqual(3, len(artifacts))
            self.assertEqual(1, len([p for p in artifacts if p.name.endswith(".tar.gz")]))
            self.assertEqual(
                [
                    "cluster_monitor-1.0.0-py3-none-linux_aarch64.whl",
                    "cluster_monitor-1.0.0-py3-none-linux_armv7l.whl",
                ],
                sorted(p.name for p in artifacts if p.suffix == ".whl"),
            )
            self.assertFalse(any("py3-none-any" in p.name for p in artifacts))

            for wheel in (p for p in artifacts if p.suffix == ".whl"):
                with zipfile.ZipFile(wheel) as archive:
                    wheel_metadata = next(
                        archive.read(name).decode("utf-8")
                        for name in archive.namelist()
                        if name.endswith(".dist-info/WHEEL")
                    )
                self.assertIn("Root-Is-Purelib: false", wheel_metadata)
                self.assertIn("Tag: py3-none-linux_", wheel_metadata)

    def test_every_artifact_contains_required_packages_and_byte_identical_native_files(
        self,
    ):
        expected_hashes = _source_hashes()
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            for artifact in Path(temporary).iterdir():
                members = _normalized_members(artifact)
                self.assertTrue(PACKAGE_FILES <= members.keys(), artifact.name)
                for prefix in REQUIRED_PACKAGE_PREFIXES:
                    self.assertTrue(
                        any(name.startswith(prefix) for name in members), artifact.name
                    )
                for name, expected_hash in expected_hashes.items():
                    self.assertIn(name, members, artifact.name)
                    self.assertEqual(
                        expected_hash, hashlib.sha256(members[name]).hexdigest()
                    )

    def test_local_no_deps_install_includes_cluster_monitor_and_waveshare_files(self):
        install_root = Path(tempfile.mkdtemp())
        try:
            result = _run_local_install_no_deps(install_root)
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)

            for name in set(PACKAGE_FILES) | set(LIBRARIES):
                self.assertTrue((install_root / name).exists(), name)

            metadata = next(install_root.glob("*.dist-info/METADATA"))
            self.assertEqual(
                "cluster-monitor",
                _normalize_distribution_name(_metadata_field(metadata.read_bytes(), "Name")),
            )
            self.assertEqual(
                "1.0.0",
                _metadata_field(metadata.read_bytes(), "Version"),
            )
        finally:
            shutil.rmtree(install_root, ignore_errors=True)

    def test_native_files_have_required_elf_class_and_machine(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            for artifact in Path(temporary).iterdir():
                for name, (elf_class, machine) in LIBRARIES.items():
                    payload = _normalized_members(artifact)[name]
                    self.assertEqual(b"\x7fELF", payload[:4], name)
                    self.assertEqual(elf_class, payload[4], name)
                    self.assertEqual(machine, int.from_bytes(payload[18:20], "little"), name)

    def test_rejects_archive_with_changed_native_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            wheel = next(Path(temporary).glob("*.whl"))
            changed = Path(tempfile.mkdtemp(dir=temporary)) / wheel.name
            with zipfile.ZipFile(wheel) as source, zipfile.ZipFile(
                changed, "w"
            ) as target:
                for info in source.infolist():
                    payload = source.read(info.filename)
                    if info.filename.endswith("DEV_Config_32.so"):
                        payload = payload[:-1] + bytes([payload[-1] ^ 1])
                    target.writestr(info, payload)
            verify = subprocess.run(
                [sys.executable, "-m", "scripts.package_artifacts", "--verify", str(changed)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, verify.returncode)
            self.assertIn("DEV_Config_32.so", verify.stderr + verify.stdout)

    def test_rejects_wrong_wheel_tag_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            wheel = next(
                artifact
                for artifact in Path(temporary).iterdir()
                if artifact.suffix == ".whl" and "linux_armv7l" in artifact.name
            )
            changed = _replace_wheel_tag(
                wheel,
                "Tag: py3-none-linux_armv7l",
                "Tag: py3-none-any",
            )
            verify = subprocess.run(
                [sys.executable, "-m", "scripts.package_artifacts", "--verify", str(changed)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, verify.returncode)
            self.assertIn("WHEEL tag mismatch", verify.stderr + verify.stdout)

    def test_rejects_wrong_metadata_name_or_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            wheel = next(artifact for artifact in Path(temporary).iterdir() if artifact.suffix == ".whl")
            with zipfile.ZipFile(wheel) as archive:
                metadata_payload = next(
                    archive.read(name)
                    for name in archive.namelist()
                    if name.endswith("dist-info/METADATA")
                )
            original_name = _metadata_field(metadata_payload, "Name")

            name_changed = _replace_in_metadata(
                wheel,
                {f"Name: {original_name}": "Name: wrong-name"},
            )
            with zipfile.ZipFile(name_changed) as archive:
                changed_name = _metadata_field(
                    next(
                        payload
                        for name, payload in (
                            (name, archive.read(name))
                            for name in archive.namelist()
                        )
                        if name.endswith("dist-info/METADATA")
                    ),
                    "Name",
                )
            self.assertEqual("wrong-name", _normalize_distribution_name(changed_name))
            verify = subprocess.run(
                [sys.executable, "-m", "scripts.package_artifacts", "--verify", str(name_changed)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, verify.returncode)
            self.assertIn("metadata name mismatch", verify.stderr + verify.stdout)

            version_changed = _replace_in_metadata(
                wheel,
                {"Version: 1.0.0": "Version: 0.0.0"},
            )
            verify = subprocess.run(
                [sys.executable, "-m", "scripts.package_artifacts", "--verify", str(version_changed)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, verify.returncode)
            self.assertIn("metadata version mismatch", verify.stderr + verify.stdout)

    def test_rejects_records_with_invalid_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = _run_builder(temporary)
            self.assertEqual(0, result.returncode, result.stderr)
            wheel = next(artifact for artifact in Path(temporary).iterdir() if artifact.suffix == ".whl")
            changed = _replace_record_hash(wheel, "waveshare_epd/DEV_Config_32.so")
            verify = subprocess.run(
                [sys.executable, "-m", "scripts.package_artifacts", "--verify", str(changed)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, verify.returncode)
            self.assertIn("RECORD hash mismatch", verify.stderr + verify.stdout)


if __name__ == "__main__":
    unittest.main()
