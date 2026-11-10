# ADR-0007: Creating new sites (first release of a new app)

- **Status:** Proposed — to be confirmed by the probe on dev and the equipment-loan demo (2026-11-05)
- **Date:** 2026-11-05
- **Related:** review-findings A3, D3, D6; ADR-0001, ADR-0002, ADR-0003

## Context

Until now every release updated sites that already existed (`updatesite`). A new app needs its sites to be created first, in every environment. Two problems:

1. **IDs do not exist yet.** Configuration refers to other sites (`Links`, `ChoicesText [[id]]`, `Summaries`, script bodies) through `${site:x}`, which `pls pack` resolves from `environments.json`. A site that has not been created has no ID, so a payload for a set of new sites that reference each other cannot be built.
2. **Creation is not reversible by the framework.** Undoing a created site means deleting it. Agents never delete (prohibited action), and a deleted site with data is lost.

## Options

### Option A — `createsite` with the complete configuration, one site at a time
- Cons: a site that references a sibling created later cannot be built (problem 1); cycles (parent ↔ child links) are impossible.

### Option B — Site package (`copysitepackage`) from the previous environment
- Pros: remaps structured references (D6).
- Cons: needs a source site, so it cannot create the first environment (dev); does not remap script bodies (D3); copies whatever is live in the source, not the reviewed git state (violates I1); behaviour with data/permissions to be probed.

### Option C — Two phases: empty skeleton, then the normal release
1. **Bootstrap:** `pls bootstrap-plan --env E --release R` lists every managed site without an ID in `E` and writes `releases/R/bootstrap.json` (`createsite` under the environment's `parent_id` folder with `Title`, `ReferenceType` from `config/<site>/meta.json`, `Body ""`, `SiteSettings {}`). The browser runner `bootstrapSites(plan)` creates them and returns the new IDs; `pls bind --env E --release R --created site=ID …` records them in `environments.json`.
2. **Release:** the usual `release-plan` with the skeleton exports — complete payload, dependency order, snapshot, reverse-order rollback to the skeleton. All `${site:x}` references resolve, including cycles and scripts.
- Pros: one code path for configuration (the reviewed git state, I1); every check of a normal release applies; rollback of phase 2 is the existing mechanism.
- Cons: two runner calls; an empty site exists briefly (harmless: no records, inherits the parent folder's permissions).

## Decision

**Option C.**

- Phase 1 is refused for `role: prod` (production sites are created by the customer-side runner, ADR-0003, using the same `bootstrap.json`).
- `bind` refuses IDs already used in any environment.
- **Undo of phase 1 is manual:** a person deletes the created sites in Pleasanter, then their IDs are removed from `environments.json`. Nothing in the framework deletes a site.
- **Building the first configuration (P3):** create the dev skeleton first, export it and `pls unpack` it, so `config/<site>/` starts from Pleasanter's own canonical form (D8); then add the design's elements. A hand-written `site.json` from scratch is not used.
- **Column slots on a new site:** ADR-0002 option A (ranges per zone) — every slot is free, so the ledger starts with the design's allocation only.
- **Permissions:** a new site inherits the parent folder at creation. If the design needs its own permissions, `permissions.json` is part of phase 2 (ADR-0006).

## Open points (probe on dev before the first use)

- `createsite` with `SiteSettings {}`: accepted? Response shape (`Id`)? Default SiteSettings created by Pleasanter (to be unpacked)?
- Does the skeleton inherit the parent folder's permissions (`InheritPermission` = parent)?

## A site is never created twice (2026-11-10, design review WS4-F7 / C10)

- `pls bootstrap` sends each `createsite` once. Sites answered with an id are bound at once, also when a later step fails. Before each request the site is written to `bootstrap.json` as `uncertain` and cleared when the request is answered; so an unanswered request (timeout) and a run that dies between the server creating the site and pls binding its id leave the same record. While it is there, a re-run is refused until a person looks at the folder and either binds the site (`pls bind --created <site>=<id>`) or confirms it is absent (`pls bootstrap <R> --absent <site>`).
- **Open question (not built, not assumed):** the design review asked for an automatic look-up "by title under the parent folder" before a re-create. Whether the 1.5.x API can list the child sites of a folder (and with which call and rights) is not verified in the KB, and titles are not unique in Pleasanter. Until a probe on dev shows it, the check stays with the person as above. Probe to add to `pls kb-verify`: create two sites under the probe folder, then try to read the folder's children through the API.

## Consequences

- `environments.json`: per environment `parent_id` (folder for new sites); a site entry may have a `title` and no `id` until it is bound.
- `pls` 0.4: `bootstrap-plan`, `bind`; unresolved references to unbound sites fail with a clear message.
- P2 decides site types (`ReferenceType`), links between the new sites and the slot allocation; P3 starts from the skeleton export.
