# Packaged runtime resources

Status: Approved

## Purpose

Make an installed `cluster-monitor` distribution self-contained for its
immutable runtime font and default configuration while retaining an explicit
external configuration override.

## Requested behavior

Installing the published package into a virtual environment must provide every
tracked runtime resource needed to start the ePaper renderer. Runtime resource
lookup must resolve inside the installed `cluster_monitor` package instead of
assuming a sibling `resources` directory exists under `site-packages`.

## Scope

- Package `Font.ttc` and the default `config.yml` under
  `cluster_monitor/resources`.
- Resolve immutable runtime resources from that packaged directory in source
  checkouts and installed distributions.
- Load packaged configuration first and then an external override directory.
- Preserve legacy source-checkout overrides from `./resources`.
- Allow installed deployments to select an external override directory with
  `CLUSTER_MONITOR_CONFIG_DIR`.
- Require both resources, with exact source bytes, in the sdist and both ARM
  wheels.
- Verify installed resources during post-publication package validation.

## Out of scope

- Packaging deployment-specific `config.local.yml` values or credentials.
- Changing configuration keys, renderer behavior, native Waveshare libraries,
  dependencies, release tags, or supported platforms.
- Publishing or tagging a new release.
- Adding automated tests for configuration, packaging, or presentation code,
  which the repository test policy forbids.

## Definitions

- **Packaged resources:** `cluster_monitor/resources/Font.ttc` and
  `cluster_monitor/resources/config.yml` inside the source tree and installed
  distribution.
- **External configuration directory:** the directory named by
  `CLUSTER_MONITOR_CONFIG_DIR`, or `./resources` when the environment variable
  is unset.

## Inputs and constraints

- `pyproject.toml` remains the package-data authority.
- The packaged default configuration contains no deployment credentials.
- External configuration files retain the established names `config.yaml`,
  `config.yml`, `config.local.yaml`, and `config.local.yml`.
- Packaged defaults load before external files, so external configuration has
  final precedence.
- The tracked font bytes must not change during relocation.
- Published distributions remain one sdist, one ARMv7 wheel, and one AArch64
  wheel.

## Deterministic behavior delivered

1. `RESOURCES_DIR` resolves to the `resources` directory inside the imported
   `cluster_monitor` package.
2. The ePaper renderer loads the packaged `Font.ttc` without depending on the
   current working directory or a source checkout.
3. Runtime configuration loads from the packaged default directory first.
4. Runtime configuration then loads from `CLUSTER_MONITOR_CONFIG_DIR` when set;
   otherwise it checks `./resources`, preserving the established checkout
   override location.
5. `config.local.yml` remains untracked and is never included in a release.
6. Package building fails when either packaged resource is absent, altered, or
   omitted from an artifact.
7. Post-publication verification fails when either installed resource is
   absent or differs from the release source.

## Assumptions

- Operators who start the installed package outside the source checkout set
  `CLUSTER_MONITOR_CONFIG_DIR` when deployment-specific configuration is
  required.
- The installed distribution is unpacked on disk, as standard pip wheel and
  source-distribution installations are.

## Impact

The installed ePaper renderer no longer fails with `OSError: cannot open
resource` because `Font.ttc` was omitted. Default configuration is also present
after installation, while local credentials and deployment overrides remain
external.

## Validation performed

- Compiled all changed Python modules with bytecode redirected to `/tmp`.
- Built the sdist, ARMv7 wheel, and AArch64 wheel in a temporary output
  directory.
- Verified both resources and exact bytes through the package artifact checker.
- Inspected every archive for the packaged font and default configuration.
- Installed the generated sdist without dependencies into a temporary target.
- Confirmed installed resource resolution and runtime configuration parsing.
- Ran `git diff --check`.

## Validation skipped

- Automated tests, because the changed packaging, configuration,
  infrastructure, and presentation paths are outside domain test scope.
- Ruff, because it is not installed in the current environment.
- Hosted GitHub Actions, Forgejo publication, and anonymous installation.
- Raspberry Pi/ePaper hardware startup and rendering.
- Code review and QA, as required by `$super-agent`.

## Documentation changes

`README.md` documents packaged defaults and the external configuration
directory. `AGENTS.md` records the new canonical resource path and override
contract.
