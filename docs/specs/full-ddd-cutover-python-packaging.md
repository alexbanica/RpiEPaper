# Spec: Full DDD Cutover with Python Standard Packaging

> Superseded in part by `docs/specs/prune-unused-python-modules.md` for legacy-wrapper removal.

## Purpose
Rewrite the production `cluster_monitor` project to a DDD/onion architecture while preserving runtime behavior and CLI/config compatibility.

## Definitions
- Domain layer: entities and service interfaces.
- Application layer: orchestration use-cases for monitor runtime and monitor client mode.
- Infrastructure layer: Docker, SSH, Raspberry Pi, config parser implementations.
- Presentation layer: CLI controller and renderers.

## Behavior
1. Existing CLI flags remain compatible: `-r`, `-p`, `-mc`, `-mc-hdd`.
2. Existing YAML configuration keys remain compatible under `cluster_monitor.*`.
3. Existing runtime behavior remains compatible for:
- renderer selection
- remote command execution
- cluster hat health checks and alerting
- periodic display refresh
4. Legacy module paths remain import-compatible via wrappers.
5. Dependencies are installable via `pip` and `requirements*.txt` and package metadata via `pyproject.toml`.

## Invariants
1. Python version support remains `>=3.9`.
2. No HTTP API endpoints are introduced in this spec.
3. No OpenAPI events are introduced in this spec.
4. Project-owner exception: no `http/` folder or `.http` files for CLI-only controllers.

## Constraints
1. One big cutover.
2. Branch is isolated from `main`.
3. Tests cover critical business logic transforms and config parsing.

## Assumptions
1. Hardware-specific dependencies continue to be installed through platform-specific requirements files.
2. Production runtime still executes as `python -m cluster_monitor`.

## Acceptance Criteria
1. `python -m compileall cluster_monitor` succeeds.
2. `python -m unittest discover -s tests` succeeds.
3. Legacy imports from `cluster_monitor.services`, `cluster_monitor.dto`, and `cluster_monitor.renderers` remain valid.
