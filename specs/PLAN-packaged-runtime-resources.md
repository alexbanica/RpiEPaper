# Packaged runtime resources plan

Status: Approved

## Spec reference

`specs/SPEC-packaged-runtime-resources.md`

## Affected files

- `AGENTS.md`
- `README.md`
- `cluster_monitor/application/services/runtime_service.py`
- `cluster_monitor/infrastructure/parsers/yaml_config_parser.py`
- `cluster_monitor/shared/constants.py`
- `cluster_monitor/resources/Font.ttc`
- `cluster_monitor/resources/config.yml`
- `resources/Font.ttc` (relocated)
- `resources/config.yml` (relocated)
- `pyproject.toml`
- `scripts/package_artifacts.py`
- `scripts/publish_forgejo.py`
- `specs/SPEC-packaged-runtime-resources.md`
- `specs/PLAN-packaged-runtime-resources.md`

## Implementation performed

1. Relocated the tracked font and default configuration into the installable
   `cluster_monitor` package without changing their contents.
2. Changed resource lookup to use the imported package directory.
3. Added packaged-default-first configuration loading with an external
   `CLUSTER_MONITOR_CONFIG_DIR` or `./resources` override.
4. Declared the font and YAML file as `cluster_monitor` package data.
5. Strengthened build validation to require both resources and compare their
   bytes in all three artifacts.
6. Strengthened post-publication verification to check both installed
   resources and their bytes.
7. Updated operator and repository documentation.
8. Recorded the delivered behavior in this approved spec and plan.

## Validation run

- Bytecode-redirected Python compilation for all changed modules.
- Deterministic build of one sdist and both ARM platform wheels.
- Archive presence and exact-byte validation for the font and default config.
- No-dependency installation from the built sdist into a temporary directory.
- Installed resource-path and runtime-configuration smoke checks.
- `git diff --check`.

## Validation skipped

- Automated tests under the repository's domain-only test policy.
- Ruff because it is unavailable in the current environment.
- Hosted Actions, Forgejo publication, anonymous registry installation, and
  Raspberry Pi/ePaper runtime validation.

## QA and code review

QA and code review were skipped as required by `$super-agent`.

## Documentation updates

The README explains the bundled default and external override behavior.
`AGENTS.md` identifies the canonical packaged resource directory.

## Staging and delivery status

All accepted in-scope changes are included in the delivery commit and pushed to
`origin/main` as subsequently requested by the user.

## Residual risk

The generated artifacts were validated locally, but a newly tagged package has
not been published or started on Raspberry Pi/ePaper hardware. Operator-specific
configuration directory selection remains a deployment responsibility.
