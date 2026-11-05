# ADR-0009: Pleasanter version detection and executable KB verification

- **Status:** Proposed (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** Nam
- **Related:** I5, I9; KB `pls-kb-pleasanter` (every entry says "1.5.2"); D8 (canonicalisation); ADR-0001; plan Step 4c

## Context

Every entry of the knowledge base was observed on **one** environment, MADLAB dev, Pleasanter 1.5.2. The skills trust those entries when they design (P2), build (P3) and test (P4).

The first brownfield candidate (a complex customer project in 運用保守) has three environments (dev, stg, prod). They may run different Pleasanter versions, and the customer can upgrade any of them without telling us. Today:
- `pls` never reads the Pleasanter version of an environment;
- the only version-like value it sees is `SiteSettings.Version` in an export (e.g. `1.017`). That is the version of the settings schema, not of the application;
- `pls canon` uses one list of canonical defaults (D8). Defaults that differ between versions would show up as false drift;
- a release planned for stg or prod is checked against dev behaviour only.

A version difference can silently break a design that relies on a KB entry (e.g. D10 display conditions enforced by the API, D21 a process needs a display condition, D23 summary behaviour).

## Open questions

- [ ] Does Pleasanter 1.5.x expose the application version over the API, or only on a page (login page, footer, "about")? — *probe on dev*; record the answer in KB `api.md`.
- [ ] Which versions do the customer's dev, stg and prod run today? — answered by the tool once it exists.
- [ ] Does `SiteSettings.Version` change together with the application version, or only with schema changes? — *probe after the next dev upgrade*.
- [ ] Can the customer's dev hold a probe folder for `kb-verify` (write access, `allow_write`)? — *customer / project lead*.

## Options

### Option A — Version recorded by hand in `environments.json`
- Pros: no code.
- Cons: goes stale after every upgrade; nobody notices; says nothing about behaviour.

### Option B — Automatic version label only (`pls version`)
- Pros: cheap; warns when an environment is upgraded.
- Cons: a label does not say which KB entries still hold; a patch release can change behaviour without a visible schema change.

### Option C — Version label **plus** executable verification of the KB
- Pros: checks what the designs actually rely on, on the version that is really installed; turns "which version?" into "which entries still hold?"; a failing probe is a KB correction (I9).
- Cons: every KB entry needs a probe spec; probes write to a probe folder on dev; stg and prod cannot be probed (no writes), so they are covered by label comparison only.

## Decision

**Option C (proposed).**

1. **`pls version --env <e>`** reads the application version (source chosen by the open-question probe; fallback order: API, then page) and the schema version from an export. It stores `envs.<e>.pleasanter = {"app": "...", "schema": 1.017, "checked": "<date>"}` in `environments.json`. `http-check` and `export` re-read it and warn when it changed since the stored value.
2. **KB entries carry `verified_on`** (list of application versions) and a **probe spec** in the same format as `tests/api/*.json`, stored next to the KB (`references/probes/D<nn>.json`).
3. **`pls kb-verify --env dev`** runs every probe on a dedicated probe folder of a dev environment (`envs.<e>.values.probe_parent_id`) and updates `verified_on`. A failing probe marks the entry **unverified for that version**; the KB entry is corrected or split by version (I9).
4. **Skills** (P2, P3, P4) treat an entry not verified on the target version as an assumption: design the branch that is safe if it is wrong, or carry it as an open point (existing P2 rule).
5. **`release-plan`** compares the target's version label with the dev version the release was tested on. If they differ, it lists the KB entries the release relies on that are not verified on the target version; the P5 diff report must show that list at G4.
6. **Canonical defaults** (`canonical-defaults.json`) are keyed by schema version, so `canon` and drift do not report false differences across versions.

## Consequences

- Easier: upgrades become visible; behaviour changes are found on dev before a release instead of in production; the KB states where each fact was seen.
- Harder / costs: one probe spec per KB entry (D1–D28 today); a probe folder on each dev used for verification; stg/prod remain label-checked only.
- Follow-up: probe the version source; write probe specs for the entries the current skills depend on first (D8, D10, D19–D24, D27, D28); add `verified_on` to `behaviours.md`; lint rule for KB entries without a probe.
