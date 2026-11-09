# WS-1 — Architecture, ADR and invariant governance

Reviewer: independent AI agent (static, method S only). Commit `10c328a` (detached worktree `wt-ws1`, clean). Standard `docs/review-criteria.md` v2.1; plan `docs/reviews/design-review-2026-11-09/00-review-plan.md`. No file in the repository was modified; no command wrote to the repo; no network.

Legend: **[F]** fact verified in this review (location given) · **[H]** hypothesis for another workstream.

ADR-0014 is **Proposed**. Every ACCEPTED BOUNDARY below reads "(ADR-0014 Proposed — holds only once Nam accepts it)".

---

## 1. Finding table (standard §5)

| ID | Criterion | Severity | Status | Stage | Finding | Evidence | Reproduction | Proposed fix | Verification |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Every command, skill, lint rule, template maps to phase/artifact/invariant | Low | PARTIAL | demo | All subcommands except two, all 11 skills and all 16 modules map. Unmapped or phantom: commands `setup`, `principals` absent from `docs/architecture.md` §7.1; lint rules `L-ENV-01`, `L-REF-02` emitted by code but absent from catalogue §7.2; catalogue/§3.3 name things the code does not have (`pls deploy`, rule id `L-SLOT-02` — collision check exists but never emits that id); template layout (`gates/`, `ops/log/`, `ops/usage/`, `ops/onboarding/`, `design/roles.json`, `config/_tenant/scheduled-scripts/`, `meta.json`) not in §3.2, which still shows `meta.yaml`, `approvals.md`, `checks.json`, `secrets.catalog.json` | parser `tools/pls/pls.py:2501-2645`; lint ids `pls.py:573-582` (L-ENV-01), `:551,595,600` (L-REF-02); `docs/architecture.md:97,277` (`deploy`), `:301` (L-SLOT-02), `:43-91` (§3.2); `templates/project/CLAUDE.md` Layout table | `grep -c "pls setup\|pls principals" docs/architecture.md` → 0; `grep -o "L-SLOT-02" tools/pls/*.py` → none | Update §7.1/§7.2/§3.2 from the parser and lint code (one table generated or checked by a test that compares `add_parser` names and emitted rule ids with the doc) | Doc-vs-code test lists 0 unmapped items |
| A2 | Decisions are in ADRs; code introduces none | Medium | FAIL | demo | Architecture-level behaviour exists in code with no ADR Decision: (1) gate-record model — `gates/*.json`, last-decision-wins, single approver per gate, G3 required by `release-plan` and G4 by `apply`/`bootstrap` for every non-dev env; architecture says gate records live in `releases/` (I4) and G4 needs "customer owner + operator"; (2) `Operators` profile row and the operator/g4-approver roles for `jobs-verified` — stated only in notes appended to Accepted ADR-0012; (3) onboarding-first refusal (L-ONB-01 + refusals of `step`/`gate`/`bootstrap-plan`/`release-plan`) — only in lifecycle skill §0; (4) `pls setup`/`init` machine profile: stores the admin key in `~/.pls/profiles/`, writes `allow_write: true` by default and labels the profile URL `role: dev` — contradicts ADR-0008 "operator opt-in" and "file under `.pls/`"; (5) `file:` key refs not confined to `.pls/` (absolute path wins in `Path(_dir)/ref`); (6) env overrides `PLS_CONNECTIONS`, `PLS_PROFILE_DIR`, `PLS_ACTOR`; (7) framework distribution (launcher, `framework.lock`, `skills check/sync`). Implementation detail (no ADR needed): gate file naming/microsecond ordering, profile parse forms, POSSIBLE display groups, timeout range, log schema, canonical-defaults table (covered by D8 + ADR-0009 point 6) | `tools/pls/pls_gate.py:1-11,154-197`; `pls.py:1023-1026,2121-2125,2195`; `docs/architecture.md:27,116-119`; `docs/adr/0012-…:50-57` (added by `5fc9f55`, 2026-11-09); `pls_gate.py:200-257`; `pls.py:1902-1973` (`allow_write: True` at :1959, `role: dev` at :1968); `tools/pls/pls_http.py:41,84-88`; `tools/pls/pls_log.py:78-82`; `pls.py:1773-1897` | `grep -l "pls gate\|Operators\|PLS_CONNECTIONS\|pls setup" docs/adr/*.md` → only 0012 (notes) and 0014 | One ADR "Gate records and approver model" (location, binding, roles per stage, single vs dual approver); move Operators into it or a superseding ADR; ADR (or ADR-0008 amendment) for setup profile, key-file location and env overrides; ADR for framework distribution | ADR README lists them; each code docstring cites its ADR |
| A3 | ADR status and lifecycle match reality | Medium | FAIL | demo | 7 ADRs are **Proposed** while implemented, tested and relied upon: 0001 (Decision section still "Not decided — waiting for spike round 2" although round 2 results are written above it and `pls_scope` refuses plans on its basis; ADR-0012 already cites "ADR-0001 option B"), 0007, 0008 (made the default transport by template rule and ADR-0014 TB-7), 0009, 0010, 0011, 0013. Accepted ADR-0012 was edited after acceptance (2026-11-09) with new decisions (Operators row, roles, fallback to G4 approvers), against `docs/adr/README.md:20`; its "Follow-up" (choose B or C) is stale. Implemented-without-test: ADR-0004 decision 3 (conversion and rollback by `bulkupsert`) — `Client.bulk_upsert` has no caller and no test; runner `bulkUpsert` untested. `architecture.md` §10 lists ADRs only to 0008. Same issue raised 2026-11-08 (audit F-03), not resolved, not in tech-debt | `docs/adr/0001-…:3,46-52`; ADR headers (0007 :3, 0008 :3, 0009 :3, 0010 :3, 0011 :3, 0013 :3); `git log -- docs/adr/0012*` → `5fc9f55` after `ae5d8dc` (accept); `docs/adr/0012-…:63`; `tools/pls/tests/test_write_guards.py:32` (`"bulk_upsert": set()`); `tools/pls/tests/test_runner.mjs` (6 tests, none for bulkUpsert); `docs/architecture.md:377-379`; `docs/reviews/architecture-audit-2026-11-08.md` F-03 | read headers vs code; `grep -rn bulk_upsert tools/pls/tests` → only the inventory | Nam decides each Proposed ADR (accept / accept with limits / supersede); move ADR-0012 notes into a new ADR that supersedes the jobs-verification part; add tests for bulk upsert path or mark ADR-0004 decision 3 as runner-only/manual | ADR README statuses = code reality; no Accepted ADR changed after acceptance (git log) |
| A4 | One authoritative source per rule | Medium | FAIL | demo | Conflicting statements of the same rule: (1) **gate records** — architecture I4 and §4 "`releases/R-*/approvals.md`" vs code/template `gates/*.json` via `pls gate`; (2) **migration order** — ADR-0004 decision 3 "backup → conversion → configuration → verification" vs architecture P5 "runs after the configuration" (step 3 after apply); (3) **browser runner on stg** — architecture §3.3 and P5 list runner `applyRelease` as an stg write path, ADR-0014 TB-7 accepts it for dev only, runner header says "dev/stg-like"; (4) **write rule** — framework `CLAUDE.md` rule 1 still the spike-era wording (`localhost`, `config.json`, `scripts/common.py`) next to the `pls` rule; template rule 2; ADR-0008; architecture §3.3 (`pls deploy`); (5) **run-log failure** — ADR-0013 decides "Logging never breaks a command", ADR-0014 lists it as an open gap; (6) **versions/status** — architecture §7.3 (KB 0.7, P1 0.3, P2 0.5) and §8 ("no P3 skill") vs `skills/README.md` (KB 0.13, P1 0.4, P2 0.6, P3 0.3…); HANDOFF repo table (ADRs 0001–0008, pls 0.7, KB 0.9) stale; (7) I7 enforcement "secret lint at unpack, in CI and pre-deploy" vs code: L-SEC-01 only in `lint` and `adopt`; no CI | `docs/architecture.md:27,87,119,97,207-223,322-331,350-357`; `docs/adr/0004-…:47`; `docs/adr/0014-…:41`; `tools/pls/browser/pls-runner.js:3`; `CLAUDE.md:9`; `templates/project/CLAUDE.md` rule 2; `docs/adr/0013-…:20`; `docs/adr/0014-…:46-50`; `skills/README.md:7-17`; `HANDOFF.md:44`; `pls.py:538,604,1268` (only SECRET_RES uses) | grep commands above | Make architecture.md point to ADRs and to generated tables instead of restating; fix the seven items; remove spike-era rule from framework `CLAUDE.md` (D6 item) | Grep for each rule returns one normative source |
| A5 | No customer-specific content in the core | Low | FAIL | demo | No hostnames, person names, keys or business data in `tools/`, `skills/`, `templates/` (non-test). Found: app name "PLAY BOARD" (customer application, per plan G5) in 5 places incl. a heuristic regex with that app's logging identifiers; MADLAB-dev site ids as KB/defaults evidence (site 797 — adopted brownfield candidate — 15 lines in core; 42410/42411/44565 once; 44734/44735 once); a sample id in CLI help. Severity Low: display-only regex and evidence comments, no data. Whether "PLAY BOARD" and site 797 are customer-owned is [U] — Nam to classify | see §7 A5 table | grep per §7 | Replace app-specific identifiers in `pls_scripts.py:322` with a configurable list (project config / `patterns/`); refer to evidence by probe id, not customer app name / site id; keep MADLAB probe ids only in KB `probes/` | Re-run §5 searches → 0 customer hits |
| A6 | Trust boundaries written down | High | PARTIAL | demo | ADR-0014 exists with 8 rows, each with risk, owner and stage [F]. But: (a) **Proposed**, so no boundary holds yet; (b) **missing boundaries present in code**: env overrides `PLS_CONNECTIONS`/`PLS_PROFILE_DIR`/`PLS_ACTOR`; `pls setup` → `init` auto opt-in (`allow_write: true`, URL labelled `role: dev`); `file:` key refs readable from any path; untrusted Pleasanter content (scripts, titles, site packages) entering the agent context during adopt/onboarding/spec-recovery/triage (prompt-injection, EV-09); spike write path with localhost exemption; shared tenant resources across dev/sandboxes (and stg on the same MADLAB server per HANDOFF); API-key privilege (admin keys); production package/customer runner only as open question; (c) **compensating controls that do not hold**: TB-1 "every change is visible in git diff/history" — `.pls/connections.json` (where `allow_write` lives) is gitignored; TB-3 "no force-push rule" — no such rule anywhere in the repo, and project repos are local-only (HANDOFF); TB-2 "run log records the actor" — actor is `PLS_ACTOR` or git `user.name`, self-asserted, and log writes fail open; (d) TB-7 conflicts with architecture §3.3/P5 (A4) | `docs/adr/0014-trust-boundaries.md:33-50`; `pls_http.py:41,84-88`; `pls.py:1905,1959,1968-1973`; `pls_log.py:78-82,122`; `templates/project/.gitignore:1`; `grep -rni "force-push\|force push" CLAUDE.md templates skills docs` → 0 hits; `HANDOFF.md:21` | see §5 | Add rows TB-9…TB-14 (§5); fix the three compensating controls (protected remote or signed commits for gate records; log actor ≠ approver; state that `.pls/` changes are invisible to git and add `http-check`-style print of effective `allow_write` to the run log); Nam accepts per row | Every ACCEPTED BOUNDARY in the batch reports cites an Accepted TB row |
| B9 | INV-09: each finding → rule/test/KB/TD | Medium | PARTIAL | demo | All findings of the four source sets traced row by row (§8). **20 items have no artefact** (none of rule, regression test, KB entry, tech-debt line) and 2 are partial: e.g. coverage passes on empty traceability (D3-review S6), dev "test data only" migration override (S8), line-level script diff (slice-1 S6), D7 post-deploy save regression, migration volume (S2-6), HTTP migration path (R2-6), audit F-03/F-06/F-07/F-08. The register `docs/review-findings.md` is stale: 9 rows "Open" that are implemented (A1, B3, C5, D3, D4, D7 lint, D8, D11, A3 wording) and KB findings D21–D31 are not in it (CLAUDE.md requires spike findings there). Register ids A1–D20 collide with criteria ids | `docs/review-findings.md:9-45`; `skills/pls-kb-pleasanter/references/behaviours.md` (D3–D31); `pls.py:739-755` (coverage iterates only traceability entries, `ok` starts True) | §6 | Add a "Trace" column (rule / test / KB / TD) to the register, import D21–D31, prefix ids (`RF-`), add TD lines for the 20 | Every register row has a non-empty trace |
| D5 | Tamper evidence for records | High | FAIL | prod | TB-3 names git history as the boundary for gates, releases and run log, **accepted for demo only**; cstg/prod follow-up (protected branch / signed commits / record store) is an open question. Code protects nothing beyond exclusive create (`open("x")`) and an approver-name re-check; `latest()` orders by `date`/`at` read from the file, so a hand-written later record wins. Cited control "no force-push rule" does not exist; project repos are local-only. For `demo` the view would be: ACCEPTED BOUNDARY (ADR-0014 Proposed — holds only once Nam accepts it), weakened by the missing control. Gap does not block demo | `docs/adr/0014-…:13-14,38`; `pls_gate.py:166,174-178,181-188`; `HANDOFF.md:21` | static; scenario 1 of plan D5 (hand-written G4) belongs to WS-2 | Before cstg: gate records on a protected remote branch with required review, or signed commits verified by `pls`, or digest of each record in the release plan | Hand-edited/rewritten record detected by a check |
| H4 | Gaps from earlier reviews closed or in tech-debt | Medium | FAIL | demo | Of the earlier-review items (D3 review 19, demo-readiness 12, audit 11, jobs-guard report), **17 are neither closed nor in `docs/tech-debt.md`**: audit-2026-11-08 F-03 (ADRs Proposed), F-06 (`pls.py` now 2 989 lines, `http_cmd` 448 lines — worse), F-07 (socket warnings, not verifiable statically), F-08 (L-LAD-01 substring still at `pls.py:620`), F-02 partly (HANDOFF repo table); D3 review S6, S8, S9 (partly), S10, N1–N6 ("Open — D6, before D7"; plan D6/D7 not done, no deadline in TD); demo-readiness R2-6 (migration over HTTP), R3-6 (clean-up). Jobs-guard report: all closed or TD-15 [F] | `docs/reviews/architecture-audit-2026-11-08.md:59-136`; `docs/reviews/architect-review-d3.md:53-66`; `docs/plan.md:78,81-82`; `docs/tech-debt.md` (TD-01…TD-15); `plans/reports/code-reviewer-2026-11-09-jobs-guard.md:96-133` | §7 | One TD line per open item with deadline (most "before cstg"); close F-03 by ADR decisions | `docs/tech-debt.md` contains every open item |

Counts: PASS 0 · PARTIAL 3 (A1, A6, B9) · FAIL 6 (A2, A3, A4, A5, D5, H4) · ACCEPTED BOUNDARY 0 · NOT VERIFIABLE 0. No Critical. High: A6, D5 (D5 is stage prod).

---

## 2. Map P — phase → artifact (completed)

| Phase | Commands (verified in parser) | Skill (exists) | Artifacts (code writes) | Human point (code-enforced?) | Gaps vs architecture |
|---|---|---|---|---|---|
| Setup / init | `setup`, `init`, `skills check/sync`, `principals` | — | `~/.pls/profiles/<name>.json` + `.admin.key`; project tree, `.claude/framework.lock`, `.pls/connections.json` | none | not in §7.1 (`setup`, `principals`); decisions without ADR (A2) |
| Onboarding (Origin `existing`) | `version`, `adopt`, `adopt-package`, `env-compare`, `refs`, `xref`, `spec-skeleton`, `harvest` | `pls-x-onboarding`, `pls-x-spec-recovery` | `ops/onboarding/*-summary.md`, adoption records `releases/A-*`, `design/as-is/` | onboarding-first refusal (code: `pls_gate.py:209-216`) | no ADR (A2) |
| P1 | `step`, `gate G1` | `pls-p1-requirements-analyst` | `requirements/REQ-*.md`, `index.md` | G1 record (`gates/`) | arch says records in `releases/` |
| P2 | `xref`, `gate G2` | `pls-p2-solution-designer` | `design/decisions/DES-*`, `roles.json`, slot ledger | G2 record | — |
| P3 | `unpack`, `pack`, `canon`, `lint`, `bootstrap-plan`, `bootstrap`, `bind`, `principals`, `sandbox`, `harvest`, `merge-site`, `merge-install`, `refs` | `pls-p3-config-builder`, `pls-p3-script-engineer` | `config/**`, `config/_tenant/scheduled-scripts/` | bootstrap on stg needs G4 (`pls.py:2195`) | §8 says "no P3 skill" (stale) |
| P4 | `test`, `coverage`, `kb-verify` | `pls-p4-test-writer` | `tests/api/`, `tests/results/`, `releases/<R>/g3-verification.md` | G3 record required by `release-plan` for non-dev (`pls.py:1023`) | reviewer agents (§7.3) not built; coverage passes on empty traceability |
| P5 | `release-plan`, `plan`, `gate G4`, `apply`, `mark-applied`, `jobs-verified`, `backup` | `pls-p5-release-manager` | `releases/<R>/plan.json`, payload/rollback, scheduled-scripts, operator report, `apply-log.json` | G4 for non-dev apply; typed confirmation; `jobs-verified` (person's words) | migration conversion has no `pls` path (runner only) |
| P6 | `drift`, `export`, `harvest`, `env-compare`, `slots` | `pls-p6-maintenance-triage` | `ops/drift/` | accept/revert by person (decision record for `--accept-drift`) | `pls-p6-ops-watcher` not built; no incident records |
| Cross-phase | `step`, `usage`, every command (run log) | `pls-x-lifecycle`, `pls-kb-pleasanter` | `ops/log/*.jsonl`, `ops/usage/`, `gates/` | — | `ops/log`, `gates/` missing from §3.2 |

## 3. Map Q — invariant enforcement (completed)

| INV | Enforcement in code [F] | Tests [F] | Documented claim not matched by code | Status hint for owner WS |
|---|---|---|---|---|
| 01 | unpack/pack/canon; `mark-applied` compare; drift vs last applied | `test_pack_dev_reproduces_export`, `test_release_lifecycle_drift_against_last_release`, `test_release_plan_mark_applied_and_drift_per_site` | — | WS-4 B1 |
| 02 | `plan_site` L-DEP-01 (`pls.py:987-989`), drift refusal, `UpdatedTime` preflight | `test_pls.py`, `test_http.py` | API limit stated in ADR-0014 TB-8 | WS-2/3 |
| 03 | `assert_writable` (`pls_http.py:92-97`), G4 for stg | `test_prod_is_never_written`, `test_apply_bootstrap_test_kbverify_send_nothing_without_allow_write` | "write guard in tooling" does not cover browser runner (TB-7) nor setup's auto `role: dev` labelling | WS-2 B3 |
| 04 | `pls gate` record/require, L-GATE-01, `job_verifier` | `test_gate.py` (11), `test_jobs_verified_accepts_an_operator_of_the_env_or_a_g4_approver` | architecture I4 "Gate records in `releases/`; reviewer agents are read-only" — wrong location; no reviewer agents exist | WS-2 B4, A6 |
| 05 | L-LAD-01 substring match (`pls.py:620-621`) | `test_lint_rules` | "over-coding reviewer (P4)" not built; brittle (F-08) | WS-5 B5 |
| 06 | diff/classify/coverage/drift in code | `test_classify*`, `test_coverage_checks_the_element_not_only_the_file` | coverage `ok` on empty `traceability.json` (`pls.py:745-755`) | WS-6 B6/B8 |
| 07 | L-SEC-01 in `lint` (`pls.py:604`, jobs `:538`) and `adopt` refusal (`:1268`); literal keys refused (`pls_http.py:89`) | `test_lint_rules`, `test_adopt.py` | **"at unpack, in CI and pre-deploy"** — `unpack` (`pls.py:2863-2867`) and `harvest` (`:1650`) write config without a secret check; `release-plan` has none; no CI | WS-2 B7 |
| 08 | `coverage`, `traceability.json` | as above | REQs absent from traceability not reported | WS-4 B8 |
| 09 | process only (register, KB, TD) | `test_kbverify.py` (KB probes) | register stale; D21–D31 missing; no incident records | this report B9 |

## 4. Map R — ADR → code, status vs reality (completed)

| ADR | Status (header) | Implementation [F] | Tests [F] | Reality | Finding |
|---|---|---|---|---|---|
| 0001 scope | Proposed; Decision "Not decided" | `pls_scope.py`, release-plan refusal, `--accept-unverified` | `test_scope.py` (7) | option B in force | A3: decide; Decision text contradicts its own round-2 section |
| 0002 slots | Proposed (TD-01) | ledger, L-SLOT-01, collision check in plan | `test_slots_*`, `test_slot_ledger` | partial (zones need customer) | consistent |
| 0003 prod deploy | Proposed (TD-02) | none | — | nothing built | consistent; J-group |
| 0004 data-impacting | Accepted | classify, migration gate (P-MIG-01), runner `backupRecords`/`bulkUpsert`, `pls backup` | `test_migration_problems`, runner `backupRecords pages…` | conversion/rollback by bulkupsert: no `pls` caller, no test; order contradicts architecture P5 | A3, A4 |
| 0005 secrets | Partially accepted | L-SEC-01 (lint, adopt), key refs | `test_lint_rules`, adopt tests | not at unpack/plan | A4 (I7 claim) |
| 0006 permissions | Accepted | permissions.json refs, L-PERM-01, pack refusal | `test_permissions_*`, `test_process_access_control_refs` | matches | — |
| 0007 new sites | Proposed | bootstrap-plan/bootstrap/bind | `test_bootstrap_plan_and_bind_new_site`, write-guard tests | proven slice #3, D5 | A3 |
| 0008 HTTP | Proposed | `pls_http.py` | `test_http.py` (22), `test_write_guards.py` | default transport | A3; setup profile/`file:` paths deviate (A2) |
| 0009 version/KB | Proposed | `pls_version.py`, `pls_kbverify.py` | `test_version.py` (10), `test_kbverify.py` (8) | point 6 (defaults per schema) not built — stated | A3 |
| 0010 mail/jobs | Proposed | `pls_side_effects.py`, guards in test/apply/release-plan | `test_side_effects.py` (33) | in force | A3 |
| 0011 sandboxes | Proposed | sandbox/harvest/merge, `pls_merge.py` | `test_sandbox_merge.py` (14) | first run recorded | A3 |
| 0012 scheduled scripts | Accepted + notes 2026-11-09 | jobs layout, `lint_jobs`, `jobs-verified`, Operators | `test_pls.py` jobs tests | notes add decisions after acceptance | A3 (README rule), A2 |
| 0013 observability | Proposed | `pls_log.py`, `pls_usage.py` | `test_observability.py` (13) | fail-open logging decided here | A3; conflicts with ADR-0014 gap list (A4) |
| 0014 trust boundaries | Proposed | n/a | n/a | see §5 | A6 |
| — none — | — | gate model, Operators, onboarding refusal, setup profile, env overrides, launcher/lock/skills sync | `test_gate.py`, `test_change_work_on_an_existing_app_waits_for_the_onboarding_summary`, `test_init_*`, `test_skills_check_*` | in force | A2 |

## 5. Map S — trust-boundary coverage vs ADR-0014

| Boundary in code | ADR-0014 row | Risk/owner/stage present | Gap |
|---|---|---|---|
| Operator files (`gates/`, plan.json, profile, environments.json, connections) | TB-1 | yes | control "visible in git" false for gitignored `.pls/connections.json` |
| CLI words (`--approver`, `--quote`, `--by`, `--yes`) | TB-2 | yes | control "run log records the actor": actor self-asserted (`pls_log.py:78-82`), log fails open (`:122`) |
| Git history for records | TB-3 | yes (demo only) | "no force-push rule" not found in repo; project repos local-only |
| Role label vs URL | TB-4 | yes (demo, cstg) | setup/init labels the typed URL `role: dev` with `allow_write: true` automatically (`pls.py:1959,1968-1973`) — not stated |
| Agent harness permissions | TB-5 | yes | — |
| Framework code (`PLS_HOME`, lock) | TB-6 | yes | `merge-install` registers a git merge driver that runs framework code on merges — not stated |
| Browser runner | TB-7 | yes (dev only) | contradicts architecture §3.3/P5 (stg path) |
| API limits | TB-8 | yes | — |
| **Env overrides** `PLS_CONNECTIONS`, `PLS_PROFILE_DIR`, `PLS_ACTOR`, `CLAUDE_CONFIG_DIR` | **missing** | — | redirect connections (allow_write) / profiles / actor without file change |
| **Key file location** (`file:` any path; setup key in `~/.pls/profiles`) | **missing** | — | ADR-0008 says "file under `.pls/`"; `pls_http.py:85` joins absolute path |
| **Untrusted Pleasanter content → agent context** (scripts, titles, site packages in adopt/onboarding/spec-recovery/triage) | **missing** | — | prompt injection (standard EV-09) |
| **Spike write path** `spike/round-trip/scripts/common.py` (localhost exemption) | **missing** | — | separate guard named in framework CLAUDE.md rule 1 |
| **Shared tenant resources** (SMTP, scheduled scripts; dev, sandboxes, MADLAB "stg" on the same server per HANDOFF:118-121) | **missing** (ADR-0010/0011 cover parts) | — | env label ≠ isolation |
| **API key privilege** (admin keys) | **missing** (ADR-0008 Limits) | — | — |
| Production package / customer runner | open question only | no | expected FAIL/NOT VERIFIABLE in J-group |

## 6. A1 unmapped items

1. Commands `setup`, `principals` — absent from architecture §7.1 (phase: setup / P2–P3).
2. Lint rules `L-ENV-01` (setup not finished), `L-REF-02` (references resolve per env) — emitted, not in §7.2.
3. Phantom in docs: `pls deploy` (§3.3, §7.1), rule id `L-SLOT-02` (behaviour exists in plan, id never emitted), `pls validate` (marked "Not built" — ok).
4. Template/layout: `gates/`, `ops/log/`, `ops/usage/`, `ops/onboarding/`, `design/roles.json`, `config/_tenant/`, `meta.json`, `.gitattributes` not in §3.2; §3.2 items not produced by any command: `meta.yaml`, `secrets.catalog.json`, `releases/<R>/checks.json`, `approvals.md` (legacy, read only by L-GATE-01), `tests/permissions/`, `tests/smoke/`.
5. §7.3 planned assets not built (reviewer agents, `pls-p6-ops-watcher`, hooks) — mapped but not built; status column absent.

## 7. A5 search results (counts only; no customer content copied)

Scope: `tools/` (excl. `tools/pls/tests`), `skills/`, `templates/`.

| Search | Hits | Files |
|---|---|---|
| Hostnames/URLs (excl. example/localhost/vendor) | 0 real (placeholders `pleasanter-dev.example.jp`, `<pleasanter-dev-host>`) | `pls_http.py:9`, `templates/project/connections.example.json:4` |
| MADLAB dev host name / mail domain / operator login | 0 | — |
| Spike/probe/test-principal names (`zz_*`) | 0 | — |
| HANDOFF site ids 44562, 44566, 44573, 44574, 44588, 44592, 10061 | 0 | — |
| Site ids 42410, 42411, 44565 | 1 line (evidence text) | `tools/pls/canonical-defaults.json:32` |
| Site ids 44734/44735 | 1 line | KB `behaviours.md` (D29/D30 evidence) |
| Group id 372 | 1 line (example) | `skills/pls-p3-config-builder/references/config-layout.md:30` |
| Site id 797 (adopted brownfield site) | 15 lines | `tools/pls/pls_scripts.py` (comments/regex docs), KB `api.md:45`, `behaviours.md:26`, `probes/D21-process-view-without-filter.json` |
| Sample id 44656 | 1 | `pls.py:2550` (CLI help) |
| App name "PLAY BOARD" / app-specific identifiers | 5 lines | `pls.py:85`, `pls_scripts.py:5,99,322` (regex with app-specific logger names), KB `api.md:59` |
| Business terms (romanised/Japanese site names) | 2 generic examples (`--name` help, spec-recovery example) | `pls.py:2561`, `skills/pls-x-spec-recovery/SKILL.md:41` |
| Secrets / keys | 0 | — |

## 8. B9 trace table

Legend: R rule/lint/refusal · T regression test · K KB entry · TD tech-debt · ADR · — none.

**`docs/review-findings.md`**

| Finding | Trace | Register status vs reality |
|---|---|---|
| A1 migrations | ADR-0004, R P-MIG-01, T `test_migration_problems` | "Open" — stale |
| A2 slot collisions | R L-SLOT-01 + plan check, T `test_slots_collision_blocks_plan`, TD-01 | ok |
| A3 cross-site deploy | R release-plan order/restore, T `test_release_plan_orders_by_dependency_and_reverses_rollback`, ADR-0007 | ok (partly) |
| B1 network boundary | R `assert_writable`, T `test_prod_is_never_written`, TD-02, ADR-0014 TB-4 | "Open" |
| B2 ownership zones | TD-01, drift | ok |
| B3 deterministic diff | R `pls diff/classify`, T `test_classify*` | "Open" — stale |
| B4 round trip | R `pls_scope`, T `test_scope.py` | ok |
| C1, C2 | closed | ok |
| C3 Playwright brittle | — | no artefact |
| C4 on-prem data | ADR-0005, TD-03 | ok |
| C5 pre-deploy drift | R release-plan drift refusal, T `test_release_lifecycle_drift_against_last_release` | "Open" — stale |
| D1 built-in MCP | ADR-0003 mention only | informational |
| D2 CodeDefiner | — | informational |
| D3 ids in scripts | R L-REF-01/03, `pls refs`, T `test_scripts.py`, K | "Open" — stale |
| D4 updatesite replaces | R L-DEP-01, T `test_pls.py`, K | "Open" — stale |
| D5 plaintext secret | R L-SEC-01 (lint, adopt), T `test_lint_rules`, ADR-0005 | ok (not at unpack/plan) |
| D6 package remap | K (SKILL.md), ADR-0007 | ok |
| D7 const/let | R L-SCR-01, T `test_lint_rules`, K; **post-deploy save regression: —** | "lint rule open" — stale; regression part none |
| D8 canonicalisation | R `canon`, L-CAN-01, `canonical-defaults.json`, T `test_canon_and_lint`, K probe D08 | "automation open" — stale |
| D9, D10 | K (+ probe D10) | ok |
| D11 drift baseline | R drift `--baseline`, T drift tests, K | "Open" — stale |
| D12–D20 | K; R classify/L-PERM-01; T classify/permission tests | ok |
| D21–D31 (KB only) | K; R L-PRC-01 (D21), scope (D29/D30), ADR-0012 (D31) | **not in register** |

**Slice reports**

| Finding | Trace |
|---|---|
| S1 | R canon/L-CAN-01, T |
| S2, S3 | R drift baseline, classify, T |
| S4 transport | ADR-0008 |
| S5 mail sink | TD-10 |
| S6 line-level script diff | — (architecture §9 next step only) |
| S7, S8 | K, skills + evals |
| S2-1 | K rule D19/D20 |
| S2-2 | R L-PERM-01, T `test_process_access_control_refs` |
| S2-3 | R classify summary, T `test_classify_summary_change_is_data_impacting` |
| S2-4 | skill P1/P2 impact checklist |
| S2-5 | runner halves + SHA-256 (no test found) |
| S2-6 migration volume | — (plan Step 4 item 3, no TD) |
| S2-7 `ai1.js` generator | — (customer item O2) |
| Slice 3 lessons 3–4 | TD-13 |

**`docs/reviews/`**

| Source | Closed with R/T | In TD | None |
|---|---|---|---|
| architect-review-d3 (B1–B3, S1–S10, N1–N6) | B1–B3 (skills/KB), S1–S5, S7 (code + tests) | — | S6 (coverage empty passes — still `pls.py:745-755`), S8, S9 (partly in `setup.md:103`), S10 (CLAUDE.md:9 still spike-era), N1 (no orphan handling), N2–N6 (not re-verified; listed open) |
| demo-readiness (R2-1…R3-6) | R2-1…R2-5, R3-1…R3-5 via D1–D5 | — | R2-6 (HTTP migration), R3-6 (clean-up D6) |
| architecture-audit-2026-11-08 (F-01…F-11) | F-01, F-04 (`pls gate`), F-05 (jobs guard), F-09 (L-ONB-01), F-10, F-11 (timeout) | — | F-02 (partly), F-03, F-06, F-07, F-08 |

**`plans/reports/code-reviewer-2026-11-09-jobs-guard.md`**: H1, H2, M1–M4, L1–L4, L6, L7 and all test gaps → code + tests (resolution table lines 102-127, spot-checked test names exist); L5 and safe-side note → TD-15 (a), (c). Fully traced.

Items with no artefact (20): C3, D7 post-deploy regression, slice S6, S2-6, S2-7, D3-review S6, S8, S10, N1–N6, R2-6, R3-6, audit F-03, F-06, F-07, F-08. Partial (2): D3-review S9, audit F-02. Informational without need of an artefact: D1, D2.

## 9. Notes for other workstreams

- **WS-2 (B3/B7/C1):** `unpack` (`pls.py:2863-2867`) and `harvest` (`pls.py:1650`) write `config/` with no secret check; `release-plan` runs no L-SEC-01 → B7 "L-SEC-01 at unpack, lint, plan" likely FAIL for unpack/plan. `pls setup` writes `allow_write: true` and `init` labels the profile URL `role: dev` (`pls.py:1959,1968-1973`) → dev write without per-env opt-in or role check; `PLS_CONNECTIONS` (`pls_http.py:41`) swaps the whole connections file; `file:` refs resolve outside `.pls/` (`pls_http.py:85`).
- **WS-2 (B4/D1):** `GT.latest` (`pls_gate.py:174-178`) orders by `date`/`at` read from the record; a hand-written record with a later `at` overrides a later real rejection. G4 is single-approver although architecture §4 says "customer owner + operator" (relevant at cstg). ADR-0004 decision 5 (customer business approver signs the migration at G4) has no record field.
- **WS-3 (D6):** ADR-0013 states the policy "Logging never breaks a command" (fail open, Proposed); ADR-0014 lists it as an undecided gap — get Nam to decide which stands for cstg.
- **WS-4 (B8/E):** `coverage` returns ok for an empty traceability file and ignores REQs not listed (`pls.py:739-755`; D3-review S6 still open).
- **WS-5 (H3/F):** KB D21–D31 not in the findings register; H3 trace should use §8.
- **WS-6 (I2/I5):** framework `CLAUDE.md:9` still carries the spike-era write rule (`localhost`, `config.json`, `scripts/common.py`).
- **J-group:** ADR-0004 conversion/rollback via `bulkupsert` has no `pls` path; only the browser runner, which ADR-0014 TB-7 does not accept beyond dev → no accepted executor for a stg migration.

## 10. Top risks

1. **ADR-0014 is Proposed and incomplete** (6 missing boundaries, 3 compensating controls that do not hold) → every I3/I4 boundary status in this review is provisional; B4/D1/D5 cannot become ACCEPTED BOUNDARY yet.
2. **Architecture document contradicts code** on gate records, migration order, runner on stg and I7 enforcement → an agent or person following `docs/architecture.md` can do the wrong thing (e.g. treat `approvals.md` as approval, run conversion after config).
3. **Secrets can reach git through `unpack`/`harvest`** while I7 claims a check at unpack and pre-deploy (needs WS-2 confirmation by test).
4. **Governance drift:** 7 ADRs Proposed but enforced, one Accepted ADR edited with new decisions, earlier audit F-03 unaddressed → cannot tell decided from experimental rules.
5. **Setup convenience bypasses opt-in:** profile auto `allow_write: true` + `role: dev` label from a typed URL, keys readable from any path — decisions with no ADR on the I3 path.

## 11. Unresolved questions

- Is "PLAY BOARD" a customer application and site 797 customer-owned? (decides A5 severity)
- Should a `docs/plan.md` item with a milestone count as "target" for H4, or only `docs/tech-debt.md`? (reported strictly per the standard)
- D5: confirm the reviewer convention for a prod-stage criterion whose boundary is accepted only for demo (reported FAIL for prod, ACCEPTED BOUNDARY view for demo).
