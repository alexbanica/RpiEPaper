"""Forgejo publish orchestration helpers."""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from scripts.release_version import parse_release_tag



class ArtifactValidationError(RuntimeError):
    """Raised when the artifact directory does not contain the required set."""


class PublishError(RuntimeError):
    """Raised when upload or verification operations fail."""


PROJECT_NAME = "cluster_monitor"
SDIST_SUFFIX = ".tar.gz"
WHEEL_SUFFIX = ".whl"
ARMV7_WHEEL = "-py3-none-linux_armv7l.whl"
AARCH64_WHEEL = "-py3-none-linux_aarch64.whl"
DEFAULT_REPOSITORY_URL = "https://forgejo.alexlab.nl/api/packages/public/pypi"
DEFAULT_SIMPLE_INDEX_URL = "https://forgejo.alexlab.nl/api/packages/public/pypi/simple"
DEFAULT_DEPENDENCY_INDEX_URL = "https://pypi.org/simple"
REQUIRED_LIBRARY_FILES = (
    "DEV_Config_32.so",
    "DEV_Config_64.so",
    "sysfs_gpio.so",
    "sysfs_software_spi.so",
)
REQUIRED_RESOURCE_FILES = (
    "Font.ttc",
    "config.yml",
)
LIBRARY_SOURCE_DIR = Path(__file__).resolve().parents[1] / "lib" / "waveshare_epd"
RESOURCE_SOURCE_DIR = Path(__file__).resolve().parents[1] / PROJECT_NAME / "resources"


def _resolve_credentials() -> tuple[str, str]:
    username = os.environ.get("FORGEJO_PACKAGE_USERNAME")
    token = os.environ.get("FORGEJO_PACKAGE_TOKEN")
    if not username or not token:
        raise PublishError("missing Forgejo publish credentials in environment")
    return username, token


def _sanitize_pip_environment() -> dict[str, str]:
    env = {}
    for key, value in os.environ.items():
        if key.startswith("PIP_") or key in {
            "FORGEJO_PACKAGE_USERNAME",
            "FORGEJO_PACKAGE_TOKEN",
        }:
            continue
        env[key] = value

    env.update(
        {
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_NO_INPUT": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_CACHE_DIR": "1",
        }
    )
    return env


def validate_artifacts(artifact_dir: Path, version: str) -> list[Path]:
    """Return validated artifact paths for ``version`` and reject conflicts.

    Unrelated non-package files are ignored.
    """

    artifact_dir = Path(artifact_dir)
    expected = {
        artifact_dir / f"{PROJECT_NAME}-{version}{SDIST_SUFFIX}",
        artifact_dir / f"{PROJECT_NAME}-{version}{ARMV7_WHEEL}",
        artifact_dir / f"{PROJECT_NAME}-{version}{AARCH64_WHEEL}",
    }
    conflict_artifacts: list[Path] = []

    if not artifact_dir.is_dir():
        raise ArtifactValidationError(f"artifact directory does not exist: {artifact_dir}")

    for artifact in artifact_dir.iterdir():
        if not artifact.is_file():
            continue
        if artifact.name.startswith("README"):
            continue

        if not artifact.name.startswith(f"{PROJECT_NAME}-"):
            continue
        if not artifact.name.endswith((SDIST_SUFFIX, ARMV7_WHEEL, AARCH64_WHEEL)):
            if artifact.suffix in {".gz", ".whl", ".zip"}:
                conflict_artifacts.append(artifact)
            continue

        if artifact not in expected:
            conflict_artifacts.append(artifact)

    if conflict_artifacts:
        names = ", ".join(sorted(artifact.name for artifact in conflict_artifacts))
        raise ArtifactValidationError(f"conflicting package artifacts found: {names}")

    missing = sorted(str(path.name) for path in expected if not path.exists())
    if missing:
        raise ArtifactValidationError(f"missing required artifacts: {missing}")

    return [path for path in sorted(expected)]


def _sanitize_environment() -> dict[str, str]:
    env = {}
    for key, value in os.environ.items():
        if key.startswith("TWINE_") or key in {
            "FORGEJO_PACKAGE_USERNAME",
            "FORGEJO_PACKAGE_TOKEN",
        }:
            continue
        env[key] = value
    return env


def _run_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, env=env, text=True)
    except FileNotFoundError as error:
        raise PublishError(f"command not found: {command[0]}") from error


def _run_twine_check(artifacts: Iterable[Path]) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        "-m",
        "twine",
        "check",
        "--strict",
        *map(str, artifacts),
    ]
    return _run_command(command, env=_sanitize_environment())


def _run_upload(
    artifacts: list[Path],
    username: str,
    token: str,
    repository_url: str,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--non-interactive",
        "--repository-url",
        repository_url,
        "--disable-progress-bar",
        *map(str, artifacts),
    ]
    env = _sanitize_environment()
    env.update({
        "TWINE_USERNAME": username,
        "TWINE_PASSWORD": token,
        "TWINE_REPOSITORY_URL": repository_url,
        "TWINE_NON_INTERACTIVE": "1",
    })
    return _run_command(command, env=env)


def _run_pip_install(
    target: str,
    version: str,
    simple_index_url: str,
    target_root: Path,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        f"cluster-monitor=={version}",
        "--no-deps",
        "--index-url",
        simple_index_url,
        "--platform",
        target,
        "--only-binary=:all:",
        "--target",
        str(target_root),
        "--isolated",
        "--no-input",
        "--no-cache-dir",
    ]
    return _run_command(command, env=_sanitize_pip_environment())


def _run_dependency_install(
    version: str,
    simple_index_url: str,
    dependency_index_url: str,
    target_root: Path,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        f"cluster-monitor=={version}",
        "--index-url",
        simple_index_url,
        "--extra-index-url",
        dependency_index_url,
        "--target",
        str(target_root),
        "--isolated",
        "--no-input",
        "--no-cache-dir",
    ]
    return _run_command(command, env=_sanitize_pip_environment())


def _validate_dependency_install(version: str, target_root: Path) -> None:
    metadata = target_root / f"{PROJECT_NAME}-{version}.dist-info" / "METADATA"
    if not metadata.is_file():
        raise PublishError(f"dependency-resolving install metadata missing: {metadata}")

    metadata_version = _read_metadata_version(metadata)
    if metadata_version != version:
        raise PublishError(
            "dependency-resolving install metadata version mismatch: "
            f"expected {version}, got {metadata_version}"
        )

    _validate_installed_resources(target_root)


def _validate_installed_resources(target_root: Path) -> None:
    for name in REQUIRED_RESOURCE_FILES:
        installed_resource = target_root / PROJECT_NAME / "resources" / name
        if not installed_resource.is_file():
            raise PublishError(f"installed resource missing: {name}")

        source_resource = RESOURCE_SOURCE_DIR / name
        if not source_resource.is_file():
            raise PublishError(f"source resource missing: {source_resource}")
        if installed_resource.read_bytes() != source_resource.read_bytes():
            raise PublishError(f"installed resource bytes mismatch: {name}")


def _validate_imported_cluster_monitor(version: str, target_root: Path) -> None:
    command = [
        sys.executable,
        "-I",
        "-c",
        (
            "import pathlib, sys\n"
            "target = pathlib.Path(sys.argv[1]).resolve()\n"
            "sys.path.insert(0, str(target))\n"
            "import cluster_monitor\n"
            "module_file = pathlib.Path(cluster_monitor.__file__).resolve()\n"
            "if not module_file.is_relative_to(target):\n"
            "    raise SystemExit('cluster_monitor import path mismatch')\n"
            "if getattr(cluster_monitor, '__version__', None) != sys.argv[2]:\n"
            "    raise SystemExit('cluster_monitor version mismatch')\n"
        ),
        str(target_root.resolve()),
        version,
    ]
    env = _sanitize_pip_environment()
    env.pop("PYTHONPATH", None)
    result = _run_command(command, env=env)
    if result.returncode != 0:
        raise PublishError(f"cluster_monitor import validation failed for {target_root}")


def verify_installations(
    version: str,
    simple_index_url: str,
    targets: tuple[str, ...],
    install_root: Path,
    dependency_index_url: str = DEFAULT_DEPENDENCY_INDEX_URL,
) -> list[subprocess.CompletedProcess]:
    """Validate dependencies and published artifacts for each target platform."""

    dependency_root = Path(install_root) / "dependency-resolution"
    dependency_result = _run_dependency_install(
        version=version,
        simple_index_url=simple_index_url,
        dependency_index_url=dependency_index_url,
        target_root=dependency_root,
    )
    if dependency_result.returncode != 0:
        raise PublishError("dependency-resolving pip install failed")
    _validate_dependency_install(version=version, target_root=dependency_root)

    results: list[subprocess.CompletedProcess] = [dependency_result]
    for target in targets:
        target_root = Path(install_root) / target
        target_root.mkdir(parents=True, exist_ok=True)
        result = _run_pip_install(target, version, simple_index_url, target_root)
        if result.returncode != 0:
            raise PublishError(f"pip install failed for {target}")
        results.append(result)

        installed_libraries: list[Path] = []
        for name in REQUIRED_LIBRARY_FILES:
            installed_library = target_root / "waveshare_epd" / name
            installed_libraries.append(installed_library)

        runtime_file = target_root / PROJECT_NAME / "__init__.py"
        validate_installation(
            target=target_root,
            installed_libraries=installed_libraries,
            version=version,
            runtime_file=runtime_file,
        )
        _validate_imported_cluster_monitor(version=version, target_root=target_root)

    return results


def _read_runtime_version(runtime_file: Path) -> str:
    try:
        tree = ast.parse(runtime_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, SyntaxError) as error:
        raise PublishError(f"unable to read runtime file: {runtime_file}") from error

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(target.id == "__version__" for target in node.targets if isinstance(target, ast.Name)):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
        if isinstance(node.value, ast.Str):
            return node.value.s

    raise PublishError(f"__version__ assignment not found: {runtime_file}")


def _read_metadata_version(metadata_file: Path) -> str:
    for line in metadata_file.read_text(encoding="utf-8").splitlines():
        if not line.startswith("Version:"):
            continue
        return line.split(":", 1)[1].strip()
    raise PublishError(f"Version field not found in metadata: {metadata_file}")


def _collect_dist_info_directories(target: Path) -> list[Path]:
    return sorted(
        path
        for path in target.iterdir()
        if path.is_dir() and path.name.endswith(".dist-info")
    )


def _validate_dist_info_directory(target: Path, version: str) -> Path:
    dist_info_dirs = _collect_dist_info_directories(target)
    if not dist_info_dirs:
        raise PublishError(f"dist-info directory missing in {target}")

    expected_dist_info = target / f"{PROJECT_NAME}-{version}.dist-info"
    if expected_dist_info not in dist_info_dirs:
        names = ", ".join(path.name for path in dist_info_dirs)
        raise PublishError(f"nonstandard dist-info directory for installed package: {names}")

    if len(dist_info_dirs) != 1:
        conflicting = [path.name for path in dist_info_dirs if path != expected_dist_info]
        if conflicting:
            raise PublishError(f"conflicting dist-info directories found: {', '.join(conflicting)}")

    return expected_dist_info


def validate_installation(
    target: Path,
    installed_libraries: list[Path],
    version: str,
    runtime_file: Path,
) -> None:
    """Validate package metadata, runtime version, and required shared libraries."""

    target = Path(target)
    runtime_file = Path(runtime_file)

    if not target.is_dir():
        raise PublishError(f"target not found: {target}")

    dist_info = _validate_dist_info_directory(target, version)
    metadata = dist_info / "METADATA"
    if not metadata.exists():
        raise PublishError(f"metadata missing: {metadata}")
    metadata_version = _read_metadata_version(metadata)
    if metadata_version != version:
        raise PublishError(
            f"installed metadata version mismatch: expected {version}, got {metadata_version}"
        )

    if not runtime_file.exists():
        raise PublishError(f"runtime file missing: {runtime_file}")
    runtime_version = _read_runtime_version(runtime_file)
    if runtime_version != version:
        raise PublishError(
            f"installed runtime version mismatch: expected {version}, got {runtime_version}"
        )

    installed_library_names = [Path(path).name for path in installed_libraries]
    missing_supplied = [
        name for name in REQUIRED_LIBRARY_FILES if name not in installed_library_names
    ]
    if missing_supplied:
        raise PublishError(f"installed library list missing: {', '.join(missing_supplied)}")

    for name in REQUIRED_LIBRARY_FILES:
        installed_library = target / "waveshare_epd" / name
        if not installed_library.is_file():
            raise PublishError(f"installed library missing: {name}")
        if installed_library.stat().st_size == 0:
            raise PublishError(f"installed library is empty: {name}")

        source_library = LIBRARY_SOURCE_DIR / name
        if not source_library.is_file():
            raise PublishError(f"source library missing: {source_library}")
        if installed_library.read_bytes() != source_library.read_bytes():
            raise PublishError(f"installed library bytes mismatch: {name}")

    _validate_installed_resources(target)


def _create_work_dir(work_dir: Path | None, artifact_dir: Path) -> Path:
    if work_dir is None:
        return Path(tempfile.mkdtemp(prefix="publish-work-", dir=artifact_dir.parent))

    requested = Path(work_dir)
    if requested.exists():
        raise PublishError(f"work_dir already exists and must not be reused: {requested}")

    requested.mkdir(parents=True, exist_ok=False)
    return requested


def publish(
    artifact_dir: Path,
    version: str,
    username: str,
    token: str,
    repository_url: str,
    simple_index_url: str,
    work_dir: Path | None = None,
    dependency_index_url: str = DEFAULT_DEPENDENCY_INDEX_URL,
) -> bool:
    """Validate artifacts and publish them to Forgejo with credential scoping."""

    artifact_dir = Path(artifact_dir)
    artifacts = validate_artifacts(artifact_dir, version)
    work_dir = _create_work_dir(work_dir=work_dir, artifact_dir=artifact_dir)
    verify_root = work_dir / "installs"

    try:
        check = _run_twine_check(artifacts)
        if getattr(check, "returncode", 1) != 0:
            raise PublishError("artifact validation failed")

        upload = _run_upload(artifacts, username, token, repository_url)
        if getattr(upload, "returncode", 1) != 0:
            raise PublishError("forgejo upload failed")

        verify_installations(
            version=version,
            simple_index_url=simple_index_url,
            dependency_index_url=dependency_index_url,
            targets=("linux_armv7l", "linux_aarch64"),
            install_root=verify_root,
        )
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

    return True


def _normalize_version(version: str | None) -> str:
    if version:
        return version

    tag = os.environ.get("GITHUB_REF_NAME")
    if not tag:
        raise PublishError("version was not provided and GITHUB_REF_NAME is unset")
    return parse_release_tag(tag)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", nargs="?", type=Path, default=Path("dist"))
    parser.add_argument("--version", default=None)
    parser.add_argument("--repository-url", default=DEFAULT_REPOSITORY_URL)
    parser.add_argument("--simple-index-url", default=DEFAULT_SIMPLE_INDEX_URL)
    parser.add_argument("--dependency-index-url", default=DEFAULT_DEPENDENCY_INDEX_URL)
    args = parser.parse_args(argv)

    try:
        version = _normalize_version(args.version)
        username, token = _resolve_credentials()
        publish(
            artifact_dir=args.artifact_dir,
            version=version,
            username=username,
            token=token,
            repository_url=args.repository_url,
            simple_index_url=args.simple_index_url,
            dependency_index_url=args.dependency_index_url,
        )
    except PublishError as error:
        raise SystemExit(f"publish failed: {error}") from error

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
