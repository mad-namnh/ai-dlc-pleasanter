# Designing a new app (new sites)

Use this when a requirement needs a site that does not exist yet. Creation itself follows ADR-0007 (skeleton bootstrap, then the normal release); this page is about what P2 must decide.

## Decide per site

| Decision | Write in the DES | Notes |
|---|---|---|
| Logical name | `equipment`, `loans` … (lower case, stable) | Used in `config/<name>/`, `${site:<name>}`, traceability, `environments.json`. Never rename later |
| Site type (`ReferenceType`) | `Issues` (期限付きテーブル) or `Results` (記録テーブル), with the reason | Choose by the record's nature: work with a period, deadline or progress → Issues; a register or master data → Results. The built-in columns of each type are taken from the **skeleton export** (probe below), not assumed |
| Title per environment | `dev_…`, `stg_…`, customer title for prod | Goes to `environments.json` `envs.<env>.sites.<name>.title` |
| Relations | child site holds a link column (`ChoicesText [[${site:parent}]]` + `Links`) | One site per entity. Totals/counts from children = Summary on the child (D16) |
| Permissions | inherit the parent folder, or own `permissions.json` with `${principal:x}` (ADR-0006) | Per role: what it can see **and press** (D19/D20) |
| Statuses | the status list with values, if the type uses Status | Model states with Status, not checkboxes (D9) |

## Slots

Every slot is free on a new site. Allocate by ADR-0002 option A (framework zone first: `ClassA…`, `NumA…`, `DateA…`, …) and record each in `design/slot-ledger.json` under the new logical name. No "confirm empty" step is needed for a site created by the release; record that the ledger starts with this design.

## Probe — G2 prerequisite when the design relies on built-in columns

Create a skeleton of each chosen type on **dev** (`pls bootstrap-plan` / runner `bootstrapSites`) and export it. The export shows the default columns, statuses and settings Pleasanter creates; P3 starts from it (`pls unpack`). If the skeleton cannot be made before G2, design with **custom slots only** and treat built-in columns (e.g. Issues' period columns) as a confirmation (step 3 rule).

## Classification

The first release of a new site changes no existing record: config-only, unless the design also changes existing sites (then classify those as usual). Note in the DES that the bootstrap (phase 1) is irreversible by the framework — a person deletes the sites to undo it (ADR-0007).

## Release order

Referenced sites first (parent before child). `pls release-plan` orders by `${site:x}` references; after phase 1 all IDs exist, so cycles are allowed.
