# ai-dlc-pleasanter roadmap

Principle: **validate the biggest assumption first, then build in thin vertical slices** (see review C2), not in horizontal layers.

The frame every step serves is `docs/architecture.md` (phases P1–P6, gates G1–G4). Work that does not map to a phase there is out of scope or goes to `patterns/`.

## Step 1 — Round-trip spike (1–2 weeks) — round 1 done

Question: does Pleasanter 1.5.x configuration survive export → re-import → identical to the original? Which parts must be done manually?

- Procedure: `spike/round-trip/README.md`
- Output: report based on `spike/round-trip/report-template.md` + a **Go / Change direction / No-go** decision
- Round 1 (2026-11-05): **conditional Go** — see `spike/round-trip/report-20261105.md`. Round 2 must cover the remaining 7 core components.

## Step 2 — Decide 5 ADRs (≈1 week)

| ADR | Topic | Depends on |
|---|---|---|
| 0001 | Scope of configuration managed in git | Spike results |
| 0002 | Column-slot ranges per ownership zone | 0001, agreement with customer (deferred: TD-01) |
| 0003 | Production deployment method | Customer IT (deferred: TD-02) |
| 0004 | Data-impacting changes & dedicated gate | 0001 |
| 0005 | Configuration storage & secrets policy | Runtime part accepted; storage part deferred (TD-03) |

## Step 3 — Vertical slice #1 through P1–P6 — DONE (2026-11-05, `docs/slices/slice-01-report.md`)

One small, real requirement, carried through **all six phases** at the minimum level, on a spike copy site:

| Phase | Minimum for slice #1 |
|---|---|
| P1 Requirements | 1–3 EARS requirements written by AI from a short request; human approves (G1) |
| P2 Design | AI maps them to columns/views/プロセス with ladder reasons; slot ledger entries; classification (G2) |
| P3 Build | `pls export` + `unpack`; AI edits `config/`; `pack`; deploy to dev |
| P4 Verify | Lint rules L-SEC-01, L-REF-01, L-SCR-01; 1 API test per requirement; coverage check (G3) |
| P5 Release | `pls drift` + `pls diff` + business-language report; deploy to a second copy site as "stg" (G4) |
| P6 Operate | Make one manual UI change on the "stg" copy; detect it as drift and resolve it |

Done when: the whole chain runs from a project-repo skeleton, each gate has a record, and gaps found are written back into `docs/architecture.md`.

Spike round 2 (remaining 7 core components) runs in parallel with P3 of the slice.

## Step 4 — Thicken each stage — items 1–4 done; proven in slice #2 (`docs/slices/slice-02-report.md`)

Priority after slice #1:

0. ✅ Close slice gaps S1–S3 in `pls` (v0.2: canon, drift vs last release, plan blocks on drift, mark-applied)
0. ✅ Extract skills `pls-p1-requirements-analyst` and `pls-p2-solution-designer` (+ knowledge base `pls-kb-pleasanter`, S7)
0. ✅ Run eval case 001 for both skills with a fresh agent; fix the skills until they pass (skills v0.2, `evals/results/*/2026-11-05.md`; found escaped defect: duplicate mail to [Manager] on escalation)
0. ⏸ Mail sink for notification tests (S5) — deferred: mail not needed at this stage (TD-10)

Then:

1. ✅ Drift check + column-slot conflict check before deploy (A2, D4 — mandatory) — `pls plan` refuses on drift (v0.2) and on slot findings (v0.3, L-SLOT-02, `pls slots`)
2. ✅ Deploy plan: dependency ordering, snapshot, configuration rollback (A3) — `pls release-plan` + runner `applyRelease` (v0.3); open: automatic smoke-then-restore, creating new sites
3. ✅ Data migration (A1) — ADR-0004 accepted after probes D12–D14; migration gate in `pls plan` / `release-plan`; runner `backupRecords` / `bulkUpsert`. Open: first real migration (volume, dry run on a data copy)
4. ✅ Permission matrix (C3) — site permissions in git, opt-in (ADR-0006, D15), drift + permission-impacting classification, L-PERM-01. Open: effective-access tests per role (TD-11)
5. First skills/agents, only for what the pilot needs — next: skills v0.3 from slice #2 findings (S2-1, S2-4)
6. Slice #2 ✅ (2026-11-05): multi-site release, migrations M1/M2, permissions + process ACL across environments; R-20261105-05 on stg

## Step 4b — Demo readiness ← NEXT (review: `docs/reviews/demo-readiness.md`)

**Goal:** another person clones the framework, creates a project from a natural-language spec and sets one connection config. The agent then carries the app through the lifecycle to **dev**, with a human approving at the gates. The run must use few tokens.

**Definition of done:** a **demo dry run** passes. The runner is someone who did not build the framework, working with Claude Code on a machine that can reach Pleasanter. They go from a clean clone to a **dev release** with round trip 0 and tests passing, using only:
- the repositories;
- `docs/setup.md`;
- the spec.

Measure tokens and wall time per phase, and record them in `demo/results/`.

### Work items (in order)

| # | Item | Deliverables | Acceptance |
|---|---|---|---|
| D1 ✅ | **Lifecycle runbook** — done 2026-11-05: `skills/pls-x-lifecycle` 0.1 + `templates/project/CLAUDE.md`; lifecycle case 001 pass (review R2-1, R2-2, R3-5) | `templates/project/CLAUDE.md`.<br>Skill `pls-x-lifecycle`: phase order P1→P6, gate stops (the agent stops and asks; it never approves), where gate decisions are written, the exact `pls` command per step, error handling (refused plan, failed apply → automatic restore), and token rules (read `pls` summaries, never whole payload, rollback or export files; no base64 when HTTP works). | A fresh agent given only the project and a spec reaches G1 and stops correctly. After "approve G1" it continues to G2, and so on. |
| D2 ✅ | **Skills P3–P5** — done 2026-11-05: `pls-p3-config-builder`, `pls-p4-test-writer`, `pls-p5-release-manager` 0.1; P3/P4 case 001 pass (P5 → D7); tool gaps TD-14 (R2-1, R2-3, R2-5) | `pls-p3-config-builder`: design → `config/` edits using KB `schema.md`; canonical-form fold-back; lint/coverage loop.<br>`pls-p4-test-writer` + `references/test-spec.md`: the format of `ops`, `as_key`, `expectHttp`, `spec.vars`, `$var` and `list`; acceptance criteria → tests; role tests; G3 evidence template.<br>`pls-p5-release-manager`: `release-plan` → diff report (Japanese) → `apply` → `mark-applied` → smoke; templates for `diff-report.md`, `g3-verification.md`, `approvals.md`.<br>P6 as a runbook step: drift baseline after release. | Each skill has an eval case built from slice #3 (equipment) and graded by its rubric. No case answer may appear in a skill. |
| D3 ✅ | **Project scaffold** — done 2026-11-05: `pls init`, launcher `pls.py`, `pls skills check|sync`, template files; TD-14 (a)–(d) fixed; 46 + 6 tests (R3-1, R3-2) | `pls init <dir> --framework <path>` (or `templates/project/` + copy script) creates:<br>• `CLAUDE.md`, `.gitignore`, `environments.json` with `dev`/`stg` placeholders (`parent_id`, empty `sites`, `principals` per role);<br>• `connections.example.json`, empty ledger and traceability, the `requirements/`, `design/`, `config/`, `tests/`, `releases/` and `ops/` folders;<br>• skills copied and `framework.lock` written.<br>Framework path read from `framework.lock` (or env `PLS_HOME`) instead of a fixed `../`. `pls skills check` compares the project copy with the lock. | Unit tests; `pls init` then `pls lint` passes on the empty project. |
| D3b ✅ | **Fixes from the architecture review** — done 2026-11-05 (B1–B3 in the skills, KB `skeletons.md`; S1–S5, S7 in `pls` 0.7 with tests; S6, S8–S10 remain for D6 / before D7) (`docs/reviews/architect-review-d3.md`), decided by Nam 2026-11-05 | **B1** P5 with target dev = record only: P3/P4 deploy while building; P5 checks drift 0 since the tests, writes the diff report, then G4 = accept as released. plan.md, the lifecycle and P5 skills and `gates.md` all say the same.<br>**B2** roles prepared before the demo: `demo/roles.json`; groups, users, keys and principals are created during setup. P2 reuses existing roles; a G2 check that every `${principal:x}` and every `as_key` exists. In `http-check`, 401 = bad key and 403/404 = valid key without access.<br>**B3** skeleton exports per ReferenceType (Results, Issues; 1.5.2) in the KB; P2 needs no write and bootstrap stays in P3.<br>**S1–S4** tool defects (duplicate bootstrap, fold-back after an applied release, overwrite of a release, permissions on restore). Also S5 and S7 if cheap. | B1–B3 before D4; S1–S4 before D5; unit tests for each tool fix |
| D4 ✅ | **Setup guide + demo package** — done 2026-11-05: `docs/setup.md`, `demo/README.md` (script per gate), `demo/spec.md`, `demo/roles.json`; `pls init --roles`, lint L-ENV-01 (setup not finished); offline walk-through ok, real `http-check` is part of D5 (R1, R3-3, R3-4) | `docs/setup.md`:<br>• prerequisites (Python 3.10+, Claude Code on a machine that can reach Pleasanter, Pleasanter 1.5.x);<br>• one parent folder per environment;<br>• groups and users per role, API keys in environment variables;<br>• `connections.json`, `http-check`.<br>`demo/`: spec (equipment-loan request, Japanese), scenario script (what to say at each gate, expected stops, expected duration), the list of roles the spec needs, and a reset note (delete the demo folder in the UI). | A person follows `setup.md` to a green `http-check` without asking anyone. |
| D5 ✅ | **Real HTTP rehearsal** — done 2026-11-05: project `demo-equipment`, P1→G4 on dev, 10/10 API tests, round trip and drift 0, release `R-20261105-01-dev`; findings in `HANDOFF.md` (KB D28, TD-14h, test encoding fix); presenter guide `demo/lifecycle-and-demo-guide.html` (R2-4) | Nam's terminal on dev, in a new demo folder: `init` → `bootstrap` → `release-plan` → `apply` → `test` (both roles) → `mark-applied`. Fix whatever breaks. | Recorded in `demo/results/`; apply and bootstrap proven over HTTP. |
| D6 | **Clean-up** (R3-6) | README status and layout updated.<br>Framework `CLAUDE.md` rules updated for `pls` (no spike-era paths).<br>`spike/`, `patterns/` and `evals/results/` moved under `archive/`, or clearly marked non-core.<br>`HANDOFF.md` reduced to current state + next step. | A newcomer reading README → setup → demo finds no stale statement. |
| D7 | **Demo dry run — fresh agent session** | Clean clone → setup → spec → P1…P6 on dev, with Nam answering the gates. Record tokens, time and human corrections per phase in `demo/results/`. | Pass; fixes folded back into D1–D6. |
| D8 | **Team acceptance run** | A team member runs the demo alone from `docs/setup.md` + `demo/`, then gives feedback (where they got stuck, what was unclear). | They reach the dev release without help → demo ready. |

### Decisions (Nam, 2026-11-05)

- **Demo target = dev only.** No stg in the demo.
  - P3/P4 deploy to dev while building, through `release-plan` → `apply` → `mark-applied`.
  - P5 = **record only** (B1): drift 0 since the tests → diff report → G4 = accept the tested dev state as released → REQs marked released → P6 drift baseline.
  - stg stays supported by the tools but is out of the demo.
  - `demo/` and `templates/project/` declare only `dev`: one parent folder on MADLAB dev.
- **Dry run (D7) = a fresh agent session** (Claude Code, local, network path to dev), started from a clean clone.
- **Final acceptance (D8) = a team member who did not build the framework.** They run the demo from `docs/setup.md` + `demo/`. The framework is built for the team, so this is the real definition of done.

### Deferred (not needed for the demo)

Migrations over HTTP, reviewer agents, CI, Playwright smoke, prod / customer-side deploy package (ADR-0003), mail (TD-10), P6 on permission drift.

## Step 4c — Brownfield readiness (complex project in 運用保守) — PROPOSED, after the ADR review

**Why:** the first real candidate is an existing Pleasanter project in maintenance: standard master screens, one main screen with a custom layout, many server and client scripts, three environments (dev / stg / prod) that are hard to deploy between and to compare, dashboards, notifications, mail and scheduled jobs. The framework was proven on new apps and small changes only.

**Facts from Nam (2026-11-05):**
- The custom layout of the main screen lives **in the site** (`Htmls` / `Scripts` / `Styles`), so `unpack` already splits it into files — but these three components were never round-tripped (spike checklist rows 16–18).
- Pleasanter versions of the three environments are not known; the tool must **detect** them.
- Framework scope starts on **dev**; stg and prod are exported read-only at first.
- The project uses dashboards, notifications, mail and **jobs implemented as server scripts**.
- Whether dev can send real mail is **unknown**.
- Up to **three developers** change configuration at the same time.
- The aim is not to impose PR review but to find the most effective way of working.

**Decisions to take first:** ADR-0009 (version detection, KB verification), ADR-0010 (mail and job safety), ADR-0011 (sandboxes, harvest, semantic merge), ADR-0012 (scheduled server scripts). Nothing below is built before Nam reviews them.

### Work items (in order)

| # | Item | Content | Done when |
|---|---|---|---|
| BR1 🚧 | **Mail and job safety** (ADR-0010) — code done 2026-11-05 on branch `brownfield-adr` (`pls_side_effects.py`, 15 tests after the code review fixes, 69 + 6 green); open: SMTP answer and mail sink from the server operator, `op: "mail"` for P4, jobs guard (ADR-0012) | `side_effects` flags per environment, guards in `test` / `apply` / `bootstrap`, lint L-MAIL-01; ask the server operator about SMTP on dev; request a mail sink | Guards unit-tested; dev state recorded by a person; no test can run on a site with notifications while `mail` is `unknown` |
| BR2 🚧 | **Version detection** (ADR-0009, part 1) — code done 2026-11-05 on branch `brownfield-adr`: probe (no version in the API; `/versions` needs a session; login-page build token), `pls version`, http-check warning, `version_check` in release plans; 10 tests after the code review fixes, 79 + 6 green. Open: Nam records the app version of MADLAB dev; the candidate's three environments | Probe the version source on 1.5.2; `pls version`; label stored per environment; warning on change; version comparison in `release-plan` | Versions of all three candidate environments known; unit tests |
| BR3 | **Round-trip spike for the brownfield components** (ADR-0001 round 2) | On copies in dev: `Htmls`, `Scripts`, `Styles` of the main screen, dashboards, notifications with real-world addresses replaced; read-only probe of scheduled server scripts (ADR-0012) | Checklist rows 16–18 and dashboards ticked or marked out of scope; `release-plan` refuses sites with unverified components; ADR-0012 option chosen |
| BR4 | **Adopt** | `pls adopt --env <e>`: export every site of a folder, unpack, generate `environments.json`, slot ledger (zone `customer`), `permissions.json`, initial drift baseline; read-only on stg/prod (customer exports prod if MADLAB has no access) | One candidate site adopted from all three environments, 0 differences on re-export |
| BR5 | **Environment comparison** | `pls env-compare dev stg prod`: diff after replacing ids by logical names; classify each difference (expected id, intended per-env value, unintended) | Report for the candidate reviewed with the team; per-env values moved to `${env:x}` |
| BR6 | **Harvest, sandboxes, semantic merge** (ADR-0011) | `pls harvest`; `pls sandbox create/refresh/drop`; merge driver for `site.json`; ids in the ledger; text diff of scripts in reports | Three developers deliver tickets in parallel on one site, with merges and no lost change |
| BR7 | **Script tooling** | `node --check` lint; `pls refs suggest/rewrite` (hard-coded ids → `${site:x}` / `${principal:x}`, report for review); `pls xref` (scripts ↔ columns ↔ statuses ↔ sites) | All scripts of the candidate pass syntax lint; id rewrite report reviewed for one site |
| BR8 | **KB verification** (ADR-0009, part 2) | `verified_on` in the KB; probe specs for the entries the skills rely on (D8, D10, D19–D24, D27, D28); `pls kb-verify --env dev` | `kb-verify` green on MADLAB dev and on the candidate's dev |
| BR9 | **Skills** | `pls-x-onboarding` (adopt, env comparison, decisions per difference); `pls-x-spec-recovery` (as-is 画面設計書 per site, Japanese); `pls-p3-script-engineer` (script conventions, refactor rules, ladder for new changes only); `pls-p4-e2e-tester` (Playwright per role for the custom screen, unit tests of server scripts with a mocked context); `pls-p6-maintenance-triage` (問い合わせ／障害 → config / script / data / requirement) | Each skill has one eval case from the candidate, graded by its rubric |

**Definition of done:** on the candidate project, one real change request goes P1 → G4 on dev through sandboxes and harvest, with the as-is spec as P1 input, the version and side-effect checks green, and a stg release package that the team agrees to use.

**Order rationale:** BR1 first (safety before any test); BR2–BR3 before any write to a candidate site (D4: `updatesite` replaces everything); BR4–BR5 give value read-only (diff and history) before the workflow changes; BR6 changes how the team works, so it comes after they have seen the diffs.

## Step 5 — Real pilot & metrics (after the demo)

Metrics:
- Rate of AI changes correct on the first attempt
- Number of human corrections, and where
- Time from requirement to demo
- Drift incidents per month

## Decision log

| Date | Decision |
|---|---|
| 2026-11-04 | Split framework repo (`ai-dlc-pleasanter`) from customer project repos |
| 2026-11-04 | Constraints: on-prem, Pleasanter 1.5.x, customer may edit configuration |
| 2026-11-05 | Customer-facing questions (ADR-0002/0003/0005 storage) deferred as tech debt; use safest assumptions |
| 2026-11-05 | Spike runs on MADLAB internal dev (1.5.2) instead of localhost |
| 2026-11-05 | AI features call Claude via an internal gateway on Bedrock (IAM, no API keys); Terraform |
| 2026-11-05 | All repository documents are written in English |
| 2026-11-05 | AI gateway deployed to dev (ap-northeast-1) via Terraform in CloudShell as IAM user `namnh`; model `jp.anthropic.claude-haiku-5-5` (Japan-only inference profile) |
| 2026-11-05 | AI gateway parked as a reference pattern (`patterns/ai-gateway/`); not framework core |
| 2026-11-05 | `docs/architecture.md` v0.1 adopted as the frame: lifecycle P1–P6, gates G1–G4, invariants I1–I9 |
| 2026-11-05 | Slice #1 completed through P1–P6 on spike copies (escalation feature); architecture updated to v0.2 |
| 2026-11-05 | Skill/agent naming convention: `pls-<phase>-<role>` |
| 2026-11-05 | `pls` v0.2 (S1–S3 closed); skills v0.1: pls-kb-pleasanter, pls-p1-requirements-analyst, pls-p2-solution-designer |
| 2026-11-05 | Skills v0.2: slice answers removed from skills (eval leakage); eval case 001 passed for P1 and P2 with fresh agents |
| 2026-11-05 | AI gateway destroyed on AWS dev (`terraform destroy`, 13 resources) while parked; redeploy with `terraform apply` |
| 2026-11-05 | Mail deferred (TD-10): no mail sink, no mail tests, duplicate-mail defect left unfixed until mail is needed |
| 2026-11-05 | Slice 1.5: accepted stg drift 「緊急」 carried P6→P1→P5 with skills v0.2; R-20261105-02 record-only release; `pls` fix: last applied release ordered by instant (I9, regression test added) |
| 2026-11-05 | Step 4 items 1–4 done in `pls` v0.3: slot-collision check, multi-site release plan + automatic restore, migration gate (ADR-0004 accepted), site permissions in git (ADR-0006) |
| 2026-11-05 | Slice #2 (カテゴリ split, 経理 read, 合計対応時間) released to stg as R-20261105-05; B4 redesigned after T-015 (process access control, D20); test groups 372/373 kept until prod groups exist |
| 2026-11-05 | Stage = test/demo to shape architecture, design and process; customer questions, prod environment, real groups and mail deferred to the prod stage |
| 2026-11-05 | Feature work paused; demo readiness first (review `docs/reviews/demo-readiness.md`, plan Step 4b D1–D7) |
| 2026-11-05 | Architecture review after D3: GO with conditions. Decisions: B1 P5 on dev = record only; B2 roles prepared before the demo; B3 skeletons in the KB (D3b) |
| 2026-11-05 | Demo: one API key (the operator's); role tests deferred (project profile `Role tests: deferred`), restrictions verified in the configuration; per-role test users and keys in a later phase (TD-11) |
| 2026-11-05 | Setup simplified (Nam: too many steps): `pls setup` once per machine and environment saves a profile (URL, folder, ids by name, key file outside repos); `pls init` then creates a ready project and the first commit |
| 2026-11-05 | Permissions are a separate step of the design (P2 step 1b: roles → groups → matrix, `design/roles.json`), not setup. Groups are created by the person after G2 and bound by `pls principals`. Replaces B2 "roles prepared before the demo"; `demo/roles.json` removed |
| 2026-11-05 | D5 done: demo run `demo-equipment` released on dev (`R-20261105-01-dev`); KB 0.9 (D28), test-spec 0.2 (TD-14h) |
| 2026-11-05 | Brownfield readiness proposed as Step 4c for a complex project in 運用保守; ADR-0009 to ADR-0012 written as Proposed, waiting for Nam's review |
