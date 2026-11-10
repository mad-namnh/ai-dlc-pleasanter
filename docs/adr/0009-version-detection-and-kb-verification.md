# ADR-0009: Pleasanter version detection and executable KB verification

- **Status:** Proposed (2026-11-05) — part 1 (version label, BR2) and part 2 (`kb-verify`, BR8) implemented on branch `brownfield-adr`
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

- [x] Does Pleasanter 1.5.x expose the application version over the API, or only on a page? — **Probed 2026-11-05 (1.5.2):** not in API responses; `/api/versions` 404; the page `/versions` needs a logged-in session; the login page shows a build token (`style.min.css?v=201520`) whose mapping to a version is unknown. KB `api.md` "Version".
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

### Implementation notes (BR2, 2026-11-05)

- The probe changed point 1 of the decision: no source readable with an API key gives the application version. `pls version --env <e>` therefore **detects** the build token (login page, no credentials) and the settings schema (`SiteSettings.Version` of a managed site), and stores the **application version recorded by a person** from `/versions` (`--app`). The label is kept only while the build token was **read and is unchanged** and the schema is unchanged; otherwise it is reset to `unknown`, so a stale label cannot survive an upgrade (also when the token disappears from the page, e.g. behind a proxy or SSO). Exit code 1 while the label is unknown, the token is missing or the schema could not be read. The schema is read from the first site the key can read (then `parent_id`).
- `http-check` shows the recorded version, warns when the build token changed, and says *build NOT verified* when the page is unreachable or has no token (5 s timeout, only when a version is recorded; informational, never fails the check).
- `release-plan` writes `version_check` (target vs `dev`, where releases are tested) into `plan.json` and prints `VERSION …` lines; never a refusal (the person decides at G4).
- Point 5 built 2026-11-10 (design review F3): `release-plan` (in `plan.version_check`, printed as `VERSION` lines and in the operator report shown at G4) and `pls version` compare the application version recorded for the tested environment and for the target with `verified_on` in the KB `references/probes/index.json`, and name every entry not verified on that version. A KB label covers a version with the same leading numbers (`1.5.2` covers `1.5.2` and `1.5.2.0`, not `1.5.20` or `1.6.0`). So a dev that was upgraded and whose new label a person recorded no longer reads as tested. It is information for G4, not a refusal. Limit: the list is every KB entry not verified there, not only the entries this release relies on (pls does not know which ones a release relies on).
- Not built: a reader of `/versions` through the browser runner (session) — possible later if typing the label proves error-prone. Points 2–6 (KB `verified_on`, `kb-verify`, canonical defaults per schema) are plan BR8.
- `tools/pls/pls_version.py`, 10 tests in `tests/test_version.py`. An independent code review found eight gaps (stale label kept when the token is missing — high; schema change not resetting the label; http-check silent when nothing was verified; exceptions other than `OSError`; …); all fixed and tested. First real run on MADLAB dev: build `201520`, schema `1.017`, app label pending.
- Open: does `SiteSettings.Version` differ between sites of one installation (lazy migration)? If so, the reported schema depends on which site is read first — probe after the next upgrade.

### Implementation notes (BR8, 2026-11-08)

- Probes: `skills/pls-kb-pleasanter/references/probes/<entry>-<topic>.json` — the probe site's configuration, the expected HTTP of the save, expected stored settings (`null` = dropped, D8), and test steps in the `pls test` format. First set: D8, D10, D21, D24, D27, D28, D30 (a pair: with and without `View`, so an unrelated refusal cannot pass as D30). Probes never contain notifications or reminders (refused on load).
- `verified_on` lives in `references/probes/index.json` per entry instead of a column in `behaviours.md` (one place for the tool and the skills to read).
- `pls kb-verify --env <dev env> [--yes]`: dev only, never a sandbox; probe sites under `values.kb_probe_parent` (a folder the person creates and records); one site per probe, created once and reused (`.pls/kb-probes-<env>.json`); writes `ops/kb-verify/<date>-<env>.md/.json` with pass/fail per probe for the environment's recorded version, and the entries that have no probe. Updating `index.json` from a report is a framework change (I9), done by a person or with their review.
- Safety after code review: a probe site is reused only when getsite shows it is provably the probe's own (folder, title `zz_kbprobe_<name>`, type, not an app site) and the state file names the same server and folder — otherwise nothing is written; the probe folder must be a folder of its own (not 0, not the app's folder or sites); probes are confined to their own site and records (no `site`, `run_on`, `as_key`, `vars`; ops create/get/list/exec) and refused when they contain notifications at any depth or server scripts; the admin principal must be `User,<id>`; each probe failure is recorded per probe (`error` → exit 2). Probe validity: positive controls in D8 and D27, D10 runs from any status so only the display condition refuses, D21 has a control process with a condition, D24 uses the server's date and closes its records, D30's 500 probe is `inconclusive` when its control fails; an entry passes only when all its probes pass; `Version` and `ReferenceType` are sent inside SiteSettings as in releases.
- Not covered by probes yet: entries that need a second user or role key (D19, D20), several sites (D16, D23), data migration (D13, D14, D18), scripts (D7, D25), packages (D3, D6) — they keep their written evidence.
- Not built: `canonical-defaults.json` keyed by schema version (point 6) — needed when two schema versions are in use.

## Consequences

- Easier: upgrades become visible; behaviour changes are found on dev before a release instead of in production; the KB states where each fact was seen.
- Harder / costs: one probe spec per KB entry (D1–D28 today); a probe folder on each dev used for verification; stg/prod remain label-checked only.
- Follow-up: probe the version source; write probe specs for the entries the current skills depend on first (D8, D10, D19–D24, D27, D28); add `verified_on` to `behaviours.md`; lint rule for KB entries without a probe.
