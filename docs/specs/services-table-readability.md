# Services table readability and image release versions

Status: Approved
Date: 2026-11-18

## Purpose and authority

Improve the existing Docker Swarm services table on the 2.7-inch ePaper display.
The user invoked spec-plan, requested readable deployed versions and replica
counts, required published ports to remain visible, preferred the structured table,
confirmed that the image release version is sufficient, and subsequently directed
“let's drop the nodes”. The latest instruction removes node placement from this
services view. The user subsequently requested removing Ports in favor of Docker
health-check results, then questioned the usefulness of that extra health column.
The resulting proposal removes both Ports and Health and focuses on Name, Ver, R;
this complete revision remains subject to specification approval.
This is a planning-only proposal; specification approval does not authorize source
implementation or deployment.

Research baseline: main at 7ea5e1b7e02f58ffb5572333350d744e3efe8f33.
No earlier SPEC/PLAN files were present. Maintained existing behavior is documented
in README.md under Runtime behavior and operational limits. Preserve that behavior
except for the explicit display changes below.

## Scope and exclusions

Retain page 2 as a three-column table: Name, Ver, R. Remove the Nodes and
Ports columns from this view; retain placement and port data in the underlying
model. Do not add a Health column or new health collection. Improve cell
allocation and fitting, and replace the displayed image tag with a compact image
release version. Preserve five services per view and the existing button bindings.

No cards, secondary version view, new buttons, configuration knobs, service aliases,
health dashboard, task-state breakdown, Docker polling changes, workload changes,
release publishing, or deployment. Sorting, scroll-end handling, and existing
collection failure/staleness behavior are unchanged. No new application-health
claims or alert markers are introduced.

## Definitions and evidence

- The landscape drawing surface is 264 by 176 pixels. Current table font size is
  10 pixels, with five equal-width columns inside 5-pixel horizontal margins.
- Name identifies the Swarm service, retaining the existing stack-prefix removal
  convention. It must not be replaced by the image repository name.
- Ver is the image release from the configured Swarm service image reference,
  not a verified application/package version or proof of a completed rollout.
  During a rollout, running tasks may temporarily use other images; collecting
  or displaying mixed task versions is outside this change.
- Node placement is no longer displayed on this view. Collection and underlying
  node placement data remain unchanged.
- Ports are no longer displayed on this view. Preserve the underlying published
  port data and its existing use by other screens and consumers.
- R retains running/desired replicas, including `0/0` and global `running/-`.
  These are Swarm tasks/replicas, not Kubernetes pods or application health.
- Source references: cluster_monitor/application/services/cluster_monitor_service.py
  (draw_docker_stats_page_2), domain/entities/docker_status_entity.py,
  presentation/renderers/epapers/epaper_renderer.py (draw_table), and
  presentation/controllers/epaper_controller.py (page-2 scrolling).
- Read-only live observation on 2026-11-18: manager p0, 15 services and 20 running
  tasks. Running task images matched configured service images at observation.
  This is research evidence, not implementation or hardware validation.

## Required behavior

### Image release extraction

1. Remove any digest suffix before finding the tag. Resolve the tag only from
   the final image path component so registry ports are never treated as tags.
2. Recognize a leading numeric release with two or more dot-separated numeric
   components, optionally preceded by `v`. Display the numeric release without
   the leading `v`.
3. Preserve an immediately following lowercase prerelease suffix of the form
   `-alphaN`, `-betaN`, or `-rcN`, where N is one or more decimal digits. Strip
   subsequent platform, dependency, and build suffixes. Match complete suffix
   tokens (terminated by the end of the tag or a hyphen), not partial words.
4. Other suffixes, including dependency version segments, are omitted. A tag
   without a recognized leading numeric release displays `-`; never infer a
   version from `latest`, a digest, or an embedded unrelated number.
5. Preserve the full image reference and existing raw-tag access for consumers
   that need them. Version shortening is a display concern, not data loss.

| Image tag | Ver |
| --- | --- |
| 1.0.3-7.1.3-8.5.12-fpm-alpine3.24 | 1.0.3 |
| 1.0.2-11.7 | 1.0.2 |
| 16.0.1-rootless | 16.0.1 |
| 2.9 | 2.9 |
| 1.0.1-node24-alpine | 1.0.1 |
| 2.45.3-alpine | 2.45.3 |
| 2.0.0-beta5-node24-alpine | 2.0.0-beta5 |
| v1.2.3-rc1-alpine | 1.2.3-rc1 |
| latest / missing tag / digest only | - |

### Structured rendering

- Keep all three columns on the same view. Keep the existing title, service count,
  service order, five-row scrolling step, and other pages' behavior.
- Use fixed column widths of Name 168, Ver 56, and R 30 pixels within the
  existing 5-pixel side margins. These widths and column boundaries remain
  identical across rows, scroll batches, and refreshes, regardless of content.
  Do not auto-size or redistribute columns based on visible values. Give service
  names more space than the replica column. Keep numeric
  versions and replica counts readable at the existing font
  size; shrinking the font to hide overflow is not the solution.
- Fit display strings using the actual font's measured pixel width and cell
  padding. Replace fixed nine-character name and ten-character display-tag cuts
  on this view. Do not truncate the source values before measuring.
- Text must stay inside its cell and the 264-by-176 surface. Long names or unusually long versions use a visible ellipsis when
  shortened; never silently draw across a neighboring column.
- Normal replica strings and the researched release versions, including
  `2.0.0-beta5`, fit without truncation. Reserve numeric-column space explicitly.
- Keep table headers and all five rows within the display. Use the fixed widths
  specified above and verify them with measured rendering and a preview.
  Table vertical padding may be reduced while retaining the existing font size.
  Research measurement with the bundled 10-pixel font found a feasible width
  allocation for the earlier four-column proposal of Name 106, Ver 56, Ports 62,
  R 30 pixels, including 2 pixels of padding on each cell side. Removing Ports
  makes 62 additional pixels available, primarily for names. A feasible
  three-column allocation is Name 168, Ver 56, R 30 pixels, totaling
  the available 254 pixels. This is the fixed layout selected for the proposal;
  regenerate the preview for this final layout. With the
  surrounding header retained, 3-pixel table vertical padding places the bottom
  of five rows at y=156; current 5-pixel padding would place it at y=180 and is
  therefore unsuitable for the 176-pixel surface. A manual Pillow preview
  demonstrated the former geometry; physical-panel legibility is unverified.
- Console output remains structured and uses the same compact release value
  for this services table, without ePaper-specific character limits. Other
  tables retain their existing rendering behavior.

## Regression boundaries

Preserve published-port semantics and existing port omission behavior, namespace
handling, replica meanings (including global `running/-`), service ordering, and
button assignments. Do not alter Docker task collection, lifecycle, caching,
hardware initialization, page refresh synchronization, or GPIO configuration.
Do not change prior approved artifacts or add automated tests outside domain logic.

## Acceptance and validation

1. Deterministic domain coverage verifies release extraction for the examples
   above, registry ports, tagged images with digests, missing tags, prereleases,
   and multi-version tags. Tests may be added only for domain source logic.
2. Static/lint/syntax checks cover changed source. No automated renderer,
   orchestration, configuration, or hardware tests are created or maintained.
3. A hardware-independent, pixel-accurate rendered preview uses the bundled font
   and actual landscape dimensions. Inspect five populated rows, long names,
   `2.0.0-beta5`, replica counts,
   empty data, and a final partial batch. Verify cell boundaries and no overflow.
   This is a manual visual/smoke check, not a new automated test suite.
4. Existing domain checks remain passing. Other screens and console service
   output receive appropriate static or manual smoke checks.
5. Physical display legibility and button navigation remain operator acceptance
   checks on the target panel; a local preview does not prove hardware behavior.
   No deployment or remote mutation is authorized by this specification.

## Documentation and approval

Update README.md with compact image-release semantics, prerelease retention,
unknown-version display, removal of the Nodes and Ports columns from the services table,
and pixel-fitting/abbreviation behavior. At completed
delivery, consolidate durable behavior into maintained documentation and remove
this SPEC with its matching PLAN together under repository policy.

Approval: Explicit user approval on 2026-11-18: “approve, make sure cleanup is done”.
Approved revision: three-column Name / Ver / R table with fixed widths
168 / 56 / 30 pixels and the complete behavior and acceptance criteria above.
Subsequent clarification: “cleanup of unused code, remove code debt”; the PLAN
will address obsolete code within the changed services-display path without
expanding the approved behavior or removing data needed by other consumers.
