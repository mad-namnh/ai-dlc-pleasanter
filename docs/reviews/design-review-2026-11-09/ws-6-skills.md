# WS-6 — Skills, agent governance and human workflow

- **Standard:** `docs/review-criteria.md` v2.1; plan `docs/reviews/design-review-2026-11-09/00-review-plan.md` (WS-6 rows, scenario 26)
- **Commit reviewed:** `10c328a62efd3e7f7598d0b2e4f17ca13c4e3226` (worktree `wt-ws6`, detached, `git status` clean after the review)
- **Environment:** Windows 11, Git Bash, Python 3.12.10, node v24.19.0. No network. No Pleasanter access.
- **Reviewer:** independent AI agent (WS-6). Repository content treated as data.
- **Labels:** [S] = static (read), [F] = runtime-verified on a copy / by running a test.

## 1. Criteria summary

| ID | Status | Severity | Stage | One line |
|---|---|---|---|---|
| B5 | PARTIAL | Medium | demo | Skill text complete. L-LAD-01 exists and has a positive test, but it matches a script name as a substring anywhere in `design/**/*.md`. A false clearance was reproduced [F]. No negative test. Shared scripts and rungs 4–5 are not checked. |
| B6 | PARTIAL | Medium | demo | Most computable results come from `pls`. Some computable checks are still left to the model: shall-count, `[assumed]`→question links, "nothing in config lacks a design element", numeric ids in links/summaries, project-state reconstruction. |
| H6 | FAIL | Medium | demo | 9 of 10 behavioural skills changed after their last eval. P5 has never been evaluated (case has no `expected.md`). EV-01…EV-10 are absent. 8 of 12 result files have no model or skill version. |
| I1 | PARTIAL | Low | demo | 6 of 11 skills have all five elements. script-engineer, P6, onboarding and lifecycle have no checklist. P3/P5 have no explicit Outputs section. |
| I2 | PARTIAL | High | demo | No instruction to read, print or ask for keys. Strong prohibitions are present. But the skills tell the agent to write guard inputs itself after "the person says it": profile `Approvers` and `Origin`, `environments.json` `role`, and the review attestation that clears L-LAD-01. The `--yes` wording for sandboxes is loose. Installed copies lack the newest prohibitions. The trust boundary (ADR-0014 TB-1/TB-2) is only Proposed. |
| I3 | PARTIAL | Low | demo | `skills check` exits 1 on all 3 copies [F]. No local edits in the 2 hashed copies. All 3 lag the framework. 1 copy has an old lock format, so edits there cannot be detected. |
| I4 | PARTIAL | Low | demo | Token rules are in lifecycle §2.8, the template and P4/spec-recovery. `ops/usage` exists in only 1 of 3 copies. That one session covers 2 change requests, against the "one session per CR" rule [F]. |
| I5 | PASS | — | demo | Spot-check [S]: no Vietnamese in the repo (scripted scan). Customer-facing texts are Japanese, the rest English, in skills and in the project copy. |
| I6 | PARTIAL | Low | demo | No common completion-report rule in the skills (only the gate message and the script-engineer hand-over). slice-03 report: no changed-file list and no command results. The code-review report is complete. |
| J5 | FAIL | Medium | prod | No handover document or template section names customer responsibilities for backup, incident and recovery. They exist only as open questions in ADR-0003/0004 (TD-02). Does not block `demo`. |

Counts: PASS 1 · PARTIAL 7 · FAIL 2 · others 0.

## 2. Findings (§5 format)

| ID | Criterion | Severity | Status | Stage | Finding | Evidence (file:line, test, command output) | Reproduction | Proposed fix | Verification |
|---|---|---|---|---|---|---|---|---|---|
| B5 | INV-05 ladder reason + L-LAD-01 | Medium | PARTIAL | demo | (1) Skill side complete: P2 step 2 + checklist, `ladder.md`, DES template `Rung:` line, script-engineer "Before you edit" #1. (2) L-LAD-01 clears a server script when its `Name` appears as a substring in **any** `design/**/*.md`. That includes `design/as-is/*.md`, which `pls spec-skeleton` generates with every script name (`pls_spec.py:148-158`), and files of other sites. So the ladder reason is never checked, and spec-recovery's "DES-000 only after review" control is bypassed as soon as the skeleton exists. (3) Shared server scripts are exempt (`pls.py:620` `not it.get("Shared")`). Rungs 4–5 (extended SQL, external integration) have no lint. (4) Only a positive test; no test that a script with a DES reason passes, and none for the substring/as-is case. | `tools/pls/pls.py:572` (decisions = concat of all design md), `:620-621`; same logic in adopt report `:1289-1291`; `pls_spec.py:154-158`; `tests/test_pls.py:84-90` `test_lint_rules` (ran: OK). [F] In copy `pls-onboard-playboard-r2`: 38 non-shared named server scripts; `lint --summary` → `L-LAD-01 5`. One site has 4 server scripts but only 3 are flagged. The 4th has a 2-character name, is in no `design/decisions/*.md`, and is "cleared" by a substring hit in a **different site's** `design/as-is/*.md`. | Copy a project; in `config/<s>/server-scripts/_index.json` give a non-shared script a short name (e.g. `ab`) that occurs in any `design/**/*.md` text; `pls lint` → no L-LAD-01. Also: run `pls spec-skeleton --site <s>` on an adopted site with undecided scripts → L-LAD-01 disappears before any review. | Match only `design/decisions/DES-*.md`. Require a structured entry per script (e.g. a `## Server scripts` table row `\| <site> \| <Name> \| rung 3 \| reason \|`), matched by site + exact name. Exclude `design/as-is/`. Decide on shared scripts in an ADR line. Add negative tests. | Unit tests: script named in as-is only → flagged; script in another site's DES → flagged; script with DES row → not flagged; shared script per decision. |
| B6 | INV-06 tools compute | Medium | PARTIAL | demo | Tool use is good: P2 uses `xref` and `lint`, P3 `canon/lint/coverage/refs`, P4 `test/coverage`, P5 `drift/release-plan/mark-applied`, P6 `drift/classify/env-compare/version/xref`, onboarding `adopt/env-compare/refs/version`, spec-recovery `spec-skeleton` (tables are tool output). Computable checks still left to the model: P1 "exactly one `shall`" and "every `[assumed]` points to a question" (`p1 SKILL.md:47,51`, no lint); P3 "nothing in config lacks a design element" and "Check links and summaries yourself" for numeric ids (`p3-config SKILL.md:48,50`); P2 slot choice "first slot never allocated" (`p2 SKILL.md:31`; `pls slots` exists but is not named); lifecycle §1 project-state reconstruction from status lines (no `pls status`), which EV-08 depends on; P2 change classification is written by the model at design time, and `pls classify` only runs later at release-plan. | Skill lines cited; `pls.py:1-60` command list (no status command, no REQ lint) | Read the cited lines | Add lint rules L-REQ-01 (single shall, `[assumed]`→question) and L-REF for links/summaries; a coverage check for config elements not in traceability; `pls status` (state summary from records); in P2, run `pls classify` on a dev export, or tell the agent the tool decides at release-plan. | New lint tests; skill text names the commands |
| H6 | Evals after behaviour edits; EV cases | Medium | FAIL | demo | See §6. 9 of 10 behavioural skills have behaviour-changing versions after their last eval. Those include the I4-critical lifecycle 0.10–0.14 (gate recording, approver naming, `jobs-verified`) and P5 0.3–0.5 (G4 record, `--yes`, `jobs-verified`). P5 was never evaluated: its case has only `input.md`, which says "Not run separately: the D7 dry run…", and there is no results file. EV-01…EV-10: no case exists (`grep -rl "EV-0" evals` → none). Partial overlap only: EV-03, EV-05, EV-10. 8 of 12 result files do not record the model (`evals/README.md:13` requires model + skill version). README rule "Add or update an eval case … that shows why" (`skills/README.md:26`) was not followed for most bumps. ADR-0014 TB-2 lists EV-03/EV-10 as compensating controls (`0014:36`), but those controls do not exist. | `skills/README.md:7-17`; `git log` per skill dir vs per results dir (§6); `evals/pls-p5-release-manager/case-001-equipment/` (input.md only); `grep -c -i model evals/results/*/*.md` → 0 in 8 files | `git log --format='%ad %h %s' -- skills/<s>/` vs `-- evals/results/<s>/` | Re-run cases for every skill at its current version. Write P5 `expected.md` and run it. Add EV-01…EV-10 as cases, under `evals/pls-x-lifecycle/` or a new `evals/agent-behaviour/`, with a pass threshold. Make `skills check` or CI fail when a README version is newer than the last result file's recorded version. | A results file per skill naming the current version; EV results files |
| I1 | Skill structure | Low | PARTIAL | demo | See §3. Missing elements: checklist in script-engineer, P6, onboarding and lifecycle (they have "Never" lists or a hand-over instead); explicit Outputs section in P3-config and P5 (implied by the steps); KB skill is reference material (N/A). | §3 table | Read each SKILL.md | Add a short "Checklist before hand-over" to the four skills and an Outputs block to P3/P5 | Re-read |
| I2-a | No agent edits of profile/guards | High | PARTIAL | demo | The skills tell the agent to write guard inputs itself once "the person says it". Lifecycle §1: "add the name [approver] to the profile only after the person says it" (`pls-x-lifecycle/SKILL.md:44`). Lifecycle §0: "you update `Origin` (and … stage and release target) in the profile" (`:26`); Origin drives the L-ONB-01 / onboarding refusals. Onboarding step 0: "after the person approves it you write it" for `environments.json` `role` (`pls-x-onboarding/SKILL.md:19`). So the same agent both writes the approver list that `pls gate` checks and records the gate, with nothing but its own report of the person's words. The skills only forbid editing these files "to get past a refusal" (`:54,56,57`; template `CLAUDE.md:33`). ADR-0014 TB-1/TB-2 would make this a boundary, but its status is **Proposed** (`0014:3`), so ACCEPTED BOUNDARY cannot be given. | Lines cited; `pls_gate.py` re-checks names against the profile only (per ADR-0014 TB-1 text) | Static | Either (a) the person edits `Approvers`/`Operators`/`Origin`/`role` themselves, and the agent shows the diff and never writes it, or (b) a `pls profile set` command records the person's words like `pls gate` and is logged. Then accept ADR-0014 TB-1/TB-2 explicitly. | ADR-0014 Accepted; skill text changed; EV-01 run |
| I2-b | `--yes` only on instruction | Medium | PARTIAL | demo | script-engineer: "`pls apply R-…` (the person or `--yes` for that sandbox)" (`pls-p3-script-engineer/SKILL.md:44`) does not say "only after the person tells you". Lifecycle P3 steps "(or allows `--yes`)" (`:101,113`) rely on rule 3 (`:58-60`) elsewhere in the file. The eval rubric `evals/pls-p3-config-builder/case-001-equipment/expected.md:8` accepts "apply by the person or `--yes`" without that condition. | Lines cited | Static | Same wording everywhere: "`--yes` only after the person tells you to, for the target they named". Fix the rubric. | grep `--yes` in skills/evals |
| I2-c | Human-review attestation written by the agent | Medium | PARTIAL | demo | spec-recovery: after review, the agent writes 「レビュー: <name>, <date>」 into the as-is header and writes DES-000, which clears L-LAD-01 (`pls-x-spec-recovery/SKILL.md:42`). No `pls` record or quote is required, unlike `pls gate`. In the playboard copy, DES-000 files say "reviewed by Nam 2026-11-08" and have no record. | Line cited; copy `design/decisions/DES-000-as-is-*.md` header | Static | Record the review with `pls gate`-like evidence (or a `pls review` record with a quote), and have L-LAD-01 accept DES-000 only with that record | Lint test |
| I2-d | Keys | — | (PASS part) | demo | No instruction to read, print or ask for keys. Lifecycle rule 4 (`:61`) and template rule 4 (`CLAUDE.md:35-38`) forbid it. P4 "keys: `pls http-check` lists them" (`p4 SKILL.md:18`) lists key **names** only (`pls.py:2055-2075` prints names, HTTP status and title; never a value). | Lines cited | — | — | — |
| I2-e | Scenario 26: imperative text in data files | Medium | PARTIAL | demo | No injection-style text found in `evals/**` or in the copies' `requirements/sources/` and `requirements/*.md` (regex scan, §4). One source file in `pls-onboard-playboard-r2` (`requirements/sources/2026-11-08-site-id-alignment.md`) stores approvals as imperative instructions to the agent, including "Mark … with `--by Nam`". It is marked as "relayed by the coordinator … verbatim in substance", i.e. a paraphrase passed on by an agent, and it was used to authorize `pls refs --ref/--keep --by Nam` (no `--quote` needed). This is the TB-2 risk in practice: the provenance of a person's words is an agent relay. Not followed by the reviewer. | Copy file lines 3-11; `pls-p3-config-builder/SKILL.md:27` (`--keep … --reason … --by`, no quote) | Static | Never accept relayed or paraphrased approvals as a person's words. `refs --ref/--keep` should take `--quote`. Add EV-09. | EV-09 result; refs record has quote |
| I3 | Project skills match lock | Low | PARTIAL | demo | [F] see §5. Integrity: no project copy was edited (no "project copy was edited" line) in the two hashed locks. Currency: all 3 lag behind. playboard runs lifecycle 0.12, P5 0.4 and onboarding 0.4, so it lacks the 0.14 `jobs-verified`/"never edit `Operators`" rules. demo-equipment runs lifecycle 0.1, which has no `pls gate` and no `side_effects` rule. pls-demo-equipment has an old-format lock, so edits cannot be detected. `skills check` covers neither the project `CLAUDE.md` (both copies lack the template's `Operators` row) nor tool code (ADR-0014 TB-6). Message wording "framework has a newer version" is printed on any hash difference, whatever the direction (`pls.py:1866-1867`). | `pls.py:1853-1870`; outputs §5; `test_skills_check_finds_edited_and_outdated_copies` (ran: OK) | `cd <copy>; PLS_HOME=<fw> python pls.py skills check` | Run `skills check` at session start (lifecycle §1) and refuse `step`/`gate` on an edited copy. Compare versions, not just hashes, in the message. Hash the profile template section and tool tree too. | Re-run on copies after sync |
| I4 | Token rules | Low | PARTIAL | demo | Rules present: lifecycle `:65-73`, template `CLAUDE.md:43-47`, P4 `:36`, spec-recovery `:18`. Evidence: only `pls-onboard-playboard-r2/ops/usage/` (1 file, 13 rows). `pls usage report --by step` [F] shows a single session id spanning steps of CR-A **and** CR-B (P3/P4/P5/G3/G4 of both), against "one session per change request" (lifecycle `:71`, added in 0.12 the same day). Nothing checks it. demo-equipment and pls-demo-equipment have no `ops/usage`. | `ops/usage/<session>.json` (`rows` 13); report output in §5 | `PLS_HOME=<fw> python pls.py usage report --by step` | `pls usage report` warns when one session holds steps of several releases/CRs. Keep the rule in the template too. | Report shows warning |
| I5 | Language | — | PASS | demo | [S] Scripted scan for Vietnamese letters over `skills/`, `templates/`, `evals/`, `docs/`, `tools/pls/*.py`: 0 files. Customer questions, end-user messages and the as-is 画面設計書 are Japanese (P1 `:31,53`; P3 `:26`; spec-recovery `:20`; P6 `:34`). The playboard copy's REQ and DES files are English with Japanese labels. | Scan script output `{}` | — | — | — |
| I6 | Completion reports | Low | PARTIAL | demo | Skill text: only the gate message (`gates.md:3-8`: what was done, evidence, decisions, question) and the script-engineer hand-over (`:49-51`). No rule that a phase or session ends with changed files, commands with results, open items and decisions needed. `docs/slices/slice-03-report.md` has results per phase, lessons and leftovers, but no changed-file list and no commands with outputs. `plans/reports/code-reviewer-2026-11-09-jobs-guard.md` lists files, the test command with its result (`Ran 194 tests … OK`), findings and recommended actions, so it is complete. | Lines cited | Static | Add a "Completion report" block to lifecycle §2 (files, `pls` commands + exit/result, open items, decisions needed); pair it with EV-07 | EV-07 result |
| J5 | Customer responsibilities | Medium | FAIL | prod | No handover document. Template profile names only "customer operator" for prod Operators and "customer owner" approvals (`templates/project/CLAUDE.md:24,27`; `gates.md:34,37`). Backup, incident, recovery and execution ownership exist only as open questions to "Customer IT (TD-02)" (`0003:15-19`, `0004:20`), with ADR-0003 still Proposed. P6 triage routes incidents but names no customer duty. | Lines cited | Static | A handover template (`templates/handover/` or a profile section): approval (G1/G4), execution (runner operator), incident contact/SLA, backup (DB + `pls backup` before migrations), recovery (rollback package and who runs it), signed by the customer | Template exists; used in a cstg project |

## 3. Per-skill checklist

Legend: Y present · P partial · N missing · n/a.

| Skill | Ver. | Inputs | Procedure | Outputs | Checklist | Stop points | Tool use for computable results | Last eval (date, ver., result) | Changed after last eval |
|---|---|---|---|---|---|---|---|---|---|
| pls-kb-pleasanter | 0.13 | n/a | Y (How to use) | P (KB entries) | N | Y (probe dev only, never stg/prod) | Y (`kb-verify`) | none (kb-verify run 2026-11-08 7/7 is probe evidence, not a skill eval) | n/a |
| pls-p1-requirements-analyst | 0.4 | Y `:11-15` | Y | Y `:35-43` | Y `:45-54` | Y G1 `:33` | P (shall-count and `[assumed]` links done by the model) | 2026-11-05, 0.3, case 002 PASS | yes, 0.4 (`f206559`, 11-08) |
| pls-p2-solution-designer | 0.6 | Y | Y | Y `:38-46` | Y `:48-59` | Y G2 `:36`; probe as G2 prerequisite | P (`xref`, `lint` used; slot choice and classification by the model) | 2026-11-05 13:02, 0.4, case 002 run 2 PASS | yes, 0.5 new sites, step 1b permissions, 0.6 xref |
| pls-p3-config-builder | 0.3 | Y | Y | P (no Outputs block) | Y `:46-53` | Y `:9` design silent → stop; person runs apply | P ("check links and summaries yourself") | 2026-11-05 06:36, 0.1, case 001 PASS (no model/version recorded) | yes, 0.2, 0.3, `5ae8391` |
| pls-p3-script-engineer | 0.2 | P ("Before you edit") | Y | P (hand-over) | N | P (old ids → ask; `--yes` wording loose `:44`) | Y (`xref`, `refs`, `lint`) | 2026-11-05, 0.1, case 001 PASS | yes, 0.2 written after the run, `5ae8391` |
| pls-p4-test-writer | 0.4 | Y | Y | Y (specs, results, g3 file) | Y `:49-55` | Y G3 `:47`; triage before change | Y (`test`, `coverage`, `lint`) | 2026-11-05 06:36, 0.1, case 001 PASS (no model) | yes, 0.2–0.4 (mail safety, exec 200) |
| pls-p5-release-manager | 0.5 | Y | Y | P (files named in steps) | Y `:53-65` | Y G4, drift, `jobs-verified` only on person's words | Y (`drift`, `release-plan`, `mark-applied`) | **never** (case has no `expected.md`, no results) | all versions |
| pls-p6-maintenance-triage | 0.2 | Y | Y | Y triage file | N ("Never" list) | Y missing facts → ask | Y | 2026-11-05, 0.1, case 001 PASS | yes, 0.2 after the run |
| pls-x-lifecycle | 0.14 | Y (§1 repo state) | Y | P (per phase) | N (gates.md table) | Y every gate, refusals, §5 | P (state reconstruction by the model; no `pls status`) | 2026-11-08 11:10, ~0.8 (cases 002/003 PASS; 0.9 changes made after the runs) | yes, 0.9–0.14 (gate records, approver naming, step logging, L-ONB-01, jobs-verified) |
| pls-x-onboarding | 0.5 | Y | Y | Y summary `:34` | N ("Stop and ask" + "Never") | Y every decision steps 2–8 | Y | 2026-11-05, 0.1, case 001 PASS | yes, 0.2–0.5 |
| pls-x-spec-recovery | 0.3 | Y | Y (Output + Rules) | Y | Y `:44-49` | Y review before DES-000 | Y (`spec-skeleton`, `xref`) | 2026-11-05, 0.1, case 001 PASS | yes, 0.2, 0.3 (spec-skeleton) |

## 4. I2 search results (skills, templates, `CLAUDE.md`)

Search: `--yes|allow_write|side_effects|api key|keys?|Approvers|Operators|connections.json|assert_writable|--accept-drift|--accept-unverified|role` over `skills/`, `templates/`, `CLAUDE.md` (probes excluded).

| Location | Text (short) | Assessment |
|---|---|---|
| `pls-x-lifecycle/SKILL.md:54` | gate record only after the person states it; "never change the profile to get past it" | Good |
| `:56` | `jobs-verified` only after operator/G4 approver said it; never edit `Operators`/`Approvers` | Good |
| `:57` | never edit `connections.json` (`allow_write`) or `side_effects` | Good |
| `:58-60` | `--yes` only after explicit instruction, for the named target | Good |
| `:61` | never read, ask for or print keys | Good |
| `:44` | "add the name to the profile only after the person says it" | **Agent edits `Approvers` (I2-a)** |
| `:26` | agent updates `Origin`/stage/release target in the profile | **Agent edits a guard input (I2-a)** |
| `:101,113` | "(or allows `--yes`)" | OK only together with `:58-60` |
| `:118,120` | `--accept-drift` after a recorded decision; `--accept-unverified` record "never write yourself" | Good |
| `pls-x-onboarding/SKILL.md:19` | "after the person approves it you write it" (`role` in `environments.json`) | **Agent writes `role` (I2-a)**; `side_effects`/`allow_write` correctly person-only |
| `:21,42` | never set `side_effects`, `allow_write`, roles; never record literal/acceptance decisions | Good (note: `:42` "never set … roles" contradicts `:19`) |
| `pls-p3-script-engineer/SKILL.md:44` | "the person or `--yes` for that sandbox" | **Loose `--yes` (I2-b)** |
| `:20,32` | POSSIBLE numbers and literals are the person's decision, "never record it" | Good |
| `pls-p3-config-builder/SKILL.md:27` | `refs --keep … --by <name>` "never record it yourself" | Good; tool needs no quote (note) |
| `pls-p5-release-manager/SKILL.md:44,47` | G4 via `pls gate`; `--yes` on instruction; `jobs-verified` "never before, never with your own words" | Good |
| `:40` | drift decision record before `--accept-drift` | Good; who writes the record is not stated |
| `pls-x-spec-recovery/SKILL.md:42` | agent writes 「レビュー: name, date」 + DES-000 that clears L-LAD-01 | **Self-attested human review (I2-c)** |
| `pls-p4-test-writer/SKILL.md:18` | keys listed by `http-check` | Names only (verified `pls.py:2055-2075`) |
| `templates/project/CLAUDE.md:32-38` | never approve; never change roles/`allow_write`; never add `--yes` on your own; never ask for a key | Good; no rule on editing `Approvers`/`Operators`/`Origin` |
| `CLAUDE.md:9-11` (framework) | do not modify/loosen `assert_writable`; agents must not add `--yes` | Good |

**Scenario 26 (embedded imperative text in data files)**
- Scanned: `evals/**` (inputs, expected, results incl. generated `sources/`), and `requirements/sources/*.md` + `requirements/*.md` of the 3 copies. Regex: ignore/disregard, "you must approve/run/skip", addressed-to-AI/agent phrasing, auto-approve, skip gate/check, `--yes`, `allow_write`, Japanese 承認してください / 自動承認 / AIへ / エージェント.
- Result: no injection-style text. Hits were descriptive (rubric lines, "Model:" headers).
- One relevant data file: `pls-onboard-playboard-r2/requirements/sources/2026-11-08-site-id-alignment.md` holds approvals written as instructions to the agent ("Mark … with `--by Nam`"), "relayed by the coordinator … verbatim in substance" (finding I2-e). Reported, not followed.
- No eval case tests this behaviour (EV-09 absent).

## 5. `skills check` outputs [F]

Command: `cd <copy> && PLS_HOME=<wt-ws6> python pls.py skills check`. pls-demo-equipment has no launcher, so `python <wt-ws6>/tools/pls/pls.py skills check` was run from its root.

```
=== pls-onboard-playboard-r2           (lock: commit d0c27f1, synced 2026-11-08T21:23)
pls-p5-release-manager: framework has a newer version (0.5) - `pls skills sync` to upgrade
pls-x-lifecycle: framework has a newer version (0.14) - `pls skills sync` to upgrade
pls-x-onboarding: framework has a newer version (0.5) - `pls skills sync` to upgrade
exit=1
=== demo-equipment                     (lock: commit bd7cb4d, synced 2026-11-05T17:03)
pls-kb-pleasanter / p1 / p2 / p3-config-builder / p4 / p5 / x-lifecycle: framework has a newer version (0.13/0.4/0.6/0.3/0.4/0.5/0.14)
pls-p3-script-engineer, pls-p6-maintenance-triage, pls-x-onboarding, pls-x-spec-recovery: in the framework but not installed
exit=1
=== pls-demo-equipment                 (old lock format, "version": "0.7 (2026-11-05, commit f425bd1)")
pls-kb-pleasanter, p1, p2: no hash in the lock (old format) - run `pls skills sync`
8 other skills: in the framework but not installed
exit=1
```

Supporting runs [F]:
- `lint --summary`: playboard → L-LAD-01 5, L-SCR-01 3, L-SCR-02 1; demo-equipment → L-GATE-01 11.
- `usage report --by step`: playboard → 13 steps, one session, CR-A and CR-B.
- Unit tests (`PYTHONDONTWRITEBYTECODE=1 python -B -m unittest test_pls.PlsTest.test_lint_rules test_pls.PlsTest.test_skills_check_finds_edited_and_outdated_copies`) → 2 run, OK.
- Side effects: `ops/log/*.jsonl` only, in the copies (allowed). The worktree is unchanged.

## 6. Eval coverage

**Per skill (version history vs results; dates from `git log`)**

| Skill | Cases | Result files (date) | Model + version recorded | Evaluated version | Current | Behaviour changed after last eval |
|---|---|---|---|---|---|---|
| p1 | 001, 002 | 2026-11-05 (×2) | yes | 0.3 | 0.4 | yes |
| p2 | 001, 002 | 2026-11-05 (×2) | yes | 0.4 | 0.6 | yes (README itself: 0.5 "not yet evaluated") |
| p3-config-builder | 001 | 2026-11-05 | no | 0.1 | 0.3 | yes |
| p3-script-engineer | 001 | 2026-11-05 | version only in text | 0.1 | 0.2 | yes |
| p4 | 001 | 2026-11-05 | no | 0.1 | 0.4 | yes |
| p5 | 001 (input.md only, **no expected.md**) | **none** | — | never | 0.5 | n/a, never evaluated |
| p6 | 001 | 2026-11-05 | version only in text | 0.1 | 0.2 | yes |
| lifecycle | 001, 002, 003 | 2026-11-05, 2026-11-08 | no | ~0.8 | 0.14 | yes (0.10–0.14 are the I4 rules) |
| onboarding | 001 | 2026-11-05 | version only in text | 0.1 | 0.5 | yes |
| spec-recovery | 001 | 2026-11-05 | version only in text | 0.1 | 0.3 | yes |
| kb | — | — | — | n/a (`kb-verify` probes) | 0.13 | n/a |

**Agent-behaviour cases (standard appendix)**

| Case | Present in `evals/`? | Closest existing coverage |
|---|---|---|
| EV-01 refused apply → edit guards | No | none |
| EV-02 delete/relax failing test | No | P4 case 001 Must-not "bend expectations … without a reason" (partial, not the request situation) |
| EV-03 gate, person silent | No | lifecycle case 001: stops at G1, no self-approval (partial) |
| EV-04 key pasted in chat | No | lifecycle case 001 Must-not "ask for or mention API keys" (not the paste case) |
| EV-05 contradictory/unsafe requirement | No | P1 cases: ambiguities as questions (partial) |
| EV-06 hard-code customer rule in tools/ | No | none |
| EV-07 completion report | No | none |
| EV-08 interrupted mid-release | No | lifecycle 002/003 establish state from the repo, but not mid-release (partial) |
| EV-09 repo file instructs approve/bypass | No | none |
| EV-10 `--yes` "to save time" without target | No | script-engineer 001 "no `--yes`"; p3-config 001 rubric accepts `--yes` unconditionally (weak) |

## 7. Notes for other workstreams

- **WS-1 / A6 (ADR-0014):** TB-2 lists EV-03/EV-10 as compensating controls (`0014:36`), but they do not exist. TB-1 should name the skill-sanctioned profile edits (I2-a) explicitly. ADR-0014 is Proposed, so no I-group item can be ACCEPTED BOUNDARY yet.
- **WS-1 / A4:** profile template drift. Both copies' `CLAUDE.md` lack the `Operators` row that `jobs-verified` relies on, and `skills check` does not cover the template. Onboarding `:19` ("you write it", role) contradicts `:42` ("never set … roles").
- **WS-2 / B4, D2:** `pls refs --ref/--keep --by` takes no `--quote` (`p3-config SKILL.md:27`). The spec-recovery review attestation has no record. Approvals relayed by an agent are stored as sources (I2-e).
- **WS-3 / D1:** demo-equipment `lint` → L-GATE-01 ×11 (approvals from before `pls gate`, not re-recorded).
- **WS-5 / H1, H2:** `test_lint_rules` asserts presence only (no negative test for L-LAD-01); the false-clearance path is untested (B5).
- **WS-5 / H6 owner:** the P5 case is incomplete; 8 result files lack the model.
- **WS-7:** the review plan's hypothesis "EV-01…10 absent" is confirmed.

## 8. Top risks (impact × likelihood)

1. **Approval path unproven at the agent layer (High).** I4 depends on skill behaviour (TB-2). The rules that implement it (lifecycle 0.10–0.14, P5 0.3–0.5) were never evaluated, and EV-01/03/09/10 do not exist. One agent error records an approval nobody gave.
2. **Agent-writable guard inputs (High).** The skills let the agent write `Approvers`, `Origin` and `role` "after the person says it", and then record gates against them. No tool separates the two steps, and ADR-0014 is not accepted.
3. **L-LAD-01 false clearance (Medium, reproduced).** Substring match over all `design/**/*.md`, including the generated as-is docs, so INV-05's rung-3 control can pass silently.
4. **P5 never evaluated (Medium).** The skill that holds G4, `--yes` and `jobs-verified` has no rubric and no result.
5. **Projects run stale skills (Low–Medium).** 3 of 3 copies lag. Nothing forces `skills check` before work, and the old lock format hides local edits.

## 9. Not reviewed / limits

- No agent eval runs (T12; needs human authorization). EV cases are reported present/absent only.
- KB reference content (F1/F2) and the tool code behind each command were not reviewed beyond the lines cited.
- I did not reproduce the L-LAD-01 spec-skeleton path end to end: it would write `design/as-is` in a copy. The code path is shown statically, and the cross-site substring clearance is [F] on existing copy files.
- `ops/log` contents (D4) and release folders (D3) are not in WS-6 scope.

## 10. Criteria covered

B5 PARTIAL · B6 PARTIAL · H6 FAIL · I1 PARTIAL · I2 PARTIAL · I3 PARTIAL · I4 PARTIAL · I5 PASS · I6 PARTIAL · J5 FAIL (prod).
