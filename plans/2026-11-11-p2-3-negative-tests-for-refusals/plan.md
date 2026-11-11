# Plan — P2-3: a negative test for every refusal (ratchet), records asserted in failure tests, S7 and cp932 tests, fix-commit check

- **Date / branch / parent commit:** 2026-11-11 / `brownfield-adr` / `f77b47a`
- **Objective:** Close review criteria H1, H2, H3 as far as Nam chose: no new refusal of `pls` without a test; the refusals the review named get their tests; failure tests assert the records; the vacuous CRLF test and the missing cp932 test are fixed; `fix(pls)` commits without a test change are reported by a script.
- **Tier:** Standard — tests and one read-only developer script. No guard, gate or command changes. If a new test shows a guard that does not refuse, that fix is **Critical** and is reported before it is built.
- **Nam's decisions (2026-11-11, asked before building):** scope = "ratchet + the items the review names" (not all 118 untested refusals now); fix-commit rule = "a check script + the rule in `HANDOFF.md`".
- **Measured before the task:** 261 refusal lines in `tools/pls/*.py` (a `raise`, or a `print` / `return` that says REFUSED / NOT marked / NOT VERIFIED); the suite never runs 118 of them (Python 3.12 `sys.monitoring`, one-off script).
- **Scope, three commits:**
  1. **Ratchet.** A test module that records which lines of `tools/pls/*.py` the suite runs (Python 3.12+ `sys.monitoring`; skipped on 3.10 and when only part of the suite runs) and fails when a refusal line is never run and is not in `tools/pls/tests/refusals_without_a_test.txt`, or when that list names a refusal that is now run or no longer exists. Entries are keyed by file, function and statement text, not by line number.
  2. **Tests the review names** (H1, H2, H3): L-DEP-01 refusal; L-LAD-01 negative direction; prod refusal of `bootstrap`, `test`, `kb-verify`; a restore that fails; `jobs.verified` checked on use; `mark-applied` on a wrong status / a foreign export; a timeout after a write; the 8 exit-code-only tests assert state; failure tests read `apply-log.json` / `plan.json`; the CRLF test (S7) asserts a difference count; a cp932 console test. Items already covered since the review are listed with the test that covers them instead of being written twice. The list of commit 1 shrinks accordingly.
  3. **Fix-commit check.** `tools/pls/dev_check_fix_commits.py` (read-only, `git log`): reports every `fix(pls)` commit after a start commit that changes no file under `tools/pls/tests/`. Rule added to `HANDOFF.md` "How we work".
- **Out of scope:** tests for the rest of the untested refusals (→ `docs/tech-debt.md` with a deadline); refusals reached only through a subprocess count as untested; the node runner; B9 trace items (P2-7).
- **Files:** `tools/pls/tests/test_zz_every_refusal_is_run_by_a_test_or_listed.py`, `tools/pls/tests/refusals_without_a_test.txt`, new and changed test files under `tools/pls/tests/`, `tools/pls/dev_check_fix_commits.py`, `docs/tech-debt.md`, `HANDOFF.md`, this folder.
- **Invariants and ADRs touched:** none (tests of I2, I3, I4 guards; no behaviour change).
- **Stop points expected:** none; item 2 of `docs/agent-rules.md` if a guard turns out not to refuse.
- **Acceptance criteria:**
  1. The suite fails when a refusal is added to `tools/pls/*.py` that no test runs and the list does not name.
  2. The suite fails when the list names a refusal that a test now runs, or that no longer exists.
  3. Every refusal the review names under H1 has a test that asserts the refusal and that nothing was written; where one existed already, it is named.
  4. No test on a guard or failure path asserts only an exit code; failure tests of `apply` assert `apply-log.json` and the plan status.
  5. The CRLF test fails when script bodies lose CRLF; a test fails when pls output cannot be written to a cp932 console.
  6. `dev_check_fix_commits.py` reports a `fix(pls)` commit without a test change and passes on the history after its start commit.
  7. New tests fail on the parent commit where the parent lacks them (mechanism tests) or are shown to fail when the guarded code is disabled (tests of existing guards cannot fail on the parent: the guard is already there — stated per test).
  8. Both suites pass (Python 3.12 and 3.10; node). No test is weakened or deleted.
- **Subagents planned:** `pls-x-reviewer` on `sonnet`, effort `medium`, once over the three commits; `opus` if a guard defect is found.
- **Documents to update:** `HANDOFF.md` (progress, counts, "How we work"), `docs/tech-debt.md` (remaining untested refusals, with a deadline).
