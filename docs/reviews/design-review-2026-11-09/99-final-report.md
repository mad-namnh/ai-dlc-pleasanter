# Design review 2026-11-09 — final report (WS-7: evidence verification and verdict)

| Item | Value |
|---|---|
| Standard | `docs/review-criteria.md` v2.1 (§2 statuses, §5 format, §6 final report, §6.8 verdict rule, §7 independence) |
| Plan | `docs/reviews/design-review-2026-11-09/00-review-plan.md` (WS-7 row; Deliverables 7, 8) |
| Reviewed commit | `10c328a62efd3e7f7598d0b2e4f17ca13c4e3226` (= planning commit `782116b` + docs only: `git diff --stat 782116b 10c328a` touches 4 docs files, no code) |
| Trust boundaries | `docs/adr/0014-trust-boundaries.md` — **Proposed**, not accepted by Nam |
| Inputs | WS reports `ws-1-architecture.md` … `ws-6-skills.md` (in repo, commits `bcac7c8`…`2e3a98f`) |
| Reviewer | independent AI agent, fresh context; did not write the code or the WS reports |
| Environment | Windows 11 Pro 10.0.26200 · Python 3.12.10 (+ isolated 3.10.21 from WS-5) · node v24.19.0 · own detached worktree `wt-ws7` (removed after the review) |
| Safety | no real Pleasanter / URL contacted (fake server 127.0.0.1 only); no env vars or keys printed; no repo file changed; nothing committed |
| Labels | **[R]** runtime-verified by WS-7 (test re-run or new probe) · **[S]** static re-read at `10c328a` |
| WS-7 artefacts | `review/ws7-out/` (suite log, re-run logs, `review_ws7_h5.py` probe + output, `e1-rerun.json`) |

---

## 1. Executive summary

**Criteria reviewed: 65** (A1–J5). The plan and the request say "66"; the standard has 65 rows (A6 + B11 + C11 + D6 + E4 + F4 + G6 + H6 + I6 + J5; `grep -cE "^\| [A-J][0-9]+ \|" docs/review-criteria.md` → 65). No criterion is missing.

**Status counts (primary status, one per criterion, as reported by each WS):**

| Status | All | demo (55) | cstg (4) | prod (6) |
|---|---|---|---|---|
| PASS | 5 (C2, E1, F4, G3, I5) | 5 | 0 | 0 |
| PARTIAL | 31 | 31 | 0 | 0 |
| FAIL | 28 | 19 | 4 (B10, C8, C10, D6) | 5 (D5, J1, J2, J4, J5) |
| ACCEPTED BOUNDARY | 0 | 0 | 0 | 0 |
| NOT VERIFIABLE | 1 (J3) | 0 | 0 | 1 |
| NOT APPLICABLE | 0 | 0 | 0 | 0 |

With the two WS-7 disputes (§2.3) applied: PASS 4, PARTIAL 31, FAIL 29 (F4 → PARTIAL, G2 → FAIL). No verdict changes either way.

**Verdict:** `demo` **NOT READY** · `cstg` **NOT READY** · `prod` **NOT READY** (§8).

**Critical (criterion severity Critical, open):** B10 FAIL (cstg — G4 not bound to payload / target), J2 FAIL (prod — no verifiable package), J1 FAIL / J3 NOT VERIFIABLE (prod — no customer-side runner), C1 FAIL (demo — guard placement: `steps[]` bypass, `pls test` on stg without G4, no per-site re-validation), B3 / B4 / B7 / C4 PARTIAL (demo — Critical-class criteria with High/Medium open items).

**High findings (sub-findings):** WS2-F1 (later rejection loses to earlier approval), WS2-F3 (no secret check at `unpack` / `release-plan`), WS2-F7 + WS3-F7 (plan `steps` write sites outside the env, incl. shared dev sites), WS3-F1 (failed restore reported `rolled-back`), WS3-F2 (timeout after write → traceback, no record, no restore), WS3-F3 + WS4-F1 (`mark-applied` launders failed / rolled-back / drifted state into an applied baseline), WS3-F4 (apply evidence overwritten), WS3-F6 (sandbox shared-write check only at create), WS4-F2 (permissions/title not read back), WS4-F3 (duplicate list keys hide changes — present in real config), WS4-F4 (`${env:x}` substring rewrite), WS4-F7 (interrupted bootstrap duplicates sites), G4 (runner parity: HTTP 500 → `pass`, `as_key` ignored, restore aborts), I2-a (skills let the agent write `Approvers`/`Origin`/`role`), A6 / D5 (trust boundaries incomplete / not tamper-evident).

---

## 2. Findings

### 2.1 WS-7 criteria (H1, H2, H3, H5, J1, J3, J4)

| ID | Criterion | Severity | Status | Stage | Finding | Evidence (file:line, test, command output) | Reproduction | Proposed fix | Verification |
|---|---|---|---|---|---|---|---|---|---|
| H1 | Every guard in B and C has a positive and a negative test | Medium | **FAIL** | demo | Mapping in §2.2. 9 guards have both directions in the framework suite (allow_write, role spellings via apply, G4 on stg, G3 for release-plan, UpdatedTime preflight, side effects, sandbox shared `per_site`, typed confirmation, gate writer). Missing negative test [S/R]: L-DEP-01 refusal and transport key-presence check (no hit for `L-DEP`/`misses` in `tests/test_*.py`); L-LAD-01 (only presence asserted, `test_pls.py:84-90`); prod refusal of `bootstrap`, `test`, `kb-verify` (only `apply` and `bootstrap-plan`: `test_write_guards.py:147-155`, `test_pls.py:617-622`); failed restore (`test_http.py:31` `fail_restore_on` declared, never used by `Fake.handle`); `jobs.verified` on use; `mark-applied` on wrong status / foreign export; timeout after write. Guards that do not exist have no tests by construction (B10 digest, per-site re-validation, `steps` vs `per_site`, secret check at unpack/plan). Static write lock is heuristic (literal endpoint, owner `client/c/self`: `test_write_guards.py:82-83,99`) | `grep -n fail_restore_on tests/*.py` → only `test_http.py:31` [R]; test inventory (214 names) [S]; WS-2/3/4 reviewer suites exercise the uncovered cases (§7) | grep as stated | One negative test per refusal message (`REFUSED`/`Fail(`): generate the list from the code and fail the suite when a refusal has no test; add the missing ones above | refusal-to-test map has no empty cell |
| H2 | Tests assert resulting state and records, not only exit codes | Medium | **PARTIAL** | demo | AST scan of 214 tests: **206** assert state (fake-server site contents, written files, records, messages); **8** assert only an exit code (`test_http_check_accepts_a_restricted_key_without_access`, `test_log_failure_never_breaks_a_command`, `test_drift_detects_ui_change`, `test_no_drift_across_envs_when_equal`, `test_slots_missing_ledger_refuses_plan`, `test_script_bodies_keep_crlf`, `test_unverified_component_only_in_git_refuses_too`, `test_read_only_tests_and_sites_without_mail_are_not_blocked`) [R]. One is **vacuous**: `test_script_bodies_keep_crlf` (`test_pls.py:760-765`) asserts `diff` rc 0, but `diff` always returns 0 (`pls.py:2903-2905`) [S] (confirms WS-5 G2-c). Failure paths assert the transport status only: no test reads `apply-log.json` or `plan.json` status after a failure (`grep apply-log tests/test_*.py` → 0) [R]; `test_apply_release_ok_and_rollback_on_failure` (`test_http.py:184-197`) never checks restore results — which is why WS3-F1/F4 went unnoticed | AST scan (counts above); lines cited | AST scan script in this report's run log | Assert records (apply-log, plan status, gate files, run-log event) in every failure test; replace the S7 assertion with a difference count | re-run scan: 0 exit-only tests on guard/failure paths |
| H3 | Every escaped defect has a regression test that fails on the old code | Medium | **FAIL** | demo | Spot-checks pass [R]: reverting the code of `63f1f45` (secret detector) makes `test_adopt.test_secret_detector_flags_literals_not_concatenation` fail; reverting `1a5f67a` (gate clock ordering; commit has no test change) makes `test_gate.test_records_are_never_overwritten_and_the_last_one_wins` fail. Violations: `993eae1` (cp932 console crash, TD-12) has no regression test in the suite (only WS-5's reviewer test); the S7 CRLF regression test cannot fail (H2); B9 trace (WS-1 §8) lists escaped defects without any artefact (D7 post-deploy save regression, D3-review S6 coverage-on-empty, audit F-08 L-LAD-01 substring — the latter reproduced as a false clearance by WS-6 B5). 17 `fix` commits: 3 without a test change (`1a5f67a` covered by an existing test, `a060b6c` KB probe, `993eae1` none) | `git diff <fix>^ <fix> -- <code> \| git apply -R` + module run: `test_adopt` FAILED (failures=1), `test_gate` FAILED (failures=1) [R]; `git log --grep=^fix` table [R] | as stated, on a worktree | Rule: every `fix(pls)` commit changes a test that fails on its parent (check in CI / `skills check`-style script); add cp932 and CRLF-count tests; trace B9 items | parent-commit run of each new test fails |
| H5 | Skipped, failed and not-run tests reported separately; `pass-api-only` visible in coverage | Medium | **FAIL** | demo | Framework suite: 214 run, 0 skipped; no skip decorators (`grep skipIf\|SkipTest` → none); node-less syntax check prints a warning (`test_pls.py:158`) [R]. `pls test` prints and stores each status (`pass`, `pass-api-only`, `fail`, `error`) (`pls.py:2278-2288`, `pls_http.py:349-354`) [S]. **Coverage hides them** [R]: `coverage()` counts `pass-api-only` as passed and its row has no api-only field (`pls.py:749,752-753`; CLI prints only `tests=passed/total`, `pls.py:2893-2895`); a failed test and a never-run test give identical rows; empty `traceability.json` → `ok: True`; a later result file of another env overrides a failure (`pls.py:742-744`, last file wins). No existing test calls `coverage()` (only `config_path_exists`, `test_pls.py:725`) | `review_ws7_h5.py` (4 probes, each asserts the observed behaviour): `test_pass_api_only_is_counted_as_pass_and_not_shown`, `test_failed_and_not_run_are_indistinguishable`, `test_empty_traceability_is_ok`, `test_later_result_file_overrides_failure_of_other_env` — Ran 4, OK (= findings reproduced) | `python -m unittest tests.review_ws7_h5 -v` in a worktree | Row fields `passed`, `api_only`, `failed`, `error`, `not_run` per env; `covered` only when all linked tests pass in the target env; `pass-api-only` shown as `covered (api-only: N)` and not sufficient for a UI requirement unless the REQ says so; empty traceability → GAP | probes invert |
| J1 | Customer-side runner path (ADR-0003) runs without an AI agent, with the same release package | Critical | **FAIL** | prod | No runner and no package format exist [S]: ADR-0003 Decision "*(Not decided)*" (`docs/adr/0003-production-deploy.md:3,41-43`), TD-02 open (`docs/tech-debt.md:8`); `release-plan` for prod only prints a note (`pls.py:1020-1021`). ADR-0003's 2026-11-05 note says option A "can run exactly" `pls apply` in the customer network, but `assert_writable` refuses `role: prod` unconditionally (`pls_http.py:90-96`) — the only described path is closed by design. Absence of the required path is evidence of non-compliance, not missing evidence → FAIL, not NOT VERIFIABLE. Method-L dry run impossible | lines cited | read ADR-0003, `pls_http.py:90-96` | Decide ADR-0003 (option B/C package + `pls verify` stdlib command); design how a customer runner obtains a prod-capable `apply` without loosening the I3 guard for agents (e.g. separate entry point that refuses unless run with a customer-held key and a verified package) | method-L dry run by a person: package → verify → apply on dev |
| J3 | Production runner has no AI credentials and no AI-triggered path | Critical | **NOT VERIFIABLE** | prod | Nothing to inspect: the runner does not exist (J1). What is verifiable today: the HTTP transport refuses prod for every write command [R by WS-2 `test_s06_…`, re-run by WS-7: Ran 24 OK]; `pls` holds no AI credential (only a detector pattern `pls.py:80`) [S]. Not covered: browser runner (no guard, TB-7) — a person could inject it in a prod session; HANDOFF.md:86 says *agents* use the runner | `pls.py:80`; `pls_http.py:90-96`; `HANDOFF.md:86`; `docs/adr/0014-trust-boundaries.md:41` | — | Runner design must state its inputs (package only), credentials (customer key only), and have a test that it runs with no network route to an AI endpoint | review of the runner once built |
| J4 | Production-blocking tech debt resolved or accepted by Nam in writing | High | **FAIL** | prod | `docs/tech-debt.md`: TD-01 (ownership zones), TD-02 (prod deploy method), TD-04 (gateway HTTP) have deadline "before (first customer) production (deploy)", TD-03 "before receiving real customer configuration" — all open, interim assumptions only, none accepted by Nam [S]. Review findings that block prod are not in the register at all: B10/J2 digest, D5 record protection, J5 customer responsibilities, ADR-0014 "gaps that are not boundaries" (`0014:44-48`), WS-1 H4 lists 17 earlier-review items missing | `docs/tech-debt.md:7-10`; `docs/adr/0014-trust-boundaries.md:44-48` | read | Add a TD line per prod-blocking finding with "before cstg"/"before prod" deadline; Nam signs off each (accept with control, or fix) | register lists every prod-stage FAIL with an owner and a written decision |

### 2.2 H1 guard → test map (framework suite only; reviewer tests excluded)

| Guard (criterion) | Code | Positive test | Negative test | Gap |
|---|---|---|---|---|
| role dev/stg + `allow_write` (C1, B3) | `pls_http.py:90-96` | `test_http.test_apply_release_ok_and_rollback_on_failure` | `test_write_guards.test_apply_bootstrap_test_kbverify_send_nothing_without_allow_write`, `test_http.test_write_guard` | prod only for `apply` (`test_prod_is_never_written`, `test_cli_apply_refused_for_prod`) and `bootstrap-plan` |
| G4 on stg (C1) | `pls.py:2121-2125,2195-2198` | `test_gate.test_dev_needs_no_gate` | `test_apply_to_stg_needs_g4_of_that_release`, `test_bootstrap_on_stg_needs_g4_naming_it` | record content / env not checked (B10) |
| G3 for release-plan | `pls.py:1023-1027` | many plan tests | `test_release_plan_for_stg_needs_g3` | — |
| gate writer (B4) | `pls_gate.py:143-171` | `test_record_checks_approver_gate_quote_and_scope` | same + `test_require_rechecks_the_approver`, `test_no_approver_in_profile_means_ask` | ordering by local date (WS2-F1) untested |
| `jobs-verified` writer / use (B4) | `pls.py:804-827`, `785` | `test_jobs_verified_accepts_an_operator_…` | same (writer) | use-side re-check: none |
| L-DEP-01 / key presence (B2) | `pls.py:987-989`; `pls_http.py:144-146` | plan tests | **none** | WS3-F10 |
| drift refusal + decision record (B2) | `pls.py:1016-1019` | `test_release_lifecycle_drift_against_last_release` | `test_release_id_is_used_once_and_drift_decision_must_exist` | record content not checked |
| `UpdatedTime` preflight (B2, C9) | `pls_http.py:182-187` | `test_apply_release_ok_…` | `test_apply_refused_when_live_changed` | per-site window (WS3-F5) |
| read-back status (B11) | `pls.py:2164-2177,2811-2843` | `test_apply_with_canonicalisation_differences_becomes_the_baseline` | **none** (wrong status / foreign export) | WS3-F3, WS4-F1 |
| L-SEC-01 (B7) | `pls.py:538-540,604-606,1268` | `test_secret_detector_flags_literals_not_concatenation` | same; `test_secrets_refuse_before_anything_is_written` | not at unpack/plan (WS2-F3) |
| L-LAD-01 (B5) | `pls.py:620-621` | `test_lint_rules` (presence) | **none** | WS-6 B5 false clearance |
| side effects (C2) | `pls_side_effects.py` | `test_release_without_mail_changes_is_not_affected`, `test_apply_without_job_changes_passes_while_jobs_are_unknown` | 20+ refusal tests | — |
| typed confirmation (C4) | `pls.py:2026-2038` | `--yes` paths | `test_cli_apply_needs_confirmation` | piped stdin accepted |
| shared / own sites (C7) | `pls.py:2128-2133`, `1528-1535` | `test_sandbox_lifecycle_never_touches_shared_dev` | `test_shared_sites_and_stale_plans_are_never_written`, `test_sandbox_refuses_a_copy_that_writes_to_a_shared_site` | `steps[]`, late scripts (WS3-F6/F7) |
| partial failure + restore (C6, C8, C11) | `pls_http.py:189-211` | `test_apply_release_ok_…` | `test_restore_restores_permissions_and_survives_errors` (HTTP error only) | failed restore, timeout: **none** |
| malformed input (C3) | loaders | — | `test_index_must_be_utf8_with_safe_names`, `test_effects_default_unknown_and_reject_unknown_values`, `test_apply_refuses_a_hand_broken_jobs_record`, `test_broken_decisions_file_is_a_clear_error` | plan / env / connections / gates: none (WS3 matrix: 25 tracebacks) |

### 2.3 Evidence check of the other workstreams

**Every PASS re-verified** (and PASS sub-parts):

| Criterion (WS) | WS-7 check | Result | WS-7 view |
|---|---|---|---|
| C2 (WS-3) | re-ran `test_side_effects` (Ran 33 OK) and `test_sandbox_merge` (Ran 14 OK) [R]; independent probes on `pls_side_effects`: `Unknown`, string, `off` refused; `null` → unknown; `cautious(sink/disabled, unknown/live)` → unknown/live; tie → base; jobs/mail `unknown` refusals fire [R]; re-read `pls_side_effects.py:39-60,300-332`, `pls.py:835-839` and ADR-0010:45-67 (refusal only when jobs declared / mail elements changed — matches ADR) [S] | confirmed | **agree PASS**. Note: "only a person changes the state" is not code-enforced — it rests on TB-1 (Proposed); skills keep `side_effects` person-only (WS-6 §4) |
| E1 (WS-4) | re-ran `ws4-out/e1_determinism.py` into `ws7-out/e1-rerun.json` [R] | 0 config / 0 pack differences on 3 copies (7 / 8 / 269 files; 2 / 2 / 23 packs); release-plan twice: 8 files, 0 differences after masking the release id | **agree PASS** |
| F4 (WS-4) | re-ran `review_ws4_determinism` (Ran 24, 17 fail — identical to WS-4) [R]; `test_canonicalize_keeps_unknown_fields_…`, `test_null_empty_…` ok; `test_scope`, `test_version` re-run OK [R]; re-read `pls.py:393-400` [S] | evidence for kept unknown fields / unknown states holds | **WS-7 dispute → PARTIAL** (below) |
| G3 (WS-5) | re-ran `review_ws5_offline_run.py` (Ran 214 OK, `non-loopback attempts: none`) [R] | confirmed | **agree PASS** |
| I5 (WS-6) | own scan of the worktree (`.md .py .js .mjs .json .txt`) for Vietnamese-specific letters → `{}` [R] | confirmed | **agree PASS** |
| G2-a, G2-c (WS-5, sub-parts) | re-ran `review_ws5_windows` (Ran 10: 8 ok, 2 FAIL = BOM gate record, CRLF `site.json`) [R] | identical to WS-5 | agree on sub-parts; see dispute on G2 |
| G5-a (WS-5, sub-part) | not re-run (timing; writes a release folder in a copy); `bench/results.json` read [S] | plausible | accept |

**At least one FAIL per workstream re-verified:**

| WS | Criterion | WS-7 check | Result |
|---|---|---|---|
| WS-1 | A3 | ADR headers re-read: 0001, 0002, 0003, 0007, 0008, 0009, 0010, 0011, 0013 Proposed while 0001/0007–0011/0013 are implemented and tested [S]; A6 claims: `templates/project/.gitignore:1` `.pls/`, no force-push rule (`grep` → 0 outside the review), `pls.py:1959,1968,1973` `allow_write: True` / `role: dev` [S] | confirmed |
| WS-2 | B10, C1 | re-ran `review_ws2_security` (Ran 24 OK — each test asserts the observed unsafe behaviour) and `review_ws2_runner.mjs` (3 pass) [R]; read `test_s11_payload_altered_after_g4_is_applied` (asserts stg site Title = tampered value); `pls_gate.py:174-188` [S] | confirmed |
| WS-3 | C8, C10, C7, C9 | re-ran `review_ws3_recovery` (Ran 22: 5 pass / 17 fail — identical); `test_s16` message `'rolled-back' unexpectedly found … a failed restore is reported as rolled-back`; `pls_http.py:189-211` [R/S] | confirmed |
| WS-4 | E2 | `test_duplicate_list_keys_do_not_hide_a_difference` FAIL; `pls.py:393-397` keys by `ColumnName`/`Name`/`Id` into a dict [R/S] | confirmed |
| WS-5 | G1, G4 | 3.10.21 `ast.parse` of every `tools/pls/*.py` → only `pls_adopt.py` fails (line 94: backslash in f-string expression); `docs/setup.md:15` "Python 3.10+" [R]; `review_ws5_runner_parity.mjs` 0 pass / 3 fail [R] | confirmed |
| WS-6 | H6, B5 | `evals/pls-p5-release-manager/case-001-*/` holds only `input.md`; no P5 results dir; `grep -rl EV-0 evals` → none [R]; `pls.py:572,620` L-LAD-01 substring over all `design/**/*.md` [S] | confirmed |

**WS-7 disputes** (other workstreams' statuses are **not** changed; listed with evidence for Nam's decision):

| # | Criterion | WS status | WS-7 view | Evidence | Impact on verdict |
|---|---|---|---|---|---|
| D-1 | F4 (WS-4) | PASS | **PARTIAL** | An uncertain Pleasanter behaviour — uniqueness of list items by `ColumnName`/`Name`/`Id` — is handled non-conservatively: duplicates silently collapse to the last (`pls.py:393-397`), contradicted by real config of the largest project copy (WS-4 `e2_dup_demo.py`: 3/3 sites, non-last change → 0 differences). WS-4 counted it under F2/E2, but F4 asks exactly for conservative handling of uncertain behaviour; a PASS needs no counter-evidence (§1 "lack of evidence is never a PASS" — here there is counter-evidence). Also `0`≡`False` equality (WS4-F14) | none (demo already NOT READY) |
| D-2 | G2 (WS-5) | PARTIAL | **FAIL** | WS-5's own sub-row G2-d is FAIL (Medium): `wj()` writes OS-native newlines (`pls.py:117-119`) and `config/** releases/**` are `-text`, so a cross-OS run rewrites whole files; framework repo has no `.gitattributes`. G2 lists "CRLF neither creates false diffs nor whole-file git changes" as a requirement — evidence shows it violated; §2 PARTIAL is for missing parts, FAIL for violated ones | none |

**Consistency observation (not a per-row dispute):** several workstreams use PARTIAL where a sub-part is *shown violated* by a test (e.g. B3 spike path WS2-F4, B4 WS2-F1, B11, C6, C9, I2). Under §2 these read closer to FAIL. Re-classifying them would add FAILs only at stages that are already NOT READY; recommend the standard v2.2 says "a violated sub-part makes the criterion FAIL; PARTIAL only for unverified/missing parts".

### 2.4 Consolidated findings by criterion (other workstreams; sub-finding IDs refer to the WS reports)

| ID | Sev. | Status | Stage | WS | Key sub-findings / evidence pointer |
|---|---|---|---|---|---|
| A1 | Low | PARTIAL | demo | 1 | `setup`/`principals`, L-ENV-01/L-REF-02 unmapped; phantom `pls deploy`, L-SLOT-02 |
| A2 | Medium | FAIL | demo | 1 | gate model, Operators, onboarding refusal, setup profile, env overrides, distribution — no ADR |
| A3 | Medium | FAIL | demo | 1 | 7 ADRs Proposed but enforced; ADR-0012 edited after acceptance; bulk upsert untested |
| A4 | Medium | FAIL | demo | 1 | 7 rule conflicts (gate location, migration order, runner on stg, write rule, log failure, versions, I7 claim) |
| A5 | Low | FAIL | demo | 1 | app name + adopted-site id in core (identifiers only, no data) |
| A6 | High | PARTIAL | demo | 1 | ADR-0014 Proposed; 6 boundaries missing; 3 compensating controls false |
| B1 | High | FAIL (+ live part NOT VERIFIABLE) | demo | 4 | WS4-F1, F2, F3; method-L scenario WS-4 §6 |
| B2 | High | PARTIAL | demo | 3 | WS3-F5, F10 |
| B3 | Critical | PARTIAL | demo | 2 | Python paths refuse prod [R]; runner TB-7; spike WS2-F4; WS2-F9 |
| B4 | Critical | PARTIAL | demo | 2 | WS2-F1 (High), F2; authenticity TB-1/TB-2 |
| B5 | Medium | PARTIAL | demo | 6 | L-LAD-01 substring false clearance [F] |
| B6 | Medium | PARTIAL | demo | 6 | shall-count, link checks, state reconstruction left to the model |
| B7 | Critical | PARTIAL | demo | 2 | WS2-F3 (High); scans 0 matches |
| B8 | Medium | PARTIAL | demo | 4 | WS4-F11 |
| B9 | Medium | PARTIAL | demo | 1 | 20 items without artefact; register stale |
| B10 | Critical | FAIL | cstg | 2 | no digest; payload / env / `steps` edits after G4 applied [R] |
| B11 | High | PARTIAL | demo | 3 | WS3-F3 |
| C1 | Critical | FAIL | demo | 2 | WS2-F5, F6, F7, F8; `PLS_CONNECTIONS` (TB-1) |
| C2 | High | PASS | demo | 3 | verified by WS-7 |
| C3 | High | FAIL | demo | 3 | WS3-F8, F9, F12 (25 tracebacks, 3 writes with damaged input) |
| C4 | Critical | PARTIAL | demo | 2 | piped stdin = confirmation; WS2-F5 |
| C5 | Low | PARTIAL | demo | 3 | WS3-F11 |
| C6 | High | PARTIAL | demo | 3 | WS3-F2; runner restore aborts |
| C7 | High | FAIL | demo | 3 | WS3-F6, F7, WS2-F7, F9 |
| C8 | High | FAIL | cstg | 3 | WS3-F1, F4 |
| C9 | Medium | PARTIAL | demo | 3 | WS3-F5; TB-8 control false |
| C10 | High | FAIL | cstg | 3 | WS3-F2; bootstrap duplicate |
| C11 | High | FAIL | demo | 3 | WS3-F1, F3, F4, F12 |
| D1 | High | PARTIAL | demo | 2 | no env / digest in records; WS2-F1; bad JSON traceback |
| D2 | High | PARTIAL | demo | 2 | agent = operator in run log; no executor in apply-log |
| D3 | Medium | PARTIAL | demo | 4 | WS4-F10 (no read-back evidence, no guarded undo) |
| D4 | Medium | PARTIAL | demo | 4 | WS4-F8 (`env: null` on 4/4 apply events) |
| D5 | High | FAIL | prod | 1 | TB-3 demo only; cited control absent |
| D6 | Medium | FAIL | cstg | 4 | WS4-F9 (fail-open, ADR-0013 vs ADR-0014 conflict) |
| E1 | Medium | PASS | demo | 4 | verified by WS-7 |
| E2 | High | FAIL | demo | 4 | WS4-F3, F2, F14 |
| E3 | High | FAIL | demo | 4 | WS4-F1, F7 |
| E4 | High | FAIL | demo | 4 | WS4-F4, F5, F6 |
| F1 | Low | PARTIAL | demo | 4 | WS4-F13 |
| F2 | Medium | PARTIAL | demo | 4 | key uniqueness, omitted top-level fields, dead `SITE_VOLATILE` |
| F3 | Medium | PARTIAL | demo | 4 | WS4-F12 (`verified_on` unused) |
| F4 | Medium | PASS (WS-7: PARTIAL, D-1) | demo | 4 | — |
| G1 | Medium | FAIL | demo | 5 | `pls_adopt.py:94` 3.12-only syntax |
| G2 | Medium | PARTIAL (WS-7: FAIL, D-2) | demo | 5 | BOM in gates; CRLF writes |
| G3 | Low | PASS | demo | 5 | verified by WS-7 |
| G4 | High | FAIL | demo | 5 | 3 parity differences; guards absent (TB-7) |
| G5 | Low | PARTIAL | demo | 5 | no `release-plan --summary`; summaries untested |
| G6 | Low | PARTIAL | demo | 5 | env vars, `allow_write` default, recovery undocumented |
| H4 | Medium | FAIL | demo | 1 | 17 earlier-review items neither closed nor in TD |
| H6 | Medium | FAIL | demo | 6 | 9/10 skills changed after last eval; P5 never; EV-01…10 absent |
| I1 | Low | PARTIAL | demo | 6 | 4 skills without checklist |
| I2 | High | PARTIAL | demo | 6 | I2-a agent writes `Approvers`/`Origin`/`role`; I2-b, c, e |
| I3 | Low | PARTIAL | demo | 6 | 3/3 copies lag; old lock format |
| I4 | Low | PARTIAL | demo | 6 | one session spans 2 CRs |
| I5 | Low | PASS | demo | 6 | verified by WS-7 |
| I6 | Low | PARTIAL | demo | 6 | no completion-report rule |
| J2 | Critical | FAIL | prod | 2 | no verifier, no digest |
| J5 | Medium | FAIL | prod | 6 | no customer-responsibility document |

### 2.5 Consistency check (Deliverable 8 items 1, 4)

- **Exactly one primary status per criterion:** 65/65; no duplicates as primary, none missing. Secondary mentions exist and are labelled (e.g. WS-3 reports C1 scenario 12 as WS2-F6 "not re-reported"; WS-3 S24 feeds D6). Format deviations: B1 carries a second status for its live part (primary = FAIL); WS-5 splits G2/G5 into sub-rows with sub-statuses (primary in its summary line: G2 PARTIAL, G5 PARTIAL); I2 has a "(PASS part)" sub-row (primary PARTIAL). Accepted as readable; v2.2 should require one row per criterion.
- **Count:** plan / request say 66 criteria; the standard has 65 (above).
- **ACCEPTED BOUNDARY:** used as primary status **0** times. Used for sub-parts, each citing an ADR-0014 row and marked "Proposed — holds only once Nam accepts it": B3 → TB-7, TB-4; B4 → TB-1, TB-2; C1(d) → TB-1; C4 → TB-2/TB-5; D2 → TB-2/TB-5; D5 (demo view) → TB-3; G4 → TB-7; C9 → TB-8 (control shown false, so not accepted); I2 → TB-1/TB-2 (explicitly not granted). Uncovered by any TB row and therefore findings: spike write paths (WS2-F4), env overrides, `file:` key paths, untrusted Pleasanter content → agent context, shared tenant resources, admin-key privilege (WS-1 A6).
- **Plan scenarios 1–26:** executed or explicitly skipped with reason across WS-2/3/4/6 (23 "not run": static only; 26 static part only). Mandatory paths (Deliverable 8 item 5) all examined.
- **Priority set** (B3, B4, B10, B11, C1, C2, C3, C8, C11, D2, H5): all evidenced; only C2 PASS.
- **Repository unchanged:** framework `git status` = `M HANDOFF.md` (pre-existing at session start, not by WS-7); reviewed code identical between `782116b` and `10c328a`.

---

## 3. Not verifiable (Deliverable 7, updated)

| Criterion / part | Missing method or evidence | Change since planning |
|---|---|---|
| B1 live part | method L: person runs apply → export → mark-applied on MADLAB dev (scenario written: WS-4 §6, 10 steps; step 9 predicts WS4-F2) | still open |
| C10 live confirmation | whether real Pleasanter commits `updatesite` when the client times out (fake-server evidence suffices for the FAIL) | still open |
| C9 live race | real concurrent UI edit between preflight and write | still open (fake evidence → PARTIAL) |
| G6 clean-machine part | clean machine walkthrough by a person | still open (static part PARTIAL) |
| J3 | runner does not exist | still open |
| H6 agent-behaviour cases EV-01…EV-10 | agent eval runs (T12; human authorization; standard appendix) — H6 itself is FAIL on static evidence | still open |
| Real-server timeout for exceptions other than `TimeoutError` (WS3-F2 hypothesis) | injection not run | new |
| G1 | — | **resolved**: Python 3.10.21 authorised (H-3), FAIL verified |
| G5 | — | **resolved**: exports used on a copy, timings recorded |
| D5 | — | **decided** on ADR-0014 TB-3 (demo only) → FAIL at prod |
| J1 | — | **decided** FAIL (absence of the required path is evidence, §2.1) |

---

## 4. Accepted boundaries

No criterion has ACCEPTED BOUNDARY as its primary status. ADR-0014 rows cited for sub-parts:

| TB row (`0014:35-42`) | Cited by | Accepted for | WS-7 note |
|---|---|---|---|
| TB-1 operator files | B4, C1(d), C2 (person-only part), I2 | demo | control "visible in git" false for gitignored `.pls/connections.json` (WS-1); skills sanction agent edits of `Approvers`/`Origin`/`role` (WS-6 I2-a) — must be named or removed before acceptance |
| TB-2 CLI words | B4, C4, D2, I2 | demo | compensating controls EV-03/EV-10 do not exist (WS-6 H6); piped stdin = `--yes` not stated; relayed approvals in a project source (I2-e) |
| TB-3 git history | D5 | demo | "no force-push rule" not found; project repos local-only |
| TB-4 role label vs URL | B3 | demo, cstg | `setup`/`init` auto-label `role: dev` + `allow_write: true` not stated |
| TB-5 harness permissions | C4, D2 | demo | — |
| TB-6 framework integrity | B3 scenario 9 | demo | merge driver runs framework code on merges (not stated) |
| TB-7 browser runner | B3, G4 | demo, dev only | `HANDOFF.md:86` says **agents** use the runner — contradicts "driven by a person"; architecture §3.3/P5 lists it as an stg path; only `bulkupsert` path |
| TB-8 API limits | C9 | demo, cstg | compensating control "caught by the read-back" shown false (WS3-F5 `test_s18a`) |

**ADR-0014 is Proposed.** Effect on the verdict:
- **If Nam accepts it as written:** the boundary sub-parts above hold for `demo`; no primary status changes (every cited criterion also has code-closable violations: WS2-F1/F2/F4/F7/F9, G4 parity, C9 window); A6 stays PARTIAL until the missing rows are added and the three false controls fixed. **demo verdict unchanged (NOT READY).** Accepting rows whose compensating controls do not exist (TB-1, TB-2, TB-3, TB-8) would record false assurance — fix the text first.
- **If Nam does not accept it:** per §2 every boundary sub-part becomes "missing trust-boundary ADR": B3, B4, C4, D2, I2 move from PARTIAL to FAIL (G4, C1, D5 already FAIL); A6 → FAIL. Verdicts unchanged (all stages already NOT READY), but the demo fix list grows by the approval-authenticity and runner items.
- **For cstg:** TB-1/TB-2/TB-3/TB-5/TB-6 are accepted for demo only and TB-7 for dev only; cstg needs the open questions (`0014` Open questions 1–2) decided regardless of acceptance.

---

## 5. Top 5 risks (impact × likelihood, 1–5 each)

| # | Risk | Impact | Likelihood | Score | Evidence |
|---|---|---|---|---|---|
| 1 | **Agents write through the unguarded browser runner.** HANDOFF says agents use it; it has no role / `allow_write` / G4 / side-effect / confirmation / log guard, reports HTTP 500 as `pass`, ignores `as_key`, aborts restores; it is the only `bulkupsert` path | 4 | 4 | 16 | `HANDOFF.md:86`; `pls-runner.js:31-35,65-66,126-140`; G4, B3, TB-7 |
| 2 | **Changes deployed but invisible.** Duplicate list keys collapse (real config of the largest project copy, 3 sites), permissions/title never read back or drift-checked → "0 changes" at G4, `applied` without verification | 4 | 4 | 16 | WS4-F3, WS4-F2; `pls.py:393-397,853-861` |
| 3 | **Approval not bound to what is written.** G4 names a release id only; payload, target env and `steps[].site_id` editable after G4 (incl. writes to sites outside the env / shared dev sites) | 5 | 3 | 15 | B10, J2, WS2-F7, WS3-F7; `pls_gate.py:181-188`, `pls.py:2128-2133` vs `pls_http.py:183,192,207` |
| 4 | **Human-approval layer unproven.** ADR-0014 Proposed with false controls; agent writes the approver list it later records against (I2-a); later rejection can lose (WS2-F1); lifecycle 0.10–0.14 and P5 never evaluated, EV cases absent | 5 | 3 | 15 | A6, I2, WS2-F1, H6 |
| 5 | **Failure recorded as success.** Failed restore → `rolled-back`; timeout → traceback, no record; `mark-applied` turns half-applied / rolled-back / drifted state into an applied baseline; next run overwrites evidence | 4 | 3 | 12 | WS3-F1–F4, WS4-F1, F7; C8, C10, C11, E3 |

Next below the cut: secrets reach git through `unpack` / `release-plan` (WS2-F3; High, likelihood lower because `lint` usually runs).

---

## 6. Not reviewed

- `patterns/` (AI gateway, Terraform, IAM), `demo/`, `docs/slices/*` content beyond B9 tracing, `plans/` other than cited reports.
- adopted brownfield project copy (no copy provided); real release folders beyond `R-20261108-05` (D3).
- Runtime of `merge-install` git merge driver on real merges (only `test_real_git_merge_with_the_driver` in suite), `adopt-package`, `harvest` secret path (static only), `pls_usage` token-accounting accuracy.
- `kb-verify` against a server, any method-L step, agent eval runs (T12), suite with the network actually disabled (replaced by a loopback-only socket guard, WS-5).
- Exceptions after a write other than `TimeoutError` (WS3-F2 hypothesis).
- G5-a timings not re-run by WS-7.
- WS-7 did not re-run the WS-3 malformed matrix (80 cases) or WS-4 B1 replay; sampled instead (§2.3).

---

## 7. Test evidence

| Run | By | Command (worktree at `10c328a`) | Runtime | Run | Pass | Fail | Error | Skip | Not executable |
|---|---|---|---|---|---|---|---|---|---|
| Framework suite (T1) | WS-2/3/4/5, **WS-7** | `cd tools/pls && python -m unittest discover -s tests -v` | 57.0 s (WS-7) | 214 | 214 | 0 | 0 | 0 | 0 |
| Node runner (T2) | WS-2, WS-5, **WS-7** | `node --test tools/pls/tests/test_runner.mjs` | 0.08 s | 6 | 6 | 0 | 0 | 0 | 0 |
| Suite on Python 3.10.21 (T9) | WS-5 | same | 0.8 s | 14 | 1 | 0 | 13 (import `SyntaxError`) | 0 | 13 modules |
| Suite on 3.10.21, one line patched (reverted) | WS-5 | same | 54.0 s | 214 | 214 | 0 | 0 | 0 | 0 |
| Offline (loopback-only sockets) | WS-5, **WS-7** | `python tests/review_ws5_offline_run.py` | 54.0 s | 214 | 214 | 0 | 0 | 0 | 0 |
| WS-2 security scenarios | WS-2, **WS-7** | `python -m unittest review_ws2_security -v` | 13.9 s | 24 | 24 (each asserts observed behaviour; findings reproduced) | 0 | 0 | 0 | 0 |
| WS-2 runner scenarios | WS-2, **WS-7** | `node --test review_ws2_runner.mjs` | <1 s | 3 | 3 (observed) | 0 | 0 | 0 | 0 |
| WS-3 failure injection (T5) | WS-3, **WS-7** | `python -m unittest discover -s tests -p review_ws3_recovery.py -v` | 31.6 s | 22 | 5 | 17 (= findings; tests assert the safe outcome) | 0 | 0 | 0 |
| WS-3 malformed matrix (T6) | WS-3 | `… -p review_ws3_malformed.py -v` | — | 7 tests / 80 cases | 52 cases as expected | 25 tracebacks, 3 writes | — | 0 | 0 |
| WS-4 determinism / round trip | WS-4, **WS-7** | `python -m unittest tests.review_ws4_determinism -v` | 7.5 s | 24 | 7 | 17 (= findings / 2 over-reach → Low) | 0 | 0 | 0 |
| WS-4 E1 (T7) | WS-4, **WS-7** | `python ws4-out/e1_determinism.py <review>` | ~2 min | 3 copies + 1 release-plan pair | 0 differences | — | — | — | — |
| WS-4 B1 replay, B8 coverage, D4 scan, E2 real data | WS-4 | `ws4-out/*.py` | — | 6 releases / 3 copies / 371 files / 105 lists | as reported | — | — | — | 1 release (no after-export) |
| WS-5 Windows (G2) | WS-5, **WS-7** | `python -m unittest tests.review_ws5_windows -v` | 1.1 s | 10 | 8 | 2 (BOM gate, CRLF) | 0 | 0 | 0 |
| WS-5 runner parity (G4) | WS-5, **WS-7** | `node --test tools/pls/tests/review_ws5_runner_parity.mjs` | <0.1 s | 3 | 0 | 3 (= findings) | 0 | 0 | 0 |
| WS-6 lint/skills subset, `skills check`, `usage report` | WS-6 | as in WS-6 §5 | — | 2 tests + 3 copies | 2 OK; `skills check` exit 1 ×3 | — | — | — | — |
| C2 / F3 / F4 suites | **WS-7** | `test_side_effects`, `test_sandbox_merge`, `test_version`, `test_scope` | 18 s | 33 + 14 + 10 + 7 | all | 0 | 0 | 0 | 0 |
| H5 probes | **WS-7** | `python -m unittest tests.review_ws7_h5 -v` | 0.1 s | 4 | 4 (observed behaviour = finding) | 0 | 0 | 0 | 0 |
| H3 revert spot-checks | **WS-7** | revert code of `63f1f45` / `1a5f67a`, run `test_adopt` / `test_gate`, restore | ~10 s | 15 / 11 | 14 / 10 | 1 / 1 (regression tests fail on old code, as required) | 0 | 0 | 0 |
| G1 parse on 3.10 | **WS-7** | `python3.10 -c ast.parse(...)` per module | <5 s | 15 modules | 14 | 1 (`pls_adopt.py`) | — | — | — |
| Method L (B1, J1) | — | written only (WS-4 §6) | — | 0 | — | — | — | — | all (by rule) |
| Agent evals EV-01…10 (T12) | — | — | — | 0 | — | — | — | — | all (no cases, no authorization) |

WS-7 re-runs reproduced every count reported by WS-2, WS-3, WS-4 and WS-5 exactly.

---

## 8. Verdict per stage (§6.8)

| Stage | Verdict | Rule applied | Blocking items |
|---|---|---|---|
| `demo` | **NOT READY** | stage criterion FAIL (19 demo FAILs; C1 is a Critical-class criterion FAIL) | High-impact: C1, C3, C7, C11, E2, E3, E4, B1, G4; process: A2, A3, A4, H1, H3, H4, H5, H6; low-cost: A5, G1 |
| `cstg` | **NOT READY** | open Critical (B10) + cstg FAILs (C8, C10, D6) + all demo blockers | plus TB-3/TB-7 not accepted for cstg; ADR-0014 open questions |
| `prod` | **NOT READY** | open Critical (J1, J2) + prod FAILs (D5, J4, J5); J3 NOT VERIFIABLE | no runner, no package, no customer responsibilities, TD-01/02/04 open |

Path to `demo` READY WITH CONDITIONS: every demo-stage FAIL fixed or reduced to PARTIAL with evidence, no open Critical; remaining High/Medium listed with controls (e.g. runner use restricted to a person on dev per TB-7 with HANDOFF corrected; ADR-0014 accepted after its text is fixed).

---

## 9. Remediation roadmap (ordered)

**P0 — Critical (human approval, production path, secrets)**

| # | Action | Findings | Expected result | Verification |
|---|---|---|---|---|
| P0-1 | `release-plan` writes `plan_sha256` + per-file sha256; `pls gate G4` stores `{release, env, plan_sha256}`; `apply`/`bootstrap` recompute and refuse on mismatch or env ≠ record | B10, J2, D1 | edited payload / env / steps after G4 → REFUSED, 0 writes | WS-2 `test_s11*` invert |
| P0-2 | Rebuild `steps`/`rollback` from `per_site` at apply (or require exact match with env site ids and `plan.sites`) | WS2-F7, WS3-F7, C1, C7 | step for a foreign / shared site refused | `test_s11c`, `test_s14b/c` invert |
| P0-3 | Gate ordering by parsed `at` instant, refuse future `at`, rejection wins ties; validate record types (lists of strings), read with `utf-8-sig`, bad JSON → GateError | WS2-F1, WS3-F8, D1, C3 | later rejection always blocks; `releases` string refused | `test_g4_ordering…`, `test_s01b`, matrix gate rows |
| P0-4 | Agent never writes `Approvers`/`Operators`/`Origin`/`role`: person edits, or `pls profile set` with quote + record; spec-recovery review recorded like a gate; `refs --keep` takes `--quote`; re-check `jobs.verified` on use | I2-a, I2-c, I2-e, WS2-F2 | approval inputs and approvals not writable by the same agent action | skill grep; new tests |
| P0-5 | Runner: agents do not use it (correct HANDOFF:86) until it has guard parity; move `bulkupsert` to a guarded HTTP `migrate` command | TB-7, G4, B3 | no unguarded write path used by agents; migrations guarded | parity probes pass; WS-2 runner S10 inverts |
| P0-6 | L-SEC-01 enforced at `unpack`, `harvest`, `release-plan` (refuse before writing) | WS2-F3, B7, A4(7) | secret-like literal never lands in `config/` or `releases/` | `test_b7_…` inverts |
| P0-7 | ADR-0014: add missing rows (env overrides, `file:` keys, untrusted content → agent, spike, shared tenant, admin keys), correct TB-1/2/3/8 controls, then Nam decides per row | A6, D5 | each ACCEPTED BOUNDARY cites an Accepted row with true controls | A6 re-review |
| P0-8 | Evals: P5 `expected.md` + run; re-run lifecycle at 0.14; add EV-01, 03, 09, 10 first | H6 | current-version results with model + version | `evals/results/*` |
| P0-9 (before prod) | Decide ADR-0003; build package + stdlib `verify`; customer responsibilities template; Nam signs TD-01/02/04 | J1, J2, J3, J4, J5 | method-L dry run passes | person-run scenario |

**P1 — High**

| # | Action | Findings | Expected result | Verification |
|---|---|---|---|---|
| P1-1 | Recovery states: `applying` before first write, `recovery-required` on any failed / unverified restore (read back restored sites), `uncertain` on timeout (catch `OSError`/`HTTPException`), append-only apply log; `apply` refuses on these states | WS3-F1, F2, F4, C6, C8, C10, C11 | no failure leaves a success-like status; evidence kept | WS-3 `test_s16`, `test_s19*`, `test_s20*` invert |
| P1-2 | `mark-applied`: precondition `applied-unverified`, export `SiteId` = planned id, no re-stamp; partial mode `partially-applied` (not in `APPLIED`) | WS3-F3, WS4-F1, B11, E3 | rolled-back / foreign / drifted states never become baseline | WS-3 ReadBack, WS-4 F1 tests invert |
| P1-3 | Read-back model from the whole payload (permissions, Title); diff key by `Id` or `(key, occurrence)` + duplicate-name lint | WS4-F2, F3, B1, E2, F4 | duplicate / permission / title changes visible | WS-4 tests invert; method-L step 9 |
| P1-4 | `${env:x}` reverse-map whole values only; validate `values` types on load | WS4-F4, F5, WS3-F12, E4 | no substring rewrite; refusal instead of traceback | WS-4 E4 tests |
| P1-5 | Bootstrap: per-step catch, bind created ids, look up by title before re-create | WS4-F7, C10 | no duplicate site on retry | `test_c10_createsite_…` inverts |
| P1-6 | Sandbox shared-write check (`_writes_to`) in every `release-plan` for sandbox envs; test specs limited to env site ids | WS3-F6, WS2-F9, C7 | late shared-site scripts refused | `test_s22c` inverts |
| P1-7 | `pls test` on non-dev: G3/G4 record or typed confirmation; typed confirmation requires a TTY | WS2-F5, C4 | stg records not written silently | `test_c1_test_command…`, `test_c4_…` invert |
| P1-8 | Runner parity fixes (exec status, `as_key`, per-restore catch, `transport` field) + ADR-0008 differences table | G4 | parity probes pass | `review_ws5_runner_parity.mjs` |

**P2 — Medium**

| # | Action | Findings | Verification |
|---|---|---|---|
| P2-1 | One loader per file kind (`utf-8-sig`, shape validation, `Fail` naming file/field) | C3, WS3-F9, G2-b | WS-3 matrix all `ok` |
| P2-2 | Coverage per env with `api_only`/`failed`/`not_run`; empty traceability = GAP; check `design` links | H5, B8, WS4-F11 | `review_ws7_h5` probes invert |
| P2-3 | Negative test for every refusal; assert records in failure tests; fix vacuous S7 test; `fix` commits must carry a failing-on-parent test; cp932 test | H1, H2, H3 | refusal→test map complete; parent run fails |
| P2-4 | Per-site `UpdatedTime` re-read right before each write; correct TB-8 text; KB line for the race | WS3-F5, C9, B2 | `test_s18a` inverts |
| P2-5 | Run-log policy decided in one ADR (fail closed for WRITING commands, or warn + record); env / written sites in events | D6, D4, WS4-F8, F9, A4(5) | unwritable log + apply → refused or recorded |
| P2-6 | ADR governance: decide Proposed ADRs, new ADRs for gate model / setup profile / env overrides / distribution, supersede ADR-0012 notes; architecture.md points to ADRs | A2, A3, A4 | ADR README = reality |
| P2-7 | `docs/tech-debt.md` line per open review item with deadline; findings register gets a Trace column, imports D21–D31 | H4, B9, J4 | every row traced |
| P2-8 | `pls_adopt.py:94` one-line fix + startup version guard; LF writes in `wj()` + framework `.gitattributes` | G1, G2-d | 3.10 suite 214 OK; cross-OS unpack no diff |
| P2-9 | L-LAD-01 on structured DES rows only (exclude `design/as-is/`), negative tests | B5 | false-clearance test flags |
| P2-10 | KB `verified_on` compared with env version in `release-plan`/`version` | F3, WS4-F12 | VERSION line lists unverified entries |
| P2-11 | Release folder: read-back digest, executor, confirmation mode; guarded `pls rollback <R>` | D2, D3, WS4-F10 | new release folder self-sufficient |
| P2-12 | Spike folder retired or guarded (role check before localhost exemption) | WS2-F4 | static |

**P3 — Low**

| # | Action | Findings |
|---|---|---|
| P3-1 | architecture.md §3.2/§7.1/§7.2 generated or test-checked against parser and lint ids | A1 |
| P3-2 | Replace app name / site ids in core with probe ids or project config | A5 |
| P3-3 | Refusal messages with next action; no traceback text to the person | C5, WS3-F11 |
| P3-4 | KB rows: per-entry version, evidence, probe contents | F1, WS4-F13 |
| P3-5 | Skill checklists / outputs; completion-report rule; `skills check` at session start; usage warning for multi-CR sessions | I1, I3, I4, I6 |
| P3-6 | `release-plan --summary`; content tests for summaries | G5-b |
| P3-7 | setup.md: env vars, `allow_write` default (and default `false` — WS2-F8), recovery section; per-site guard re-validation (WS2-F6) | G6, WS2-F6, F8 |
| P3-8 | Standard v2.2: 65 criteria; one row per criterion; "violated sub-part → FAIL" | §2.5 |

---

## Unresolved questions

- Nam: accept / amend ADR-0014 per row (and fix the four false compensating controls first)?
- Nam: are WS-7 disputes D-1 (F4 → PARTIAL) and D-2 (G2 → FAIL) accepted?
- Is the browser runner still meant to be driven by agents (HANDOFF:86) or only by a person (TB-7)? Decides risk 1 and G4/B3 scope.
- Standard: should a violated sub-part make the criterion FAIL (proposed for v2.2)?
- J1: does a future customer runner reuse `pls apply` (then the I3 guard needs a non-agent entry point) or a separate tool?
