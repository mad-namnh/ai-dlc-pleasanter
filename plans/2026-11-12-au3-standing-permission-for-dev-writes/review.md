# Review — AU3 standing permission for dev writes (Critical)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `e9daaa7`.

## Round 1 — accept with fixes (0 Critical, 0 High, 2 Medium, 3 Low)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | A `dev-writes` record was used without checking that its approver is an approver now; lint did not check these records | Fixed: `dev_writes` requires the record's approver in the effective profile; L-PRF-01 flags an `on` record by a non-approver; tests (former approver, hand-written record) |
| F2 | Medium | Confirmation not recorded for `migrate`; `bootstrap` only in the run log | Fixed: `confirmed` + `executed_by` in the migration entry of `plan.json` and in `bootstrap.json`; run-log metric for apply / bootstrap / migrate; end-to-end tests |
| F3 | Low | Tests checked the helper, not the commands | End-to-end bootstrap and migrate under the permission; static test: only apply / bootstrap / migrate call `_confirm_write`; empty-quote case |
| F4 | Low | Same-instant on/off records: file name decided | Fixed: the withdrawal wins a tie; test |
| F5 | Low | Stale docs (HANDOFF, architecture, TB-2, skills, ADR-0008) | Fixed; ADR-0008 (Decision section, Proposed) left for Nam, noted in ADR-0024 |

## Round 2 — accept with fixes (0 Critical, 0 High, 1 Medium, 5 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`, started by the Orchestrator on 2026-11-12 (Nam's instruction "review vong 2 for AU3"); `git status` and a hash of the diff equal before and after the call.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Medium | Round-1 fix F2 wrote `executed_by` / `confirmed` into `bootstrap.json`, which the G4 digest covers: re-running a partial stg bootstrap was refused "changed since G4" (reproduced by the reviewer on the fake server) | Fixed: one entry per run in `bootstrap-log.json` (outside the digest, keeps every run, not only the last); `bootstrap.json` untouched; test `test_a_partial_stg_bootstrap_is_resumed_under_the_same_g4` fails on the round-1 code with the reviewer's error and passes now; `pls_release_digest.py` not changed |
| R2-2 | Low | architecture §3.3 dev row, `pls.py` and `pls_profile_records.py` docstrings, P3 config-builder step 5 still said "always typed" | Fixed (config-builder 0.8) |
| R2-3 | Low | ADR-0024 option B and a code comment claimed a hand-written record is detected | Fixed: comment reworded; ADR-0024 "As built" states the narrower check (the Decision section and option text unchanged) |
| R2-4 | Low | TB-3 did not name the new record kind (deleting an `off` restores `on`) | Fixed: TB-3 "Not covered" names it; ADR-0024 "As built" too |
| R2-5 | Low | Recording `on` accepted an env whose file role is stg but role record dev (never takes effect) | Fixed: recording needs dev in both; test |
| R2-6 | Low | Static test missed other call spellings | Fixed: every `_confirm_write(` call must match the pattern |
| Obs. | — | Record names an env, not a URL (TB-10) | Written into ADR-0024 "As built" |

Not reviewed again: round 2 was the last allowed round; the R2-1 fix is verified by its test (fails on the round-1 code, passes now) and both suites.
