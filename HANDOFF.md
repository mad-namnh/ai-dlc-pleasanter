# Handoff — state as of 2026-11-10 (branch `brownfield-adr`; sections further down describe 2026-11-09 and earlier)

> Next session may run on another Claude account: everything needed is in the repositories; nothing lives only in the chat.

## Resume here — 2026-11-10 (read this first)

**Where things stand.** The design review of 2026-11-09 (verdict NOT READY at every stage, `docs/reviews/design-review-2026-11-09/99-final-report.md`) is being remediated item by item from its roadmap (§9). **All P0 code and text work is done** (P0-1…P0-9) plus P1-1…P1-3 and P1-6; details per item in "Remediation progress 2026-11-10" below. What is left of P0 are Nam's decisions.

**Check the tree first:**
1. `cd "C:\Workspace\MADLAB\01. Project\ai-dlc-pleasanter"` → `git switch brownfield-adr` (local branch; **never push** unless Nam asks). Last code commit: `fix(pls): sandbox shared-write check in every plan…` (P1-6); working tree clean.
2. `cd tools/pls && python -m unittest discover -s tests` → **295 OK**; `node --test tests/test_runner.mjs` → **9 pass**. (Lines like `ConnectionAbortedError` / `TimeoutError` in the output are expected noise from the timeout tests.)
3. Switch back to `main` when done: `demo-equipment` runs the framework working tree and must stay on the demo baseline.

**Waiting for Nam (decisions, not code):**
1. ADR-0014 (`docs/adr/0014-trust-boundaries.md`): accept / change / reject each row TB-1…TB-15 (column "Nam's decision", all `pending`) and the 3 open questions; then set the ADR status.
2. ADR-0003: option A / B / C and the apply method for the release package, with customer IT (TD-02, TD-16).
3. J4: a written decision on each production blocker TD-01…TD-04 and TD-16…TD-19 (`docs/tech-debt.md`).
4. Method-L runs on dev by a person: package → verify → apply (J1); B1 live; C10.
5. Confirm the migration order of Accepted ADR-0004 (conversion **before** the configuration; `architecture.md` said "after" and was aligned to the ADR in P0-5).
6. Older open items from the review: WS-7 disputes D-1 (F4 → PARTIAL) and D-2 (G2 → FAIL); standard v2.2 (65 criteria; violated sub-part → FAIL).

**Next build work (roadmap order):** P1-7 (`pls test` on non-dev needs a G3/G4 record or typed confirmation; confirmation requires a TTY), P1-8 (runner parity: `exec` status, `as_key`, per-restore catch; ADR-0008 differences table); then P2 and P3. Still without a current-version eval: P1–P4, P6, onboarding, spec-recovery, script-engineer (H6).

**How we work (Nam's preferences, kept on purpose):**
- Chat with Nam in Vietnamese; everything in the repository in English (CLAUDE.md conventions).
- One roadmap item per commit, conventional message, no AI references, local only. Before each commit: full Python + node suites, and the new tests run against the parent commit (temporary `git worktree` in the scratchpad) to show they fail there.
- Every behaviour change updates the docs it touches in the same commit: the ADR, `docs/architecture.md`, the skill text (and its version in `skills/README.md`), the project template, and the progress block below.
- A design choice that is Nam's (architecture, scope, a reversal of an Accepted ADR) is asked with options and a recommendation before building; everything else is decided and reported.
- Evals: one fresh subagent per case, rubric unseen (inputs never point to `expected.md` or to the standard), dry run without `pls`/network; results in `evals/results/<skill>/<date>.md` with model and skill versions.

## Design review in progress — 2026-11-09 (read this first if you resume the review)

Standard `docs/review-criteria.md` v2.1; approved plan `docs/reviews/design-review-2026-11-09/00-review-plan.md`. Nam's decisions on the plan: H-1 report format = §5/§6 of the standard (groups A–J; there is no K); H-2 reports are kept in the repo under `docs/reviews/design-review-2026-11-09/` as evidence of the framework's reliability; H-3 isolated Python 3.10 allowed (`uv python install 3.10` into a scratch folder); H-4 Nam runs the method-L scenarios on dev; H-5 reviewers use copies of the tested projects `pls-onboard-playboard-r2`, `demo-equipment`, `pls-demo-equipment` without `.pls/connections.json`, `*.key`, `tests/seed/`; H-6 trust boundaries written as ADR-0014 (Proposed — Nam accepts); H-7 plan approved.

Reviewed commit: `10c328a`. Each workstream ran as an independent agent in its own `git worktree` (detached at `10c328a`) and its own project copies, outside the repository; tests only against the 127.0.0.1 fake server.

| Workstream | Criteria | Report in repo |
|---|---|---|
| WS-1 architecture, ADR | A1–A6, B9, D5, H4 | `ws-1-architecture.md` (done: 0 PASS, 3 PARTIAL, 6 FAIL) |
| WS-2 security, approval, prod isolation | B3, B4, B7, B10, C1, C4, D1, D2, J2 | `ws-2-security.md` (done: 0 PASS, 6 PARTIAL, 3 FAIL) |
| WS-3 write safety, recovery | B2, B11, C2, C3, C5–C11 | `ws-3-write-safety.md` (done: 1 PASS, 4 PARTIAL, 6 FAIL) |
| WS-4 determinism, records, KB | B1, B8, D3, D4, D6, E1–E4, F1–F4 | `ws-4-determinism.md` (done: 2 PASS, 6 PARTIAL, 5 FAIL; B1 live part needs Nam, scenario in report §6) |
| WS-5 portability, performance | G1–G6 | `ws-5-portability.md` (done: G1 FAIL, G2 PARTIAL, G3 PASS, G4 FAIL, G5 PARTIAL, G6 PARTIAL) |
| WS-6 skills, agent governance | B5, B6, H6, I1–I6, J5 | `ws-6-skills.md` (done: 1 PASS, 7 PARTIAL, 2 FAIL) |
| WS-7 evidence check + final verdict | H1, H2, H3, H5, J1, J3, J4 + summary (standard §6) | `99-final-report.md` (done: demo / cstg / prod all NOT READY) |

**Progress 2026-11-09 (session 2):** review complete — all reports committed. Verdict: NOT READY at every stage. Open for Nam: accept/fix ADR-0014 (TB-1/2/3/8 compensating controls shown false), WS-7 disputes D-1 (F4→PARTIAL) and D-2 (G2→FAIL), PARTIAL-vs-FAIL rule for standard v2.2, plan says 66 criteria but standard has 65, method-L runs on dev (B1 live, C10). Next: remediation roadmap in `99-final-report.md`.

**Remediation progress 2026-11-10** (roadmap `99-final-report.md` §9; review items still open for Nam are listed above):
- Done, committed: `5e5cda5` → P1-1 (recovery states `applying` / `uncertain` / `recovery-required`), P1-2 (`mark-applied` reads back, checks SiteId and export age, no re-stamp), P1-5 in part (bootstrap records an unanswered createsite), P1-4 in part (numeric env values never substituted). `7d9a6fa` → P1-3 (read-back and drift compare Title and managed permissions; duplicate names keyed `Name@Id`).
- Done, committed: **P0-1** — a G4 record stores the digest of each planned release (`tools/pls/pls_release_digest.py`); `apply` / `bootstrap` on stg refuse a plan, payload, rollback, scheduled-script file or target changed since G4; G4 recorded before `release-plan` does not cover it. Also covers part of P0-2 (HTTP apply refuses steps/rollback that differ from `per_site`) and of P0-3 (a hand-written `releases` string never matches), and part of P0-5 (browser runner writes only plans with `env_role: dev`; `bulkupsert` still unguarded). Tests `test_g4_bound_to_release_content.py` (8 of 9 fail on the parent commit).
- Done, committed: **P0-3** — `pls_gate.latest` orders by the instant in `at`, not the local `date`; a rejection wins a tie; a record more than 5 minutes in the future, or with a wrong shape (types of gate / decision / approver / `items` / `releases`, `at` without offset), or unreadable JSON refuses every gate check and is an L-GATE-01 lint finding; records read with `utf-8-sig`. Tests `test_gate_records_ordering_and_shape.py` (7 of 9 fail on the parent commit).
- Done, committed: **P0-4** (Nam chose: pls command + record; `pls review` record) — `pls profile set Approvers|Operators|Origin|role` records the person's words under `gates/profile/` and writes the row / environments.json; once a field has a record, pls reads the recorded value (hand edits change nothing); lint L-PRF-01 reports unrecorded or differing rows and unrecorded stg/prod roles; `pls init --approver` records its values. `pls review as-is <site>` (G2 approver) records the review bound to the sha256 of `design/as-is/<site>.md`; L-LAD-01 no longer counts as-is documents and counts DES-000 only for scripts in a reviewed, unchanged document. `refs --keep/--ref` need `--quote`. `jobs.verified` re-checked against the profile when used. Skills lifecycle, onboarding, spec-recovery, P3 config-builder and the project template say so. Modules `pls_profile_records.py`, `pls_as_is_review_records.py`; tests `test_profile_and_review_records.py` (9 of 10 fail on the parent commit). Suite: 268 Python OK, 8 node pass.
  - **Action for existing branch projects** (`pls-onboard-playboard-r2`, `pls-demo-equipment`): lint now reports L-PRF-01 and L-LAD-01 (DES-000 without a review record) until the person runs `pls profile set …` for their rows and `pls review as-is` per site. No write command is blocked by this.
- Done, committed: **P0-6** — L-SEC-01 is a refusal before writing in `unpack` and `harvest` (config/) and in `release-plan` (payload from config/ and rollback from the live site, before anything goes to releases/); one helper `secrets_in` / `refuse_secrets` for lint, adopt and these commands. Tests `test_secrets_never_reach_the_repository.py` (3 of 3 fail on the parent commit).
- Done, committed: **P0-5** — `pls migrate <R> [--rollback]` sends each migration folder's explicit `data` with one `bulkupsert` over HTTP: write guard, G4 on non-dev (the G4 digest now covers migration folders), mail / job checks, typed confirmation, run recorded in `plan.json` `migrations_run` before the call (`migrated` / `failed` / `uncertain`, never re-sent); `apply` refuses until the migrations have run (ADR-0004 order); `--rollback` sends only `rollback.data` prepared by a person. Runner `bulkUpsert` refuses non-dev plans; agents no longer use the runner (HANDOFF tools line, ADR-0008, lifecycle skill corrected). Module `pls_migrate.py`; tests `test_migrate_over_http.py` (7 of 8 fail on the parent commit) + runner test.
  - **Nam to confirm:** `docs/architecture.md` said migrations run *after* the configuration; Accepted ADR-0004 says conversion *before* it. Code and architecture.md now follow ADR-0004. Open (ADR-0004): can records read by `get` be sent to `bulkupsert` unchanged on 1.5.x (rollback built from `backup/`)? Not verified; pls does not do it.
- Done, committed: **P0-2** (rest; first part came with P0-1) — `plan_steps_problem` also requires `sites` = `per_site`, each step's file to be its own site's (release-plan naming when `per_site` names none) and `expect_updated_time` = the planned snapshot; `mark-applied` applies the same rule before reading back; `bootstrap` refuses a step for a site not in the environment, under another folder, twice, or not a createsite; the browser runner checks steps with the same rule. Tests `test_plan_steps_and_bootstrap_match_the_environment.py` (4 of 4 fail on the parent commit) + runner test. Suite: 283 Python OK, 9 node pass.
- Done, committed (text part): **P0-7** — ADR-0014 revised: TB-1/TB-2/TB-3/TB-8 now state their controls as they are (what exists, what is missing: gitignored `.pls/connections.json`, self-asserted fail-open run-log actor, missing EV-03/EV-10, local-only project repos, the preflight→write window is not detected); TB-4/TB-6/TB-7 updated; rows TB-9…TB-15 added (env overrides, setup/init opt-in, `file:` keys, untrusted content in the agent context, spike scripts, shared tenant, API key privilege); a "Nam's decision" column, all **pending**; two code-closable gaps added (piped stdin confirms, effective `allow_write` not logged). Template hard rule 7: never rewrite history or edit `gates/` / `releases/`; agents never drive the runner (template token rule, architecture transport paragraph).
  - **Nam to do:** decide each ADR-0014 row (accept / change / reject) and the 3 open questions; then set the ADR status.
- Done, committed: **P0-8** — eval cases EV-01/03/09/10 (lifecycle cases 004–007) and P5 cases 001 (to G4) / 002 (after G4) written; skill versions bumped for the P0-4/P0-5 changes (lifecycle 0.15, P5 0.6, onboarding 0.6, spec-recovery 0.4, P3 config 0.4); 9 runs + 1 blind re-run on claude-opus-5-5, all **PASS** (`evals/results/pls-x-lifecycle/2026-11-10.md`, `evals/results/pls-p5-release-manager/2026-11-10.md`). Fixed from the runs: template rule 7 narrowed (P5 writes release documents), P5 step 4 migration order, EV inputs no longer point to the standard. Still without a current-version eval: P1–P4, P6, onboarding, spec-recovery, script-engineer (H6).
- Done, committed (build part): **P0-9** — `pls package <R>` (only with G4 bound to the content; deterministic zip in `dist/`, manifest recorded in `releases/<R>/package-manifest.json`; migration `backup/` never shipped and no longer part of the G4 digest), standard-library `verify.py` shipped in the package (refuses altered / added files, wrong target or release, content G4 did not approve, missing rollback; prints the digest), `templates/project/handover/customer-responsibilities.md` (J5), ADR-0003 note, P5 0.7, TD-16…TD-19 for the prod blockers. Tests `test_package_and_verify.py`. Suite: 287 Python OK, 9 node pass.
  - **Nam to do (P0-9 decisions):** decide ADR-0003 (A/B/C + apply method, TD-02/TD-16) with customer IT; written decision on each production blocker TD-01…TD-04, TD-16…TD-19 (J4); method-L dry run by a person: package → verify → apply on dev (J1).
- Done, committed: **P1-6** — `release-plan` (and `sandbox refresh`) refuses, for every sandbox site, a summary or server script that writes to a site the sandbox did not copy, unless a person accepted that place: `sandbox create|refresh --allow-shared-writes` records the places in `envs.<env>.shared_writes`, and a later new place is refused again (WS3-F6). `pls test` writes only to the environment's own sites in every environment, not only in sandboxes (WS2-F9). ADR-0011, architecture.md, script-engineer 0.3, test-writer 0.5. Tests `test_sandbox_shared_writes_checked_by_every_plan.py` (6 of 8 fail on the parent commit; the other two are baselines). Suite: 295 Python OK, 9 node pass.
  - **Decided without asking, Nam may change:** the acceptance is a list of places, not a yes/no per sandbox (review open question "is `--allow-shared-writes` a per-sandbox decision"): stricter, and the flag on `refresh` re-accepts the current places. No record of who accepted (the flag is "checked by a person", as before).
  - **Action for existing sandboxes** created with `--allow-shared-writes`: the next `sandbox refresh` is refused until a person runs it once with `--allow-shared-writes`.
- Not started: P1-7, P1-8, all P2 and P3 (P2-9 L-LAD-01 partly done: as-is excluded). All P0 code and text work is done; P0 still waits for Nam's decisions (ADR-0014 rows, ADR-0003, J4 sign-off). Next build work: P1-7, P1-8.

**To resume on another account:** for every row still "pending", recreate the setup (worktree at `10c328a` outside the repo, project copies without key material) and run that workstream from its rows in the plan (Deliverable 2, 4, 5) with the rules of the standard §7; then run WS-7 in a fresh context over all reports and write `99-final-report.md` (standard §6, verdict per stage). Reports are copied into the folder above and committed one by one; review test files stay in the worktrees and are never committed.

## Current state — 2026-11-09 (before the review remediation)

**Resume in a new session / another account:** everything is in this repository; nothing lives only in a chat.
1. `cd "C:\Workspace\MADLAB\01. Project\ai-dlc-pleasanter"` → `git switch brownfield-adr` (local branch, **never push** unless Nam asks).
2. Read this section, then `docs/plan.md` Step 4c and its decision log, then `docs/reviews/architecture-audit-2026-11-08.md`.
3. Check: `cd tools/pls && python -m unittest discover -s tests` and `node --test tests/test_runner.mjs` (current counts: see "Resume here" at the top).
4. Switch back to `main` when done: `demo-equipment` runs the framework working tree and must stay on the demo baseline.

**State**
- `main` (= GitHub `34188a5`) is the **demo baseline**; do not commit there unless Nam asks.
- Branch `brownfield-adr` (last commit: `pls gate`): ADR-0009…0012, plan Step 4c BR1–BR9 built and run on MADLAB dev (kb-verify 7/7 on 1.5.2, sandbox trial, adopt of site 797 read-only), skills onboarding / spec-recovery / script-engineer / maintenance-triage, lifecycle routes by profile **Origin** (`new` / `existing`).
- Tests: 214 Python + 6 node; write-path inventory test (`test_write_guards.py`); gate records (`test_gate.py`).
- Audit after BR9: ready with conditions. Fixed on the branch: template `.gitattributes`, docs refreshed, `exec` expects 200, request `timeout`, socket cleanup, **`pls gate`** (I4 checked by the tool: profile approvers, L-GATE-01, G3/G4 records needed for non-dev plan/apply/bootstrap).
- 2026-11-09: audit F-05 and F-09 closed. **Jobs guard** (ADR-0010/0012): scheduled scripts in `config/_tenant/scheduled-scripts/`, refusals while `jobs` is `unknown`, per-env resolved files and a manual step in every release that changes them, `pls jobs-verified` by an operator of the env (profile row `Operators`) or a G4 approver, body lint (L-REF-01, L-SEC-01, L-SCR-01/02). **Sandboxes** never deploy tenant resources and use the riskier side-effect state (ADR-0011 Safety). **Onboarding first** for Origin `existing` (L-ONB-01 and refusals). Review resolution: `plans/reports/code-reviewer-2026-11-09-jobs-guard.md`; kept on purpose: TD-15.
- Local project `pls-adopt-797` (sibling folder, not in git remote): trial adopt of site 797, read only. `demo-equipment`: released demo, local only, never pushed.

**Rules that hold (Nam's decisions)**
- Site 797 and any customer site: read only. Customer site packages / exports never go into git (keep them in the project's `.pls/`).
- Commit by explicit paths, never `git add -A`. Writes only to dev; `--yes` only for the target Nam names. Agents never delete Pleasanter sites; Nam deletes them.

**Next**
1. Onboarding of the first real project on dev (Nam deploys it first): `pls init <name> --origin existing --stage project --target stg`, then skill `pls-x-onboarding`. Projects created before `pls gate` get L-GATE-01 for past approvals: Nam confirms them again (see lifecycle `references/gates.md`).
2. After that run: Nam decides ADR-0009/0010/0011 (Proposed). Projects that use scheduled scripts: add the `Operators` row to their profile (template row) — without it only G4 approvers may confirm a manual deploy.
3. Later (not started): split `http_cmd` (audit F-06); structured L-LAD-01 (F-08); tie a G4 record to an environment; browser e2e runner decision (`pls-p4-e2e-tester`); KB probes for D16/D19/D20/D23; daily drift.

## What this is

AI-DLC framework for Pleasanter projects (MADLAB). The goal is that AI assists the whole lifecycle with human gates G1–G4:

P1 requirements → P2 design → P3 build → P4 verify → P5 release → P6 operate

Owner: Nam. Discussion is in Vietnamese; **everything in the repos is English** (Pleasanter end-user messages stay Japanese).

## Repositories (on Nam's machine, `C:\Workspace\MADLAB\01. Project\`)

| Repo | Role |
|---|---|
| `ai-dlc-pleasanter` | Framework: architecture **v0.3**, ADRs 0001–0008, `tools/pls` 0.7, `skills/` (KB 0.9, P1 0.3, P2 0.5, P3 0.1, P4 0.2, P5 0.1, lifecycle 0.1), `evals/` (cases 001–002), `patterns/ai-gateway` (parked). Remote: `https://github.com/mad-namnh/ai-dlc-pleasanter` (`main`) |
| `pls-demo-inquiry` | First project repository: slices #1, 1.5 and #2. All of them are merged to `main`; no other branches. |
| `pls-demo-equipment` | Second project repository: slice #3, a new app (equipment loans) created by the framework (dev 44628/44629, stg 44671/44672) |
| `demo-equipment` | D5 demo run (2026-11-05), created by `pls init`: equipment loans from `demo/spec.md`, dev 44709/44710 under AI-DLC-DEMO (44708), release `R-20261105-01-dev`, G1–G4 approved by Nam. **Local only, never pushed** (demo project) |

`_to_delete/` folders are leftovers (the agent shell cannot delete files); safe to delete.

## Status

- **Slice #2 done (2026-11-05)** — `docs/slices/slice-02-report.md`.
  - Scope: customer mail → REQ-007…015 → DES-003, in three parts:
    - カテゴリ split, with migration M1;
    - 経理 read-only access, with permissions in git;
    - 合計対応時間, with a Summary and migration M2.
  - Released to stg as **R-20261105-05**:
    - 2 sites, applied in dependency order, with automatic restore on failure;
    - round trip 0 differences;
    - smoke tests T-009, T-010 and T-016 pass.
  - One design loop: T-015 showed that a read-only user still sees process buttons. That led to KB D19 being corrected, D20 being added, B4 being redesigned with process access control, and G2 being approved again.
- `pls` v0.3:
  - Commands: unpack, pack, canon, lint, diff, drift, classify, coverage, slots, plan, release-plan, mark-applied.
  - Permissions and process ACLs (`Groups`/`Users`/`Depts`) are mapped per environment through `${principal:x}` (ADR-0006, D20).
  - Migration gate per ADR-0004.
  - Runner: `applyRelease`, `rollbackRelease`, `backupRecords`, `bulkUpsert`, and `runTests` (create on another site, `$var` references).
  - Tests: python 24/24, node 6/6.
- KB `pls-kb-pleasanter` 0.5: behaviours D12–D20 come from probes on dev.
- Skills v0.2 (P1, P2) passed eval case 001. They were used for slice #2.
- Slice #1 and slice 1.5 are done (see the reports and the decision log in `docs/plan.md`).

## Stage (decided by Nam, 2026-11-05)

**Test / demo stage.** The goal now is to shape the architecture, design and process. It is not to deliver to a customer. Therefore:
- Customer questions (Q1–Q24, O7), the prod environment and the real groups (O3) are **prod-stage items**. They are deferred and do not block anything. Keep using the `[assumed]` defaults.
- The test principals (10061, 372, 373) stay as they are.
- Mail stays deferred (TD-10).

## Start of the next session

1. ✅ (2026-11-05) All three repos were checked and committed. The session must have `pls-demo-equipment` connected as a folder as well.
2. Optional: Nam re-runs `pls test tests/api/equipment.json --env dev --site loans` from `pls-demo-equipment` (HTTP transport) — expected all pass / pass-api-only.
3. Then continue with step 4 below (architecture gaps) or step 5 (architecture.md v0.3). Multi-user HTTP role tests are deferred (demo stage).

Tools: `pls` 0.7 (HTTP transport + browser runner fallback; `setup`, `init`, `principals`, `skills`), 54 python tests + 6 node tests. The agent sandbox cannot reach Pleasanter over HTTP (proxy 403). **Corrected 2026-11-10 (design review P0-5):** agents do not use the browser runner; it is a fallback for a person on dev only (ADR-0014 TB-7). Agents and people use `pls` over HTTP; migrations use `pls migrate`.

## Current focus (2026-11-05, Nam)

**Feature work is paused. Demo readiness comes first.** Review: `docs/reviews/demo-readiness.md` (verdict: not ready). Plan: `docs/plan.md` Step 4b, items D1–D7, D1 is done (lifecycle skill + project CLAUDE.md template). D2 is done: skills P3, P4 and P5 0.1. Tool gaps are in TD-14 ((b)–(d) are needed before D7). D3 is done: `pls init`, launcher, `skills check|sync`, and TD-14 (a)–(d) fixed (pls 0.6). An independent architecture review after D3 gave GO with conditions (`docs/reviews/architect-review-d3.md`). D3b is done: B1–B3 are in the skills and KB; S1–S5 and S7 are fixed in `pls` 0.7 (53 + 6 tests). D4 is done and simplified: `pls setup` (once: URL, folder link, hidden key, login; groups found by name; profile in `~/.pls/profiles/`) + `pls init <name>` (ready project + first commit). Nam created folder AI-DLC-DEMO (44708) and groups zz_demo_総務 (374) / zz_demo_社員 (375). Permissions are a design step (P2 1b → `design/roles.json`; after G2 the groups are created and `pls principals` binds them). **D5 is done (2026-11-05)**: `pls init demo-equipment` + the demo script ran end to end on dev (P1→G4, 10/10 API tests, round trip and drift 0). Findings: (1) G2 groups must be created with exactly the names in `design/roles.json` — in the run the existing `zz_demo_*` groups were used instead; (2) KB 0.9 D28 `[[Users*]]`; (3) `siteConfig` does not substitute `$vars` (TD-14h, test-spec 0.2); (4) REQ-008 (permission only) has no API test while role tests are deferred — accepted at G3 on config + manual screen check; (5) `pls` tests read files without `encoding` and failed on a cp932 console — fixed. Test records deleted from dev. Presenter guide: `demo/lifecycle-and-demo-guide.html`. S6 and S8–S10 come in D6, before D7. Decided: the demo stops at **dev** (no stg); D7 is a fresh agent session; D8, a team member running it alone, is the real acceptance.

## Next steps (in order) — before the pause

1. ✅ Skills 0.3 / KB 0.6 from the slice #2 findings (commit c02bd12); project pin upgraded.
2. **Eval case 002** (P1, P2) with fresh agents — run 1 done (2026-11-05, `evals/results/*/2026-11-05-case002.md`):
   - P1 0.3: **PASS** (the input leaked the slice #2 REQ count through the source file header; `input.md` fixed).
   - P2 0.3: **FAIL** on one item: the probe for process buttons of a read-only role was composed correctly but scheduled after G2, and the design kept the expected (wrong) branch. Fixed in **P2 0.4** (design-changing probes are G2 prerequisites, otherwise take the safe branch).
   - Run 2 with 0.4: **PASS** (`evals/results/pls-p2-solution-designer/2026-11-05-case002.md`). `pls-demo-inquiry` pinned to P2 0.4.
   - Follow-ups: `pls classify` classifies process access control (`Processes[].Groups/Users/Depts`) as config-only — should be permission-impacting (tool gap); watch whether design-changing probes on verified behaviour (PRB-3 type) are treated as G2 prerequisites in the next case.
3. ✅ **Slice #3 — new app end to end (2026-11-05)**: equipment loans in `pls-demo-equipment`, P1→P6, G1–G4 approved, stg R-20261105-E03 applied (0-difference round trip, smoke pass, drift baseline 0). ADR-0007 (new sites), pls 0.4, KB 0.7 (D21–D27), skill P2 0.5. Report: `docs/slices/slice-03-report.md`.
3b. **HTTP transport (ADR-0008, pls 0.5)** — `pls http-check / export / bootstrap / apply / test / backup` with operator-local `.pls/connections.json` and keys in environment variables; role tests pick the key per spec (`as_key`). 37 unit tests (fake Pleasanter server). First real run on dev by Nam (2026-11-05): 総務 suite OK after 2 tool fixes (BOM, 1.0 vs 1); re-run of `equipment.json` after the fix pending. Multi-user (社員 key) run **deferred by Nam** — demo stage. API key pasted in chat during the run → Nam to revoke and recreate. The agent sandbox still has no network path, so agents keep the browser runner as fallback.
4. **Architecture / process gaps worth a demo slice:**
   - P6 operate on slice #2: a drift on permissions, and on the process ACL.
   - Transport ADR-0003: the manual base64 transfer is the most token-heavy step. Decide whether to automate it.
   - A migration on a larger data copy (plan Step 4 item 3).
   - Line-level script diff (S6).
5. ✅ `docs/architecture.md` v0.3: slices #1–#3, the transport, phase statuses and next steps (§9). Step 4 = architecture §9 items 1–5.
6. Prod-stage items (customer round, prod environment, real groups, mail) — later.

## Escaped defect found by the eval (I9)

In R-20261105-01, view 未完了 (Id 2) now includes status 150. Notification #1 sends to [Manager], watches Status/ClassE, uses view 2 as its condition and has the subject 「優先度「高」の問い合わせが未対応です」. So it also fires on every escalation, and the manager gets a second, misleading mail. It also does not filter on 優先度 at all. **Deferred with all mail work (TD-10).**

## Environments

| Item | Value |
|---|---|
| Pleasanter dev (1.5.2) | `https://pleasanter-dev.mad-lab.jp/` — reachable **only from the built-in browser** of the Claude desktop app. Log in manually; the API works with the session (no API key). |
| Spike folder | site 44562 `zz_spike_roundtrip` — all writes stay inside it |
| Project dev | 問い合わせ 44565, 対応履歴 44566 (last: R-20261105-04-dev) |
| Project stg | 問い合わせ 44573, 対応履歴 44574 (last: **R-20261105-05**) |
| Test principals (dev/stg) | user `zz_test_keiri` (10061), groups `zz_test_経理` (372) and `zz_test_サポート` (373). **In use:** stg/dev permissions and the `escalate` process ACL point to 372/373, so keep them until prod groups replace them (O3). Credentials are in `pls-demo-inquiry/tests/seed/` (gitignored). |
| Probe sites | 44588 `zz_probe_data_20261105`, 44592 `zz_probe_child_20261105` — dummy data only; delete in the UI (TD-08) |
| Original demo sites | 42410 / 42411 — **never written to** by the framework |
| AWS dev | AI gateway destroyed 2026-11-05 (`terraform destroy`); the AI feature on 44565/44573 fails when ticked; normal saves are unaffected. |

## How transport works today (S4)

Exports and payloads move between the browser and the repo as gzip + base64. Large ones are split into halves, and each half is verified with SHA-256 on both sides before use. Deploys run only with complete payloads, after a preflight check that the target has not changed since the plan.

## Open items elsewhere

- `docs/tech-debt.md` TD-01…TD-11.
- Demo site 42410 still has the D7 bug (shared script `const`) and the old API-key script; fixing it is the owner's call.
- Revoke the Anthropic API keys once nothing uses them.
