# AGENTS

## Domain-only test policy

- Automated tests of any kind, including unit, integration, contract, snapshot,
  workflow, and configuration tests, may be created or maintained only for
  deterministic domain source logic in this project.
- Do not create or maintain tests for anything outside domain source logic,
  including application orchestration, infrastructure and adapters,
  presentation, UI and controllers, Docker or container files, GitHub Actions
  or other CI/CD workflows, deployment and configuration, packaging and release
  scripts, tooling, or other operational code.
- Validate non-domain changes with appropriate static, syntax, lint, type,
  structural, build, dry-run, smoke, runtime, or operator checks instead of
  automated tests.
- If this project has no domain source logic, automated testing and test-first
  work are not applicable.
- This policy supersedes any more general testing or validation wording
  elsewhere in this file.

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
- `cluster_monitor/resources/config.yml` is the packaged default runtime
  configuration; `CLUSTER_MONITOR_CONFIG_FILE` selects one exact external YAML
  override, and otherwise the runtime checks `./resources` for established
  external configuration filenames.
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
