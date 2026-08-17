# AGENTS

## Active Spec
- `docs/specs/prune-unused-python-modules.md`

## Branch
- `spec/prune-unused-python-modules`

## Architecture Rules
- DDD/onion split:
- `cluster_monitor/domain`: entities and domain service interfaces for cluster, node, Docker, disk, and temperature status.
- `cluster_monitor/application`: orchestration services that coordinate monitoring use cases.
- `cluster_monitor/infrastructure`: adapters for YAML config parsing, SSH/command execution, Docker/system metrics parsing, and hardware/runtime integrations.
- `cluster_monitor/presentation`: CLI controllers, request objects, and ePaper/rendering output.
- `cluster_monitor/shared`: constants and shared values only.
- Dependencies point inward: presentation and infrastructure may depend on application/domain contracts, but domain must not depend on infrastructure, presentation, SSH, Docker, ePaper, or filesystem details.
- Interfaces are named with `Interface` suffix.
- Abstract classes are prefixed with `Abstract`.
- Implementations of abstract classes remove the `Abstract` prefix and keep the remaining name.
- Service implementations match interface names without suffix.
- Legacy wrapper module paths were removed; use canonical DDD module paths only.

## Project-Specific Architecture
- `cluster_monitor/domain/entities`: core status entities used by renderers and services.
- `cluster_monitor/domain/services`: domain-facing service contracts.
- `cluster_monitor/application/services`: monitor orchestration and aggregation use cases.
- `cluster_monitor/infrastructure/parsers`: parsing adapters for command output and raw system data.
- `cluster_monitor/infrastructure/services`: concrete adapters for remote and local status collection.
- `cluster_monitor/presentation/controllers`: runtime CLI/controller coordination.
- `cluster_monitor/presentation/controllers/requests`: request DTOs for invocation modes.
- `cluster_monitor/presentation/renderers`: renderer abstractions and concrete output rendering.
- `cluster_monitor/presentation/renderers/epapers`: Waveshare/ePaper-specific rendering adapters.
- `resources/config.yml` is the default runtime configuration.
- `tests/` contains deterministic unit coverage only for domain logic.

## Test Scope
- Write and maintain unit tests only for logic under `cluster_monitor/domain`.
- Do not create unit tests for code outside `cluster_monitor/domain`, including
  GitHub Actions workflows, files under `scripts/`, package/build/release/publish
  behavior, application orchestration, infrastructure adapters, presentation
  code, configuration wiring, or runtime integrations.
- Validate non-domain changes with appropriate static, syntax, structural, or
  operator checks instead of adding unit tests.
- Create test-first work units or assign test-focused subagents only when the
  requested change affects testable domain logic.

## Packaging Rules
- `pyproject.toml` is source of package metadata.
- `requirements.txt` + `requirements/*.txt` are the dependency install flows.

## HTTP/OpenAPI
- No HTTP controllers in this project.
- Exception approved by project owner: no `http/` folder or `.http` files are required for this CLI-only system.
- No swagger/openapi event files are required for this spec.
