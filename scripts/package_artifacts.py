"""Build and verify deterministic package artifacts."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator
import tarfile
import zipfile

from scripts.release_version import (
    parse_release_tag,
    prepare_release_tree,
    read_runtime_version,
    validate_canonical_version,
)

REQUIRED_LIBS = {
    "waveshare_epd/DEV_Config_32.so": (1, 40),
    "waveshare_epd/DEV_Config_64.so": (2, 183),
    "waveshare_epd/sysfs_gpio.so": (2, 183),
    "waveshare_epd/sysfs_software_spi.so": (2, 183),
}
REQUIRED_RESOURCE_FILES = {
    "cluster_monitor/resources/Font.ttc",
    "cluster_monitor/resources/config.yml",
}
REQUIRED_PACKAGE_FILES = {
    "cluster_monitor/__init__.py",
    "cluster_monitor/__main__.py",
    "waveshare_epd/__init__.py",
} | REQUIRED_RESOURCE_FILES
WHEEL_PLATFORMS = ("linux_armv7l", "linux_aarch64")


def _normalize_package_path(path: str) -> str:
    marker = ".data/purelib/"
    if marker in path:
        return path.split(marker, 1)[1]
    if path.startswith("lib/"):
        return path[len("lib/") :]
    return path


def _canonical_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _read_project_metadata(project_root: Path) -> tuple[str, str]:
    metadata = {}
    for line in (project_root / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata["name"], metadata["version"]


def _expected_artifact_names(project_name: str, version: str) -> tuple[str, ...]:
    return (
        f"{project_name}-{version}.tar.gz",
        f"{project_name}-{version}-py3-none-linux_armv7l.whl",
        f"{project_name}-{version}-py3-none-linux_aarch64.whl",
    )


def _parse_wheel_filename(path: Path) -> tuple[str, str, str]:
    match = re.fullmatch(
        r"(?P<name>.+)-(?P<version>[^-]+)-(?P<tag>py3-none-linux_[a-z0-9_]+)\.whl",
        path.name,
    )
    if not match:
        raise ValueError(f"{path.name}: not a valid wheel filename")
    return match.group("name"), match.group("version"), match.group("tag")


def _parse_sdist_filename(path: Path) -> tuple[str, str]:
    match = re.fullmatch(r"(?P<name>.+)-(?P<version>.+)\.tar\.gz", path.name)
    if not match:
        raise ValueError(f"{path.name}: not a valid sdist filename")
    return match.group("name"), match.group("version")


def _read_metadata_field(payload: bytes, field: str) -> str:
    for line in payload.decode("utf-8").splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"missing metadata field: {field}")


def _read_project_hashes(project_root: Path) -> Dict[str, bytes]:
    source_hashes = {
        name: (project_root / "lib" / name).read_bytes()
        for name in REQUIRED_LIBS
    }
    source_hashes.update(
        {
            name: (project_root / name).read_bytes()
            for name in REQUIRED_RESOURCE_FILES
        }
    )
    return source_hashes


@contextmanager
def _temporary_source_tree(source_root: Path) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        copied = Path(tmp_dir) / source_root.name
        shutil.copytree(source_root, copied)
        yield copied


def _source_hashes(project_root: Path) -> dict[str, bytes]:
    return _read_project_hashes(project_root)


def _read_archive_members(artifact: Path) -> dict[str, bytes]:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact, "r") as archive:
            return {
                member: archive.read(member)
                for member in archive.namelist()
                if not member.endswith("/")
            }

    if artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, "r:gz") as archive:
            return {
                member.name.split("/", 1)[1]: archive.extractfile(member).read()
                for member in archive.getmembers()
                if member.isfile() and "/" in member.name
            }

    raise ValueError(f"Unsupported artifact type: {artifact.name}")


def _validate_elf(path: str, payload: bytes, expected_class: int, expected_machine: int):
    if payload[:4] != b"\x7fELF":
        raise ValueError(f"{path}: expected ELF magic")
    if payload[4] != expected_class:
        raise ValueError(f"{path}: expected ELF class {expected_class}, got {payload[4]}")
    machine = int.from_bytes(payload[18:20], "little")
    if machine != expected_machine:
        raise ValueError(
            f"{path}: expected ELF machine {expected_machine}, got {machine}"
        )


def _validate_record(members: dict[str, bytes], dist_info_prefix: str, artifact: Path) -> None:
    record_name = f"{dist_info_prefix}/RECORD"
    if record_name not in members:
        raise ValueError(f"{artifact.name}: missing RECORD file")

    text = members[record_name].decode("utf-8").splitlines()
    reader = csv.reader(text)
    seen: set[str] = set()

    for row in reader:
        if not row:
            continue
        if len(row) != 3:
            raise ValueError(f"{artifact.name}: malformed RECORD row {row!r}")

        path, digest, size = row
        if path == record_name:
            continue

        if path not in members:
            raise ValueError(f"{artifact.name}: RECORD references missing member {path}")

        if not digest:
            raise ValueError(f"{artifact.name}: missing RECORD hash for {path}")
        if not digest.startswith("sha256="):
            raise ValueError(f"{artifact.name}: unsupported RECORD hash algorithm in {path}")
        if not size:
            raise ValueError(f"{artifact.name}: missing RECORD size for {path}")
        if int(size) < 0:
            raise ValueError(f"{artifact.name}: invalid RECORD size for {path}")

        expected = base64.urlsafe_b64encode(hashlib.sha256(members[path]).digest()).rstrip(b"=").decode(
            "ascii"
        )
        actual = digest.split("=", 1)[1]
        if actual != expected:
            raise ValueError(f"{artifact.name}: RECORD hash mismatch for {path}")
        if int(size) != len(members[path]):
            raise ValueError(f"{artifact.name}: RECORD size mismatch for {path}")
        seen.add(path)

    for path in members:
        if path.endswith("/RECORD"):
            continue
        if path not in seen:
            raise ValueError(f"{artifact.name}: missing RECORD row for {path}")


def _validate_metadata(
    artifact: Path,
    members: dict[str, bytes],
    project_name: str,
    version: str,
    source_hashes: dict[str, bytes],
) -> None:
    normalized_name = _canonical_distribution_name(project_name)

    if artifact.suffix == ".whl":
        wheel_name, wheel_version, wheel_tag = _parse_wheel_filename(artifact)
        if wheel_name != project_name:
            raise ValueError(f"{artifact.name}: unexpected wheel name {wheel_name}")
        if wheel_version != version:
            raise ValueError(f"{artifact.name}: unexpected wheel version {wheel_version}")

        wheel_metadata = next(
            name for name in members if name.endswith(".dist-info/WHEEL")
        )
        wheel_payload = members[wheel_metadata]
        wheel_text = wheel_payload.decode("utf-8")
        if "Root-Is-Purelib: false" not in wheel_text:
            raise ValueError(f"{artifact.name}: Root-Is-Purelib must be false")
        if f"Tag: {wheel_tag}" not in wheel_text:
            raise ValueError(f"{artifact.name}: WHEEL tag mismatch: expected {wheel_tag}")
        if "py3-none-any" in wheel_text:
            raise ValueError(f"{artifact.name}: universal wheel detected")

        metadata_name = next(
            name for name in members if name.endswith(".dist-info/METADATA")
        )
        metadata_name_value = _read_metadata_field(members[metadata_name], "Name")
        if _canonical_distribution_name(metadata_name_value) != normalized_name:
            raise ValueError(f"{artifact.name}: metadata name mismatch: {metadata_name_value}")
        metadata_version = _read_metadata_field(members[metadata_name], "Version")
        if metadata_version != version:
            raise ValueError(f"{artifact.name}: metadata version mismatch: {metadata_version}")

        dist_info_prefix = wheel_metadata.split("/")[0]
        _validate_record(members, dist_info_prefix, artifact)
    elif artifact.suffix == ".gz":
        metadata_name = next(
            name
            for name in members
            if name.endswith(".dist-info/METADATA") or name.endswith("PKG-INFO")
        )
        metadata_name_value = _read_metadata_field(members[metadata_name], "Name")
        if _canonical_distribution_name(metadata_name_value) != normalized_name:
            raise ValueError(f"{artifact.name}: metadata name mismatch: {metadata_name_value}")
        metadata_version = _read_metadata_field(members[metadata_name], "Version")
        if metadata_version != version:
            raise ValueError(f"{artifact.name}: metadata version mismatch: {metadata_version}")
    else:
        raise ValueError(f"{artifact.name}: unsupported artifact type")

    normalized_members = {
        _normalize_package_path(path): payload for path, payload in members.items()
    }

    if not (set(REQUIRED_PACKAGE_FILES) <= normalized_members.keys()):
        missing = set(REQUIRED_PACKAGE_FILES) - normalized_members.keys()
        raise ValueError(f"{artifact.name}: missing package files {sorted(missing)}")

    if not all(name in normalized_members for name in REQUIRED_LIBS):
        missing = set(REQUIRED_LIBS) - normalized_members.keys()
        raise ValueError(f"{artifact.name}: missing native libraries {sorted(missing)}")

    for path, (expected_class, expected_machine) in REQUIRED_LIBS.items():
        payload = normalized_members[path]
        _validate_elf(path, payload, expected_class, expected_machine)
        if hashlib.sha256(payload).digest() != hashlib.sha256(source_hashes[path]).digest():
            raise ValueError(f"{artifact.name}: byte mismatch for {path}")

    for path in REQUIRED_RESOURCE_FILES:
        payload = normalized_members[path]
        if hashlib.sha256(payload).digest() != hashlib.sha256(source_hashes[path]).digest():
            raise ValueError(f"{artifact.name}: byte mismatch for {path}")

    runtime_version = read_runtime_version(
        normalized_members["cluster_monitor/__init__.py"]
    )
    if runtime_version != version:
        raise ValueError(
            f"{artifact.name}: runtime version mismatch: expected {version}, "
            f"got {runtime_version}"
        )


def _run_build(command: list[str], cwd: Path) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Build failed: {message}")

    if result.stderr.strip():
        sys.stderr.write(result.stderr)


def _build_with_setup_py(project_root: Path, output_dir: Path, platform: str | None) -> None:
    command = [sys.executable, "setup.py"]
    if platform is None:
        command.extend(["sdist", "--dist-dir", str(output_dir)])
    else:
        command.extend(
            [
                "bdist_wheel",
                "--dist-dir",
                str(output_dir),
                "--python-tag",
                "py3",
                "--plat-name",
                platform,
            ]
        )
    _run_build(command, project_root)


def _collect_artifacts(output_dir: Path) -> list[Path]:
    return sorted(p for p in output_dir.iterdir() if p.is_file())


def _clear_output_dir(output_dir: Path, expected_names: tuple[str, ...]) -> Path:
    # Reject the selected path itself before resolving it, since resolve() would
    # otherwise silently redirect output into a symlink target.
    if output_dir.is_symlink():
        raise ValueError(f"Output directory must not be a symlink: {output_dir}")

    output_dir = output_dir.resolve()
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        return output_dir

    expected = set(expected_names)
    entries = list(output_dir.iterdir())
    invalid: list[str] = []
    for path in entries:
        if path.name not in expected:
            invalid.append(path.name)
        elif path.is_symlink() or not path.is_file():
            invalid.append(path.name)

    if invalid:
        raise ValueError(
            f"Output directory contains entries that cannot be replaced: {sorted(invalid)}"
        )

    # Delete only after the complete directory passed preflight.
    for path in entries:
        path.unlink()
    return output_dir


def _validate_artifact_set(
    output_dir: Path,
    project_name: str,
    version: str,
    project_root: Path,
) -> None:
    artifacts = _collect_artifacts(output_dir)
    names = [artifact.name for artifact in artifacts]
    expected_names = list(_expected_artifact_names(project_name, version))
    if sorted(names) != sorted(expected_names):
        raise ValueError(f"Unexpected artifact set: {sorted(names)} != {sorted(expected_names)}")

    source_hashes = _read_project_hashes(project_root)
    for artifact in artifacts:
        members = _read_archive_members(artifact)
        _validate_metadata(
            artifact,
            members,
            project_name,
            version,
            source_hashes,
        )


def _build(output_dir: Path, project_root: Path) -> int:
    project_name, version = _read_project_metadata(project_root)
    expected_names = _expected_artifact_names(project_name, version)
    output_dir = _clear_output_dir(output_dir, expected_names)
    with _temporary_source_tree(project_root) as source_root:
        _build_with_setup_py(source_root, output_dir, None)
        for platform in WHEEL_PLATFORMS:
            _build_with_setup_py(source_root, output_dir, platform)

        _validate_artifact_set(output_dir, project_name, version, source_root)
    return 0


def build_release(output_dir: Path, release_tag: str) -> int:
    project_root = Path(__file__).resolve().parents[1]
    with prepare_release_tree(project_root, release_tag) as release_root:
        return _build(output_dir, Path(release_root))


def _validate_artifact_names_and_metadata(
    project_name: str,
    version: str,
    artifact: Path,
) -> None:
    if artifact.suffix == ".whl":
        wheel_name, wheel_version, wheel_tag = _parse_wheel_filename(artifact)
        if wheel_name != project_name:
            raise ValueError(f"{artifact.name}: unexpected wheel name {wheel_name}")
        if wheel_version != version:
            raise ValueError(f"{artifact.name}: unexpected wheel version {wheel_version}")
        if wheel_tag not in {f"py3-none-{platform}" for platform in WHEEL_PLATFORMS}:
            raise ValueError(f"{artifact.name}: unexpected wheel platform {wheel_tag}")
        return

    sdist_name, sdist_version = _parse_sdist_filename(artifact)
    if sdist_name != project_name:
        raise ValueError(f"{artifact.name}: unexpected sdist name {sdist_name}")
    if sdist_version != version:
        raise ValueError(f"{artifact.name}: unexpected sdist version {sdist_version}")


def validate_artifact(
    artifact: Path,
    expected_version: str,
    project_root: Path | None = None,
) -> None:
    """Validate one release artifact against a canonical expected version.

    This public helper is shared with local publication validation. It reads
    archive bytes only and never imports packaged code.
    """

    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    project_name, _ = _read_project_metadata(root)
    version = validate_canonical_version(expected_version)
    artifact = Path(artifact)
    _validate_artifact_names_and_metadata(project_name, version, artifact)
    members = _read_archive_members(artifact)
    _validate_metadata(
        artifact,
        members,
        project_name,
        version,
        _source_hashes(root),
    )


def validate_release_artifacts(
    artifacts: list[Path],
    expected_version: str,
    project_root: Path | None = None,
) -> list[Path]:
    """Validate the exact three release artifacts and return their paths."""

    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    project_name, _ = _read_project_metadata(root)
    version = validate_canonical_version(expected_version)
    selected = sorted((Path(artifact) for artifact in artifacts), key=lambda p: p.name)
    expected_names = sorted(_expected_artifact_names(project_name, version))
    actual_names = [artifact.name for artifact in selected]
    if actual_names != expected_names:
        raise ValueError(
            f"Unexpected artifact set: {actual_names} != {expected_names}"
        )
    for artifact in selected:
        validate_artifact(artifact, version, root)
    return selected


def verify(artifact: Path, release_tag: str | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    _, checkout_version = _read_project_metadata(project_root)
    version = parse_release_tag(release_tag) if release_tag is not None else checkout_version
    validate_artifact(artifact, version, project_root)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--release-tag")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)

    if args.verify:
        try:
            return verify(args.verify, args.release_tag)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
    if args.release_tag:
        return build_release(args.output_dir, args.release_tag)
    return _build(args.output_dir, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
