# WS-2 — Security, human approval and production isolation

- **Review:** design review 2026-11-09, workstream WS-2 (`docs/reviews/design-review-2026-11-09/00-review-plan.md`), standard `docs/review-criteria.md` v2.1
- **Commit:** `10c328a` (detached worktree `review/wt-ws2`); trust boundaries from `docs/adr/0014-trust-boundaries.md` (**Proposed**)
- **Environment:** Windows 11 Pro 10.0.26200 · Python 3.12.10 · node v24.19.0
- **Reviewer:** independent AI agent (did not write the code). No real Pleasanter contacted; fake servers on 127.0.0.1 only. No framework file edited; no commit.
- **Labels:** **[R]** runtime-verified (test in this review or re-run of an existing test) · **[S]** static (code reading)

## 1. Test evidence

| Run | Command (in worktree) | Result |
|---|---|---|
| Framework suite (baseline) | `cd tools/pls && python -m unittest discover -s tests` | Ran 214, OK (53 s) |
| Browser runner suite | `node --test tools/pls/tests/test_runner.mjs` | 6 pass, 0 fail |
| Reviewer scenarios (new, uncommitted) | `cd tools/pls/tests && python -m unittest review_ws2_security -v` | Ran 24, OK (13 s) — each test asserts the **observed** behaviour; a pass where "Expected" ≠ "OBSERVED" in its docstring documents a finding |
| Reviewer runner scenarios (new, uncommitted) | `cd tools/pls/tests && node --test review_ws2_runner.mjs` | 3 pass |
| B7 scan | `ws2-scripts/b7_scan.py` (`SECRET_RES` from `pls.py:79` + ApiKey-field + e-mail patterns, counts only) | see §6 |

Files written by the review (worktree only, never committed): `tools/pls/tests/review_ws2_security.py`, `tools/pls/tests/review_ws2_runner.mjs`. Helper scripts outside the worktree: `review/ws2-scripts/b7_scan.py`, `b7_mask.py`.

## 2. Findings (§5 format, one row per criterion; sub-findings WS2-Fn below the table)

| ID | Criterion | Severity | Status | Stage | Finding | Evidence | Reproduction | Proposed fix | Verification |
|---|---|---|---|---|---|---|---|---|---|
| B3 | every write path refuses `role: prod` | Critical | **PARTIAL** | demo | All four Python write commands refuse prod with `allow_write: true` and fail closed on role/flag spellings [R]. Not refused: browser runner (no guard at all, incl. the only `bulkupsert` path) — **ACCEPTED BOUNDARY TB-7 for demo, dev only (ADR-0014 Proposed — holds only once Nam accepts it)**; spike tools (localhost exemption ignores role; `roundtrip-browser.js` unguarded) — no TB row → WS2-F4; role not bound to URL → TB-4 (demo, cstg). Test specs may write any site id on the server → WS2-F9 | `pls_http.py:92-97`; `pls.py:2120,2194,2220,2292,2305`; `pls-runner.js:31-35,137-164,197-200`; `spike/round-trip/scripts/common.py:59-62`; `spike/round-trip/browser/roundtrip-browser.js:11-15,40-51` | `test_s06_every_write_command_refuses_prod_with_allow_write_true`, `test_s06b_role_spellings_and_allow_write_types_fail_closed`, `test_s07_role_is_not_bound_to_url`, `test_s08_sandbox_alias_cannot_borrow_prod_or_stg_connection`, runner `S10 applyRelease writes a plan for env prod…`, `S10 bulkUpsert…`; existing `test_write_guards.DynamicTest.test_prod_is_never_written` | run the named tests | WS2-F4, WS2-F9; give the HTTP transport a guarded `migrate` command so `bulkupsert` leaves the runner (closes TB-7 for stg) | tests above invert once fixed |
| B4 | no gate / verification record without a profile approver and the person's words; skills stop | Critical | **PARTIAL** | demo | Writers check name ∈ profile for that gate (case-insensitive), non-empty quote, exclusive create [R]. Authenticity of `--approver/--quote/--by` and hand-written files = TB-1/TB-2 → **ACCEPTED BOUNDARY for demo (ADR-0014 Proposed — holds only once Nam accepts it)**. Not boundaries (code can close): decision ordering lets an earlier approval beat a later rejection (WS2-F1, High); `jobs.verified` is trusted on use without any profile re-check (WS2-F2). Skills: stop points present [S] | `pls_gate.py:143-171,174-178,181-188`; `pls.py:785,804-827`; skills `pls-x-lifecycle/SKILL.md:52-56`, `pls-p5-release-manager/SKILL.md:44,47`, `pls-p2-solution-designer/SKILL.md:36` | `test_s02_name_and_quote_validation`, `test_s04_jobs_verified_role_checks`, `test_s01_hand_written_g4_file_is_accepted_by_apply`, `test_s01b_forged_future_dated_record_overrides_a_later_real_rejection`, `test_g4_ordering_by_local_date_lets_an_earlier_approval_win_over_a_later_rejection`, `test_s03_agent_added_to_profile_can_approve`, `test_s05_hand_edited_jobs_verified_is_trusted_without_profile_recheck`; existing `test_gate.*`, `test_pls.test_jobs_verified_accepts_an_operator_of_the_env_or_a_g4_approver` | run the named tests | WS2-F1, WS2-F2 | tests invert |
| B7 | L-SEC-01 at unpack, lint, plan; `.gitignore`; no credentials / record data in logs, reports, fixtures, releases | Critical | **PARTIAL** | demo | `.gitignore` (template and 3 copies) covers `.pls/`, `tests/seed/`, `migrations/*/backup/*` [S]. Scan: **0** secret-pattern matches in 1 106 files of the three copies (incl. `ops/log/`, `releases/`, `tests/`); framework fixtures: 7 matches, all synthetic test inputs in `test_adopt.py` (5) and `test_pls.py` (2) [R]. **L-SEC-01 runs only in `lint`, `adopt` and the jobs lint — not at `unpack`, not at `release-plan`** (WS2-F3, High) [R] | `pls.py:538-540,604-606,1268`; `pls.py:2863-2867` (unpack, no check); `pls.py:962-1008` (plan_site, no check); `templates/project/.gitignore` | `test_b7_l_sec_01_runs_in_lint_but_not_at_unpack_or_release_plan`; existing `test_adopt.test_secrets_refuse_before_anything_is_written`, `test_pls` L-SEC-01 cases | run test; `b7_scan.py` | WS2-F3 | test inverts |
| B10 | G4 bound to release **and payload digest**; changed payload / target / scope refused | Critical | **FAIL** | cstg | G4 record names only release ids; no digest in G4 or `plan.json` (only `snapshot_sha256` of the live export). Payload altered after G4 → written; `plan.env` changed to another stg env after G4 → written; `steps[].site_id` changed → written [R]. ADR-0014 lists this explicitly as a gap, not a boundary | `pls_gate.py:168-170,181-188`; `pls.py:1083-1092` (plan fields), `pls.py:2121-2125,2134,2164`; real records `copies-ws2/pls-onboard-playboard-r2/gates/*.json`, `releases/R-20261108-05/plan.json` (no digest field) | `test_s11_payload_altered_after_g4_is_applied`, `test_s11b_target_env_changed_after_g4_is_applied`, `test_s11c_steps_site_id_bypasses_the_own_sites_check`, `test_s11d_g4_record_has_no_digest_and_plan_has_no_payload_digest` | run tests | `release-plan` writes `plan_sha256` over plan.json minus status fields + `sha256` per payload/rollback file; `pls gate G4` reads them and stores `{release, env, plan_sha256}`; `apply` recomputes and refuses on mismatch or env ≠ record | tests invert; add test "G4 of R, then edit one byte of payload → REFUSED, 0 writes" |
| C1 | dev/stg **and** `allow_write: true`; stg also G4; re-validated per site; no bypass | Critical | **FAIL** | demo | Role × allow_write matrix and G4 for apply/bootstrap on stg hold [R]. Violations: (a) guards evaluated once per command, never per site (WS2-F6); (b) `pls test --env stg` creates/updates/deletes records with no G4 and no confirmation (WS2-F5); (c) `apply` checks `per_site[*].site_id` but writes `steps[*].site_id` — a site outside the env (or a `shared_from` site) can be written (WS2-F7, High); (d) `$PLS_CONNECTIONS` swaps the whole connections file (TB-1); (e) `pls setup`/`init --profile` write `allow_write: true` by default, so the "local opt-in" is implicit (WS2-F8) | `pls.py:2119-2133,2164`; `pls_http.py:177-198`; `pls.py:2210-2289`; `pls_http.py:40-42`; `pls.py:1959,1973` | `test_c1_allow_write_not_revalidated_between_sites`, `test_c1_test_command_writes_stg_without_g4_or_confirmation`, `test_s11c_…`, `test_s08b_pls_connections_env_var_selects_another_connections_file`; existing `test_write_guards.DynamicTest.test_apply_bootstrap_test_kbverify_send_nothing_without_allow_write`, `test_gate.StgWriteTest.*` | run tests | WS2-F5..F8 | tests invert |
| C4 | irreversible steps need the person (typed id or `--yes` on instruction); no inference | Critical | **PARTIAL** | demo | `--yes` is an argparse flag only; no env var / config sets it; EOF → "not confirmed" [R/S]. Skills and template allow `--yes` only on the person's instruction [S]. Gaps: typed confirmation accepts piped stdin (no TTY check) — equivalent to `--yes` (TB-2/TB-5 boundary, but code-closable); `pls test` deletes/updates records with **no** confirmation (WS2-F5) | `pls.py:2026-2038,2541,2544,2553`; `skills/pls-x-lifecycle/SKILL.md:60`; `templates/project/CLAUDE.md:34` | `test_c4_typed_confirmation_accepts_piped_stdin`, `test_c4_no_confirmation_without_input`, `test_c1_test_command_writes_stg_without_g4_or_confirmation` | run tests | require `sys.stdin.isatty()` for the typed path (else demand `--yes`), record `confirmed: "typed" \| "--yes"` in `apply-log.json`; add `_confirm` (or G4 on stg) to `test` when specs write | tests invert |
| D1 | complete gate / verification records; L-GATE-01 | High | **PARTIAL** | demo | Gate record: gate, decision, approver (canonical), date, at, quote, items/releases, `recorded_by` [R]; `jobs.verified`: by, role, env, quote, at, approved_by [R]. Missing: target env and covered-artifact digest in gate records; ordering field inconsistent (WS2-F1); malformed gate file → unhandled `JSONDecodeError` (fails closed). L-GATE-01 has a positive and negative test | `pls_gate.py:138-140,168-170,218-257`; `pls.py:823` | `test_s02_…` (asserts no `env`/digest keys), `test_malformed_gate_file_is_an_unhandled_traceback`; existing `test_gate.test_lint_status_lines_need_records`, `test_records_are_never_overwritten_and_the_last_one_wins` | run tests | add `env`, `plan_sha256` to G3/G4 records; order by parsed `at` (UTC); catch bad JSON in `load` → GateError | tests |
| D2 | agent / human / operator separated; approval vs execution roles distinct | High | **PARTIAL** | demo | `jobs-verified` separates executor (`by`, `role`) and approver (`approved_by`) [R]. Elsewhere not: gate `recorded_by` is the constant `"pls gate"`; run-log `actor` = `$PLS_ACTOR` or git `user.name` — the agent runs as the operator, so agent actions and operator execution are indistinguishable; `apply-log.json` has no executor and no confirmation mode (only `ops/log` args show `--yes`) [S]. Partly TB-2/TB-5 | `pls_gate.py:169`; `pls_log.py:77-84,157-163`; `pls.py:2167`; real `releases/R-20261108-05/apply-log.json` keys `at, log, status, transport` | — (static) | inspect files | record `executed_by` (person named by the operator, checked against Operators row) and `confirmed` mode in `apply-log.json`; tag runs started by an agent (`PLS_AGENT=1` set by the harness/skill) in `ops/log` | inspect a new release folder |
| J2 | production package immutable and verifiable; altered package / wrong target / missing approval refused | Critical | **FAIL** | prod | No production runner or package verifier exists; `release-plan` writes prod plans (note only, `pls.py:1020-1021`) with no digest, no approval reference. The only apply path refuses prod entirely; on the stg path an altered package is applied (B10 tests). Not a demo/cstg blocker | `pls.py:1020-1021,1083-1112`; ADR-0003 (Proposed, TD-02) | `test_s11_*`, `test_s11d_*` | run tests | same digest scheme as B10, plus a stdlib `verify` command the customer runner calls before import (digest, env/target, release id, G4 reference, rollback present) | tests "altered byte / wrong env / no G4 → verify fails" |

### Sub-findings

| ID | Severity | Stage | Criterion | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|
| WS2-F1 | **High** | demo | B4, D1 | `latest` sorts by `(date, at)`; `date` is the recorder's **local** date and `record` bumps only `at`. A later rejection recorded from a machine whose local date is earlier (UTC+7 vs UTC+9 around midnight) loses to an earlier approval, and a hand-made future-dated record beats every real later decision. Result: `require` passes and `apply` writes stg after a recorded rejection [R] | `pls_gate.py:159-166,178`; `pls.py:2791`; tests `test_g4_ordering_by_local_date_lets_an_earlier_approval_win_over_a_later_rejection`, `test_s01b_…` | sort by `datetime.fromisoformat(at)` (aware, compared as instants); refuse records whose `at` is in the future; on equal instants a rejection wins |
| WS2-F2 | Medium | demo | B4 | `jobs.verified` is accepted by `last_applied_jobs` when merely truthy; unlike `GT.require` it is never re-checked against the Operators/Approvers rows → a hand-edited `{"by": "Mallory"}` makes the release a jobs baseline (manual deploy treated as confirmed) [R] | `pls.py:785`; test `test_s05_…` | re-run `GT.job_verifier(r, v["by"], env, v.get("approved_by"))` in `last_applied_jobs` and require a non-empty `quote` |
| WS2-F3 | **High** | demo | B7 | L-SEC-01 not enforced at `unpack` or `release-plan`: a secret-like literal from a live export lands in `config/` and `releases/<R>/payload-*.json` (both committed); only `lint` reports it [R] | `pls.py:2863-2867`, `962-1008`; test `test_b7_l_sec_01_runs_in_lint_but_not_at_unpack_or_release_plan` | run `SECRET_RES` over the export blob in `unpack` and over each payload in `plan_site`, refuse before writing (as `adopt` does at `pls.py:1268`) |
| WS2-F4 | Medium | demo | B3 | Spike write paths outside the guarded transport: `common.assert_writable` returns early for any localhost host (an SSH tunnel to a non-dev server on 127.0.0.1 is writable whatever its role); `spike/round-trip/browser/roundtrip-browser.js` creates/updates sites with no guard. ADR-0014 TB-7 names only `pls-runner.js` [S] | `spike/round-trip/scripts/common.py:59-62`; `roundtrip-browser.js:40-51` | apply the role check before the localhost exemption; mark the spike folder retired, or add a TB row |
| WS2-F5 | Medium | demo | C1, C4 | `pls test --env stg` writes records (create/update/delete; deletes are irreversible, D14) with neither a G4 record nor a confirmation [R] | `pls.py:2210-2289`; test `test_c1_test_command_writes_stg_without_g4_or_confirmation` | on non-dev envs require a G3/G4 record naming the release under test or a typed confirmation; or record the decision in an ADR (tests on stg are allowed) |
| WS2-F6 | Low | demo | C1 | Guards run once per command; `allow_write` switched off and role set to prod during a multi-site apply → the next site is still written [R]. Practical risk low (local files) but the criterion asks for per-site re-validation | `pls.py:2119-2120`; `pls_http.py:189-197`; test `test_c1_allow_write_not_revalidated_between_sites` | pass a `guard()` callable into `apply_release` that reloads env + connection and calls `assert_writable` before each `client.apply` |
| WS2-F7 | **High** | demo | C1, B3 (C7) | `apply` validates `plan["per_site"][s]["site_id"]` against environments.json (incl. `shared_from` / sandbox rules) but `apply_release` writes `plan["steps"][i]["site_id"]` and `plan["rollback"][i]["site_id"]` → an edited `plan.json` (or a plan of another env) writes a site outside the environment, including a shared base site [R] | `pls.py:2128-2133` vs `pls_http.py:183,192,207`; test `test_s11c_steps_site_id_bypasses_the_own_sites_check` | validate every `steps` / `rollback` entry (site name ∈ plan.sites, site_id == env site id, payload_file == per_site file); or rebuild steps from `per_site` at apply time |
| WS2-F8 | Low | demo | C1 | `pls setup` stores `allow_write: true` and `init --profile` writes it into `.pls/connections.json` without asking; `connections.example.json` also has `true`. The "local opt-in" is the default | `pls.py:1959,1973`; `templates/project/connections.example.json:9` | default `false`; ask "allow writes to <url>? (dev/stg only)" in setup |
| WS2-F9 | Medium | demo | B3, C7 | Test specs may target any site id (`step.site`, `run_on`): on a non-sandbox env a spec creates records in a site not listed in environments.json (another app on the same server) [R] | `pls_http.py:276,284,326`; test `test_test_spec_can_write_to_a_site_outside_the_environment` | restrict written sites to `envs.<env>.sites` ids (excluding `shared_from`) for every env, not only sandboxes |

## 3. Write-path inventory

Guard order as executed. "—" = absent.

| # | Path (entry → writer) | Endpoints | Role (dev/stg, never prod) | allow_write | G4 (stg) | Ownership / target | Confirmation | Drift / preflight | Payload | Version | Audit | Prod refused |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `pls apply` → `H.apply_release` → `Client.apply` (`pls.py:2113-2180`, `pls_http.py:177-198`) | updatesite | `assert_writable` 2120 (once) | 2120 (once) | `GT.require` 2121-2125 (release id only) | status `planned` 2126; per_site ids vs env 2128-2133 (**steps not checked**, F7) | `_confirm` 2161 | `UpdatedTime` preflight `pls_http.py:182-187`; jobs fingerprints 2145-2149 | key presence `pls_http.py:144-146`; side-effect refusals 2140-2158; **no digest** | — (plan-time `version_check`) | `apply-log.json` 2167, `ops/log` | yes [R] |
| 2 | auto-rollback inside #1 (`pls_http.py:201-211`) | updatesite | inherited from #1 | inherited | inherited | `plan["rollback"]` ids (unchecked) | inherited | — | — | — | in apply-log | yes (via #1) |
| 3 | `pls bootstrap` → `H.bootstrap` → `Client.create_site` (`pls.py:2182-2208`) | createsite | 2194 | 2194 | 2195-2198 | status ≠ created 2186; skip bound sites 2188-2189; parent is folder `pls_http.py:216-218`; step parent = plan parent 220 | `_confirm` 2200 | — | — | — | `bind` writes env; ops/log | yes [R] |
| 4 | `pls test` → `H.run_tests` (`pls.py:2210-2289`) | create, update, delete, exec(update) | 2220 | 2220 | **—** (F5) | shared-site check **sandbox only** 2241-2247 (F9) | **—** | — | — | — | `tests/results/*.json`, ops/log | yes [R] |
| 5 | `pls kb-verify` (`pls.py:2290-2412`) | createsite, updatesite, run_tests | role == dev, not sandbox 2292 + 2305 | 2305 | n/a (dev only) | probe parent ≠ app folder/sites 2296-2299; own probe site 2333 | `_confirm` 2314 | — | — | schema from env record | `ops/kb-verify/*`, ops/log | yes [R] |
| 6 | `Client.bulk_upsert` (`pls_http.py:170-172`) | bulkupsert | — | — | — | — | — | — | — | — | — | no caller (locked by `test_write_guards.CLIENT_WRITERS`) |
| 7 | read-only network commands: http-check, export, version, adopt, adopt-package, backup, sandbox refresh, harvest, principals, setup | getsite, get, users/get, groups/get, login page | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ops/log | n/a — locked by `test_write_guards.StaticTest` [R] (heuristic: owner names `client/c/self`, literal paths only — `test_write_guards.py:82-83,99`) |
| 8 | `pls-runner.js` `apply`, `applyRelease`, `rollbackRelease`, `bootstrapSites`, `runTests`, `bulkUpsert` | updatesite, createsite, create/update/delete, bulkupsert | **—** | **—** | **—** | **—** (no status/env check) | — (person drives console) | preflight `:145-151` | key presence `:32` | — | — | **no** [R] → TB-7 (demo, dev only) |
| 9 | `spike/round-trip/scripts/roundtrip.py` → `common.post(write=True)` | createsite, updatesite | role == dev (`common.py:60-62`) **after localhost exemption** | yes | n/a | — | host retype or `--yes` (`common.py:65-74`) | — | — | — | — | yes, except localhost (F4) [S] |
| 10 | `spike/round-trip/scripts/br3_probe.py` | createsite, updatesite | `H.assert_writable` + role dev (`:104-107`) | yes | n/a | `--reuse` title/type check | — | — | — | — | — | yes [S] |
| 11 | `spike/round-trip/browser/roundtrip-browser.js` | createsite, updatesite | **—** | **—** | **—** | — | — | — | — | — | — | **no** (F4) [S] |

## 4. Approval-path inventory

| Path | Writes | Checks (file:line) | What the consumer re-checks | Proof of human authorization? |
|---|---|---|---|---|
| `pls gate G1–G4` → `GT.record` | `gates/<date>-<gate>-<time>-<rand>.json`, exclusive create | gate/decision enum; quote `strip()` non-empty; items (G1/G2) / releases (G3/G4) present; approver ∈ Approvers row for that gate, casefold (`pls_gate.py:143-171`) | `GT.require` (`:181-188`): last record by `(date, at)` covering the release, decision approved, approver still in profile. No check of `recorded_by`, file name, `at` plausibility, env, content | **No** — a profile name plus any non-empty string ("." accepted). Hand-written file accepted (S1). Authenticity = TB-1/TB-2 |
| `release-plan` (stg) | needs G3 | `GT.require(…"G3"…)` `pls.py:1023-1027` | same as above | same |
| `apply` / `bootstrap` (stg) | need G4 | `pls.py:2121-2125`, `2195-2198` | same; G4 bound to release id only (B10) | same |
| `pls jobs-verified` → `jobs_verified` | `plan.json` `jobs.verified` (overwrite of the plan file, not exclusive) | release applied; jobs changed; quote non-empty; `--by` operator of env or G4 approver; `--approved-by` G4 approver (`pls.py:804-827`, `pls_gate.py:116-135`) | `last_applied_jobs` (`pls.py:785`): **truthiness only** (F2) | **No**; and not re-checked on use |
| `--accept-drift` / `--accept-unverified` decision records | none (referenced) | file exists (`pls.py:1016-1019`); unverified record hashed (`:1000-1001`) | none — no approver, no content check | **No** (any file) — note for WS-3 / B2 |
| `--yes` / typed confirmation | — | `_confirm` (`pls.py:2026-2038`): typed release id via `input()`; EOF refuses | — | **No**: piped stdin accepted (C4) |
| `environments.json` `side_effects`, `role`; `CLAUDE.md` Approvers/Operators; `.pls/connections.json` `allow_write` | plain files | parsed; placeholders rejected (`pls_gate.py:46,111`) | — | TB-1 |

Distinction asked for: every approval artifact is **a name that appears in the profile plus a non-empty quote**, written by whoever can run `pls` or edit files. Nothing binds it to a person (no signature, second channel, or session evidence). Within that boundary the code is consistent for G1–G4 writers; the consumers are weaker than the writers (ordering F1, `jobs.verified` F2, content binding B10).

## 5. Scenario results (plan Deliverable 5)

| # | Scenario | Executed | Result | Test |
|---|---|---|---|---|
| 1 | hand-written G4 → apply stg | yes [R] | **accepted** (writes) → TB-1; plus F1 (future-dated forged record beats a later real rejection) | `test_s01_…`, `test_s01b_…` |
| 2 | `--approver "nam "`, `--quote " "`, placeholder / tbd / empty profile | yes [R] | whitespace quote, unknown name, wrong gate, `<name>`, `tbd`, empty row, no row → refused; `"  nAM "` → stored as `Nam`; quote `"."` accepted | `test_s02_name_and_quote_validation` |
| 3 | add "Claude" to Approvers → `pls gate` | yes [R] | works (no denylist) → TB-1/TB-2 | `test_s03_…` |
| 4 | jobs-verified: dev operator on stg; non-G4 `--approved-by`; empty quote | yes [R] | refused; valid stg operator accepted | `test_s04_…` |
| 5 | hand-edit `plan.jobs.verified` | yes [R] | trusted without profile re-check (F2) | `test_s05_…` |
| 6 | every WRITES command vs `role: prod` + `allow_write: true` | yes [R] | 0 write requests for apply, bootstrap, test, kb-verify (exit 2 each); role/flag spellings fail closed | `test_s06_…`, `test_s06b_…` |
| 7 | same URL as prod labelled stg | yes [R] | written (role not bound to URL) → TB-4 | `test_s07_…` |
| 8 | sandbox alias to prod / stg / mismatched base | yes [R] | refused; valid dev alias works; `$PLS_CONNECTIONS` noted (S8b) | `test_s08_…`, `test_s08b_…` |
| 9 | `PLS_HOME` → modified framework | static [S] | launcher `pls.py:11-17` (copies) runs any path in `PLS_HOME` / lock; `skills check` hashes skills only → TB-6 | — |
| 10 | browser runner guards | yes [R] (node, vm + fake fetch) | `applyRelease` writes a plan with `env: "prod"`, `status: "applied"`; `bulkUpsert` unguarded; `rollbackRelease` has no per-site try/catch (parity gap vs `pls_http.py:206-209`) → TB-7 | `review_ws2_runner.mjs` (3 tests) |
| 11 | alter payload after G4 → apply | yes [R] | **applied**; also target env change and `steps[].site_id` change applied | `test_s11_…`, `test_s11b_…`, `test_s11c_…`, `test_s11d_…` |
| 12 (C1, extra) | per-site re-validation | yes [R] | not re-validated (F6) | `test_c1_allow_write_not_revalidated_between_sites` |
| 25 | grep copies' `ops/log`, `releases`, `tests` for `SECRET_RES` | yes [R] | 0 matches (see §6) | `b7_scan.py` |

## 6. B7 scan (counts and paths only; no values printed)

| Target | Files scanned | Matches (`SECRET_RES` + ApiKey-field + e-mail) |
|---|---|---|
| `copies-ws2/*/ops/log`, `releases`, `tests` (3 projects; `ops/log` exists only in playboard-r2: 2 files, 486 events) | 381 | 0 |
| whole copies (config, design, requirements, gates, ops, …) | 1 106 | 0 |
| framework `tools/pls/tests`, `demo`, `templates`, `evals` | 106 | `test_adopt.py` assigned-secret ×5 (lines 103, 113 ×2, 114, 168), `test_pls.py` anthropic-key ×2 (86, 114) — all synthetic test inputs (checked by marker, not printed); e-mail ×16 in `test_side_effects.py` (14) / `test_sandbox_merge.py` (2) — test mail-config fixtures, not inspected further |

Run-log events carry raw argv (`pls_log.py:157`), incl. `--quote` text and `--var` fixture ids; no URL found in any `message`/`args`. `tests/results/*.json` hold test-record field values (dev/stg test data at demo; would be customer data at cstg — not gitignored). `pls backup --out` is a free path (`pls.py:2624`); only `migrations/*/backup/*` is ignored.

## 7. Skipped steps

- Method L (live Pleasanter) not run, by rule. Not needed for WS-2 criteria except J2's production runner, which does not exist.
- Scenario 9 static only (running a modified framework adds nothing beyond the launcher reading).
- No check of `pls-adopt-797` (no copy provided). `pls-demo-equipment` has no `CLAUDE.md` / `gates/` (older layout).
- The static write-path lock (`test_write_guards.py`) was read, not mutation-tested (alias evasion stated from code).

## 8. For other workstreams

- **WS-3 C3/C11:** an int in `envs.<env>.values` (e.g. `kb_probe_parent: 950`, the form `test_write_guards.py:130` uses) makes the post-apply `mark-applied` raise `TypeError` at `pls.py:164` **after** the sites were written: traceback, plan left `planned`, apply-log `applied-unverified` (`test_int_env_value_crashes_mark_applied_after_a_successful_write`).
- **WS-3 C3:** non-JSON file in `gates/` → unhandled `JSONDecodeError` from `pls_gate.py:140` on apply/release-plan/lint (fails closed) (`test_malformed_gate_file_is_an_unhandled_traceback`).
- **WS-3 C6 / G4 parity:** runner `rollbackRelease` (`pls-runner.js:126-135`) stops at the first throwing restore; HTTP `rollback` continues (`pls_http.py:206-209`).
- **WS-3 B2:** `--accept-drift` accepts any existing file as the decision record (`pls.py:1016`), no approver or content check.
- **WS-3 D3/D4:** `apply-log.json` has no executor and no confirmation mode.
- **WS-1 A6:** ADR-0014 TB-7 covers `pls-runner.js` but not `spike/round-trip/browser/roundtrip-browser.js` nor the spike localhost exemption; TB-2 should name piped stdin as equivalent to `--yes`.
- **WS-1 A4:** project `CLAUDE.md` rule 1 still describes the spike guard ("only dev", `config.json`) next to the `pls` rule (dev or stg) — two wordings of one rule.
- **WS-5 H1:** `test_write_guards` static lock detects only `.call("<literal>")` and owners named `client`/`c`/`self` (`test_write_guards.py:82-83,99`); an alias or computed path escapes it. Prod refusal had a dynamic test only for `apply` before this review.
- **J1/J3:** no production runner exists; nothing to inspect.

## 9. Top risks (impact × likelihood)

1. **B10 / J2 — approval not bound to content or target** (Critical, cstg/prod). Any edit to `releases/<R>/` after G4 is applied under that G4. Must close before the first customer staging release.
2. **WS2-F1 — later rejection ignored** (High, demo already). Ordering by local date; realistic with approvers in UTC+7 and UTC+9 around midnight; also the cheapest forgery.
3. **WS2-F7 — plan steps bypass the own-site check** (High). One edited field in `plan.json` writes a site outside the environment, including shared base sites of sandboxes.
4. **WS2-F3 — secrets reach git through `unpack` / `release-plan`** (High). Only `lint` catches them; INV-07 depends on the agent running lint before commit.
5. **Unguarded runner as the only migration (`bulkupsert`) path** (TB-7; High at cstg). Data-impacting migrations to stg have no code guard; TB-7 explicitly does not accept stg with customer data.

## 10. Status per criterion

| Criterion | Status | Severity of worst open item |
|---|---|---|
| B3 | PARTIAL (Python paths verified; runner → ACCEPTED BOUNDARY TB-7 demo-dev, ADR-0014 Proposed; spike gaps) | Medium (F4, F9) |
| B4 | PARTIAL (writers verified; authenticity → ACCEPTED BOUNDARY TB-1/TB-2 demo, ADR-0014 Proposed) | High (F1) |
| B7 | PARTIAL | High (F3) |
| B10 | FAIL (stage cstg) | Critical |
| C1 | FAIL | High (F7) |
| C4 | PARTIAL | Medium (F5, piped stdin) |
| D1 | PARTIAL | Medium |
| D2 | PARTIAL | Medium |
| J2 | FAIL (stage prod) | Critical |

## Unresolved questions

- Is `pls test` on stg without G4 intended (smoke tests after apply)? If yes it needs an ADR line; otherwise WS2-F5 stands.
- Should `--accept-drift` decision records carry an approver checked against the profile (same rule as gates)?
- Spike folder: retire, or add it to ADR-0014?
