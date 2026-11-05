# Slice #3 — a new app end to end (equipment loans), 2026-11-05

**Goal:** prove the framework takes a **brand-new app** from a customer request to stg through P1–P6 with gates G1–G4. Project repository: `pls-demo-equipment`.

## Result

| Phase | Output | Gate |
|---|---|---|
| P1 | Request (demo mail from a fictional 総務部) → REQ-001…007, Q1–Q10 with `[assumed]` defaults | G1 approved |
| P2 | DES-001: 2 new sites (`equipment` Results, `loans` Issues), conditional Count summary for 貸出中, Issues `Overdue` view, process 返却 with display condition + access control, 1-line date check script (rung 3, reason written), own permissions per role. Probe PRB-001 run **before G2** on separate probe sites | G2 approved |
| P3 | Bootstrap on dev (ADR-0007) → skeleton export → `pls unpack` → config built → `release-plan` → applied; Pleasanter dropped 2 Issues defaults (D8) → git fixed → round trip **0 differences** | — |
| P4 | 7 API tests as 総務 + 2 role tests as 社員 (test user) **pass**; T-102 found that required columns are screen-only (D27) → AC revised by Nam; manual screen check by Nam | G3 approved |
| P5 | Bootstrap on stg → `release-plan` (permission-impacting) → applied in order equipment → loans → `mark-applied` 0 differences → smoke T-101/T-105/T-106 pass | G4 approved |
| P6 | Drift baseline on stg: 0 differences | — |

## What the framework gained

- **ADR-0007** (proposed): creating new sites = skeleton bootstrap, bind IDs, then the normal release. `pls bootstrap-plan`, `pls bind`; runner `bootstrapSites`; first release of a bootstrapped site keeps data-impacting reasons as notes (no records can exist).
- `pls classify`: process access control (`Processes[].Groups/Users/Depts`, whole-list additions too) → permission-impacting (gap from eval case 002).
- Runner: `list` (view contains/excludes), negative `create` (`expectHttp`), `spec.vars` fixtures for role tests, `$var` in expectations.
- KB 0.7: **D21** process via API needs a display condition (else 500), **D22** a column must be in the editor to work, **D23** conditional Count summary + `["\t","0"]` filter, **D24** Issues `Overdue`, **D25** date order needs `context.Error`, **D26** createsite skeleton, **D27** required columns are screen-only; schema rows for links, summaries, Issues.
- Skill P2 0.5: `references/new-sites.md` (site type, relations, slots zone A, skeleton probe as G2 prerequisite).

## Lessons

1. The skeleton-first rule paid off: P3 started from Pleasanter's own canonical form, and only 2 defaults differed after the first apply.
2. Three of seven KB entries were found by the G2-prerequisite probe, before any design was approved (skill 0.4 rule working). Two more (D8 defaults, D27) were found by P4 — the probe did not contain a required column with an API create; probes should include the negative path of every AC.
3. Role tests still need a person to switch the browser login (TD: runner session for a test user).
4. Transfer by base64 through the browser remains the most token-heavy step (runner re-injected after every page change) — ADR-0003 transport decision is the next lever.

## Left in place (for a person to delete if wanted)

Probe sites 44630/44631 (`zz_probe_PRB_*`) and test records on dev/stg sites, in spike folder 44562.
