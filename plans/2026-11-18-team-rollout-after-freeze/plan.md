# Team rollout after the feature freeze

Status: **approved by Nam, not started** (2026-11-18: "chốt plan trước chứ chưa làm"). Starts when Nam has finished the open tasks and freezes feature work.
Source: readiness review in the session of 2026-11-17/18 (criteria: stable, team runs it alone, simple, consistent output, automated).

## Nam's decisions (2026-11-18, his words in Vietnamese, summarised)

| # | Decision |
|---|---|
| N1 | Goal: real projects run by team members, not only the demo |
| N2 | Feature freeze after the open tasks |
| N3 | Approvers, option A: every dev approves G1–G3; G4 only Nam (stg release only through Nam) |
| N4 | A dev may approve the gates of their own task |
| N5 | The customer takes no part in gate approval |
| N6 | A delegation mechanism for G4 is needed (when Nam is away) |
| N7 | A G4 delegation always has an end date |
| N8 | Only Nam may delegate G4 (a delegate cannot delegate further) |
| N9 | Mail is out of scope for now (no mail sink work) |
| N10 | Several devs on one project, each in their own folder: **per-developer sandbox sites** (ADR-0011), merged into the shared sites |
| N11 | The shared project repository keeps Pleasanter config, the system spec and the machine records `pls` needs; AI working notes stay out |
| N12 | The main control for stg is the **stg write key**: only Nam (or a time-boxed delegate) holds it |
| N13 | The model is set by phase / skill, not chosen by the dev |
| N14 | Nam tests the multi-user mechanics with two accounts; then a real dev runs D8 |
| N15 | Commands that need a tenant administrator (`principals --create`, `test-users`) are run only by Nam; devs get no tenant administrator rights |
| N16 | "stg" in this plan is **MADLAB's own stg**. Deploying to a customer's stg / prod needs its own mechanism, built in later phases only when Nam asks |
| N17 | Automation group A accepted: scheduled drift check (A1), version check at session start (A2), one sandbox sync command (A3), one command for `principals --create` + `test-users` (A4) |
| N18 | Group B stays manual for now: 同期 on the サマリ tab (ADR-0028 not built), screen save after a JSON-link deploy (D40), app version from `/versions` |
| N19 | The drift check runs on the **personal machine of the person doing the task**; its purpose is to tell them the UI was edited and help decide whether to bring the UI change into git |
| N25 | Phase 9 (2026-11-19, Nam chose the recommended option of each question): phase 9 before the rest of phase 8; the job runs every 2 hours Mon–Fri 9:00–19:00; the session-start hook shows the last result and starts a background check when it is older than 2 hours; the agent never registers the job — Nam runs the install in phase 10 |
| N24 | Phase 5 (Nam: "1a, 3a", then "a"): one model per project in `.claude/settings.json`, a PreModelSwitch hook denies any other (stronger ones too); `opus` for every phase, effort default; a cheaper model per phase is decided after phase 10 from `pls usage` (ADR-0031) |
| N23 | Phase 4 (Nam: "1a 2a 3a"): first tag `v0.3.0` on the commit that ends phase 4, then `v0.3.x`; the Orchestrator tags locally, Nam pushes; uncommitted changes in the framework's shipped parts count as not pinned (refused outside dev) |
| N22 | Phase 3 (Nam: "1a 2a 3a 4a"): ADR-0011 accepted, element ids not allocated (TD-72); `pls sandbox sync` = refresh + apply, git stays with the person; a sandbox's releases and bootstraps gitignored. A4 (`principals --create --test-users`) **dropped** after review (Nam: "a"): its one confirmation could not list every change before the test-users plan exists — the two commands stay separate, each with its own listing confirmation |
| N21 | Phase 2 correction of N11 (Nam: "chon a"): `tests/results/` and `requirements/sources/` stay in git (pls coverage and pls check p1 read them on the approver's machine), and so do `ops/log/`, `ops/usage/`, `design/probes/` (audit, design evidence); only `ops/xref/`, `ops/adopt/`, `ops/triage/`, `ops/env-compare/` are gitignored |
| N20 | A dev's machine checks the dev sites only (shared + own sandbox); stg drift runs with the same job on Nam's machine (stg key, N12). Devs get no stg key, not even read-only |

## Findings this plan answers (verified)

- `pls profile set` accepts **any** approver of the profile, whatever gate they approve (`tools/pls/pls_profile_records.py:177-184`): under N3 a G1–G3 dev can give themselves G4 or change an environment `role`.
- The drift baseline is the last applied release in the folder's own `releases/` (`tools/pls/pls.py:1159`, `:1274`): two folders writing the same dev sites see each other's work as drift, and `updatesite` replaces SiteSettings entirely (KB D4). Hence N10.
- The Approvers row is per gate, not per environment (`tools/pls/pls_gate.py:41`).

## Phases

| # | Phase | Tier | Status |
|---|---|---|---|
| 1 | Gate model and stg control for a team | Critical | proposed |
| 2 | Shared project repository: what is kept, what is ignored | Standard | proposed |
| 3 | Per-developer sandboxes (ADR-0011) made the default way of working | Critical | proposed |
| 4 | Version pinning, hotfix flow, changelog | Critical | proposed |
| 5 | Model per phase / skill | Standard | proposed |
| 6 | CI for both suites | Standard | proposed |
| 7 | `pls status` (next step) + golden path + docs clean-up (D6) | Standard | proposed |
| 8 | Evals of the skills in use (k = 3 for P1, P2, lifecycle) | Standard | done (2026-11-19): every planned run made; FAILs open (see HANDOFF) |
| 9 | Scheduled drift check on the task owner's machine (A1) | Standard | done (2026-11-19) |
| 10 | Trial: Nam with two accounts, then one real dev (D8) | — | proposed |

### 1. Gate model and stg control
- Changing `Approvers` and any environment `role` needs a G4 approver **without an end date** (= Nam, N8). Tests: a G1–G3 approver refused; a time-boxed G4 delegate refused; shown failing on the parent commit.
- Delegation (N6–N8): `pls profile set Approvers` by Nam with a required end date, e.g. `G1–G3: A, B, C; G4: Nam; G4 until 2026-12-05: B`; `pls` ignores the segment after the date; no end date → refused; early revoke by a new `profile set`.
- Trace first: what `profile set role` by a non-G4 approver can weaken today (`assert_writable`, G4 check).
- N12: the stg key lives only in Nam's (or the delegate's) `.pls/`; devs' `connections.json` has no stg write key. Written down in setup docs and the golden path; `http-check` on a dev machine shows `stg: writes refused`.
- Gate records on the shared remote, protected branch (TD-17 brought forward).
- ADR-0020 updated with N3–N8, N12 and self-approval (N4); Nam accepts it.
- Patch (protected path) `templates/project/CLAUDE.md`: stage `project` without customer approval (N5), Approvers example per N3; Operators row: stg apply = Nam / delegate.

### 2. Shared project repository (N11)
- Ignored by the template `.gitignore` (N21): `ops/xref/`, `ops/adopt/` (regenerated by `pls xref` / `pls adopt`), `ops/triage/`, `ops/env-compare/`. Everything else stays, `tests/results/`, `requirements/sources/`, `ops/log/`, `ops/usage/`, `design/probes/` included.
- Check that no `pls` command or lint needs an ignored path to be in git (e.g. traceability, coverage, L-LAD-01); adjust or keep the path.
- Architecture §3.2 and the template layout table updated.

### 3. Per-developer sandboxes (N10)
- ADR-0011 decided (Nam). Golden path: `sandbox create` → work → `harvest` → merge to the shared branch → release to the shared dev sites by one person at a time.
- The slot ledger and drift baseline of the shared sites live only in the shared repository.
- A3: one command (`pls sandbox sync`) for refresh → harvest → merge, stopping at the first refusal.
- ~~A4: one command for Nam after G2 that runs `principals --create` then `test-users` under one typed confirmation (N15).~~ Dropped (N22): the two commands stay separate.
- Covered by the two-account trial (phase 10) before a real dev uses it.

### 4. Version pinning, hotfix, changelog
- Git tags (`v0.3.0` …); `framework.lock` records the commit; `pls` warns on a differing checkout, refuses writes to stg.
- During the freeze: bug report → `fix/` branch → tag `v0.3.x` → changelog entry → `pls skills sync` + lock update in each project (one documented command).
- A2: a session-start hook (next to the existing `pls hook` entries) warns when the project's lock differs from the latest framework tag.
- The upgrade command also reports how the project `CLAUDE.md` differs from the template of the pinned version (today it is copied once at `init` and never synced, ADR-0022), so projects started at different versions do not keep different rules silently.

### 5. Model per phase / skill (N13)
- First check the official Claude Code documentation: does skill frontmatter `model` exist and apply to the main session? Otherwise phases run as subagents whose definition sets `model` (do not guess — CLAUDE.md rule 5 applies to the tooling too).
- Evals run on the model the phase sets.

### 6. CI
- GitHub Actions: `python -m unittest discover -s tools/pls/tests` (3.10 + 3.12), `node --test tools/pls/tests/test_runner.mjs`, `pls_impact_rules.py` freshness.

### 7. `pls status`, golden path, docs
- `pls status`: reads the project (profile, REQ / DES front matter, gates, releases, sandbox) and prints the phase, the missing gate and the next command. Read-only.
- One page golden path: onboarding (`--origin existing`) → change request in a sandbox → release dev → release stg (Nam / delegate). Notes the ADR-0010 refusal for sites with notifications (N9).
- Dev onboarding checklist: Pleasanter account and dev API key (not a tenant administrator), sandbox folder, `pls setup`, `http-check`; `principals --create` and `test-users` are asked of Nam (N15) — the golden path says when (after G2).
- The manual steps that stay manual, listed in the golden path with the command that records them: screen save after deploying a JSON link (KB D40, TD-50), 同期 on the サマリ tab after a summary change (ADR-0028), app version from `/versions`.
- README status current; `HANDOFF.md` = current state + next step, history moved to `plans/`.

### 8. Evals
- k = 3: P1 0.8, P2 0.13, lifecycle 0.29 (no result on their current version, TD-37).
- k = 1 at least, current version: onboarding (the entry of every real project — existing apps), P3 config-builder, P3 script-engineer (last result FAIL, 2026-11-13), P5; P6 after its rubric / input mismatch is fixed.
- Run on the model phase 5 sets. Batch asked of Nam first.

### 9. Scheduled drift check (A1, N19)
- Scope per machine (N20): a dev — the project's shared dev sites and their own sandbox; Nam — additionally stg.
- Runs on the task owner's machine with their own key (Windows Task Scheduler; the setup is one `pls` command that registers and removes the job). Read only: export + drift of the project's sites; also run once at session start.
- Baseline must be current: the job runs `git fetch` and refuses to report while the folder is behind the shared branch's `releases/` (otherwise another dev's release looks like a UI edit).
- Result kept local (gitignored, `.pls/`): no commits from the job. Shown by the session-start hook (A2) and a Windows notification when something changed.
- The report answers the decision: what changed, `classify` of each change (config-only / data-impacting / permission), and the two ways on — take the UI change into git as a change request (unpack / harvest, then the normal gates) or revert it in the next release. Only the person's decision is recorded in `ops/drift/`.
- Tests on the fake server: behind-the-remote refusal, no write call, report shape.

### 10. Trial (N14)
- Nam, two accounts, one project: G1–G3 by account B, G4 refused for B, delegation with an end date, two sandboxes, harvest + merge, stg key only on account A.
- Then one dev who did not build the framework runs a small real change from the golden path. Measured: questions to Nam, time per phase, refusals. Friction → fixes or tech debt.

## Before phase 1 (part of "finish the open tasks")
- Working tree clean and both suites green on the freeze commit (on 2026-11-18 `test_impact_rules` failed on uncommitted KB edits: regenerate `impact-rules.md`).

## Definition of done — against Nam's five criteria

| Criterion | Done when | Phases |
|---|---|---|
| Stable enough to use | CI green on the tag; projects pinned; stg writes refused on a differing checkout; no open hole in the gate model | 1, 4, 6 |
| Team runs the repo alone | Phase 10 dev reaches a dev release with **≤ 3 questions to Nam** that the golden path does not answer, and none about the tool's internals | 2, 3, 7, 10 |
| Simple to operate | The golden path covers the trial without a second document; `pls status` names the next command at every stop of the trial | 7, 10 |
| Consistent output | Every skill used on the golden path has a PASS on its current version and the model its phase sets; projects report template drift | 4, 5, 8 |
| Highly automated | A UI edit on a project site is reported to the task owner without them asking; every remaining manual step (N18) is listed with its recording command; no step of the trial was done by hand that the list does not name | 4, 6, 7, 9, 10 |

## Not in this plan (tracked)
Customer stg / prod deployment (N16: own mechanism, later, on Nam's request) with TD-02, TD-16, TD-18, TD-20, TD-27; ADR-0014 decided; mail (N9, TD-10); scheduled daily drift; `pls.py` split (TD-32 — only Nam changes `pls` during the freeze); 8 KB entries not verified on 1.5.2.0 (D38, D40, D41a, D46, D48–D51).

## Open questions for Nam
None for the plan. Asked at phase time: ADR-0020 and ADR-0011 wording; the template patch (protected path); the eval batch (phase 8).
