"""Release version validation and release-tree preparation helpers."""

from __future__ import annotations

import ast
import contextlib
import re
import shutil
from contextlib import ExitStack
from pathlib import Path
import tempfile
from typing import Iterator


_STABLE_TAG_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_BETA_TAG_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)-beta([1-9][0-9]*)$"
)
_PROJECT_VERSION_RE = re.compile(r'^\s*version\s*=\s*"[^"]+"\s*$')
_RUNTIME_VERSION_RE = re.compile(r'__version__\s*=\s*"[^"]+"')
_CANONICAL_VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:b([1-9][0-9]*))?$"
)


def validate_canonical_version(version: str) -> str:
    """Return a stable or PEP 440 beta version in canonical form."""

    if not isinstance(version, str) or not _CANONICAL_VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid canonical version: {version}")
    return version


def parse_release_tag(tag: str) -> str:
    """Return canonical Python version for an accepted release tag."""

    match = _STABLE_TAG_RE.match(tag)
    if match:
        return validate_canonical_version(".".join(match.groups()))

    match = _BETA_TAG_RE.match(tag)
    if match:
        major, minor, patch, beta = match.groups()
        return validate_canonical_version(f"{major}.{minor}.{patch}b{beta}")

    raise ValueError(f"Invalid release tag: {tag}")


def read_runtime_version(source: bytes) -> str:
    """Read a literal ``__version__`` assignment without executing source."""

    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError, ValueError) as error:
        raise ValueError("unable to parse packaged runtime version source") from error

    def assigns_version(target: ast.expr) -> bool:
        if isinstance(target, ast.Name):
            return target.id == "__version__"
        if isinstance(target, (ast.Tuple, ast.List)):
            return any(assigns_version(element) for element in target.elts)
        if isinstance(target, ast.Starred):
            return assigns_version(target.value)
        return False

    assignments = []
    for node in ast.walk(tree):
        targets: tuple[ast.expr, ...] = ()
        if isinstance(node, ast.Assign):
            targets = tuple(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (node.target,)
        if any(assigns_version(target) for target in targets):
            assignments.append(node)

    if len(assignments) != 1 or assignments[0] not in tree.body:
        raise ValueError(
            "expected exactly one direct module-level __version__ assignment, "
            f"found {len(assignments)}"
        )
    assignment = assignments[0]
    if (
        not isinstance(assignment, ast.Assign)
        or len(assignment.targets) != 1
        or not isinstance(assignment.targets[0], ast.Name)
        or assignment.targets[0].id != "__version__"
    ):
        raise ValueError("packaged __version__ must use a direct name assignment")
    value = assignment.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        raise ValueError("packaged __version__ must be a string literal")
    return value.value


def _replace_version_line(
    text: str, pattern: re.Pattern[str], replacement: str, *, file_label: str
) -> str:
    lines = text.splitlines(True)
    updated_lines = []
    count = 0
    for line in lines:
        if pattern.match(line):
            count += 1
            updated_lines.append(replacement)
        else:
            updated_lines.append(line)

    if count != 1:
        raise ValueError(f"Expected exactly one {file_label} version line, found {count}")

    return "".join(updated_lines)


@contextlib.contextmanager
def prepare_release_tree(source: Path, tag: str) -> Iterator[str]:
    """Create and yield an isolated copy with aligned release versions."""

    source_path = Path(source).resolve()
    canonical_version = parse_release_tag(tag)

    with ExitStack() as stack:
        temp_root = stack.enter_context(tempfile.TemporaryDirectory())
        release_path = Path(temp_root) / source_path.name

        shutil.copytree(source_path, release_path)
        try:
            pyproject_path = release_path / "pyproject.toml"
            init_path = release_path / "cluster_monitor" / "__init__.py"

            pyproject_contents = pyproject_path.read_text(encoding="utf-8")
            pyproject_updated = _replace_version_line(
                pyproject_contents,
                _PROJECT_VERSION_RE,
                f'version = "{canonical_version}"\n',
                file_label="project",
            )
            pyproject_path.write_text(pyproject_updated, encoding="utf-8")

            init_contents = init_path.read_text(encoding="utf-8")
            init_updated = _replace_version_line(
                init_contents,
                _RUNTIME_VERSION_RE,
                f'__version__ = "{canonical_version}"\n',
                file_label="runtime",
            )
            init_path.write_text(init_updated, encoding="utf-8")
        except Exception:
            raise

        try:
            yield str(release_path)
        finally:
            # TemporaryDirectory handles cleanup on exit from this context.
            pass
        # explicit cleanup point retained by context exit path management
