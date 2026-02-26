# Spec: Prune Unused Python Modules and Folders

## Purpose
Reduce repository ambiguity by removing Python modules/folders that are not used by runtime entrypoints, tests, or packaging metadata.

## Definitions
- Runtime entrypoint: `python -m cluster_monitor` resolved via `cluster_monitor/__main__.py`.
- Canonical module paths: `cluster_monitor.domain`, `cluster_monitor.application`, `cluster_monitor.infrastructure`, `cluster_monitor.presentation`, `cluster_monitor.shared`.
- Unused module/folder: has no local references from runtime/tests/packaging and is outside canonical module paths.

## Behavior
1. Keep runtime behavior and CLI compatibility unchanged.
2. Remove legacy compatibility wrappers and migrate to canonical module paths.
3. Remove only modules/folders that are outside the canonical surface and currently unreferenced.
4. Remove local environment noise from workspace (`venv/`) and ignore it in git.

## Invariants
1. `python3 -m compileall cluster_monitor` succeeds.
2. `python3 -m unittest discover -s tests` succeeds.
3. Packaging metadata remains driven by `pyproject.toml`.

## Constraints
1. No API/HTTP/OpenAPI artifacts are introduced.
2. Cleanup is done on an isolated spec branch.

## Assumptions
1. Consumers are migrated to canonical imports and do not require legacy wrapper module paths.
2. Empty placeholder packages without behavior can be removed when not referenced.

## Approved Removals
1. `cluster_monitor/helpers/`
2. `cluster_monitor/infrastructure/repositories/` (empty placeholder package)
3. `cluster_monitor/presentation/controllers/responses/` (empty placeholder package)
4. Top-level wrappers:
- `cluster_monitor/main.py`
- `cluster_monitor/ClusterMonitor.py`
- `cluster_monitor/MonitorClient.py`
5. Legacy wrapper packages:
- `cluster_monitor/services/`
- `cluster_monitor/dto/`
- `cluster_monitor/renderers/`
6. Untracked local `venv/` folder
