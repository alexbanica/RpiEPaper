# AGENTS

## Active Spec
- `docs/specs/storage-temperature-disk-usages.md`

## Branch
- `spec/storage-temperature-disk-usages`

## Architecture Rules
- DDD/onion split:
- `cluster_monitor/domain`
- `cluster_monitor/application`
- `cluster_monitor/infrastructure`
- `cluster_monitor/presentation`
- Interfaces are named with `Interface` suffix.
- Service implementations match interface names without suffix.
- Legacy wrapper module paths were removed; use canonical DDD module paths only.

## Packaging Rules
- `pyproject.toml` is source of package metadata.
- `requirements.txt` + `requirements/*.txt` are the dependency install flows.

## HTTP/OpenAPI
- No HTTP controllers in this project.
- Exception approved by project owner: no `http/` folder or `.http` files are required for this CLI-only system.
- No swagger/openapi event files are required for this spec.
