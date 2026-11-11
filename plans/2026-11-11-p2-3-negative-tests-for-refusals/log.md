# Log — P2-3 negative tests for refusals

Counts: subagent calls (not eval cases) 1/6, review rounds 1/2, fix attempts 0/3.

- 2026-11-11 | state: `brownfield-adr`, parent `f77b47a`, working tree clean; classified Standard; main session model `claude-fable-5-2`
- 2026-11-11 | measured (one-off script in the session scratch folder, Python 3.12 `sys.monitoring`): 261 refusal lines, 118 never run by the suite
- 2026-11-11 | asked Nam (scope and fix-commit rule are his): chose "ratchet + the items the review names" and "a check script + the rule in HANDOFF"
- 2026-11-11 | part 1 implemented: ratchet module (6 tests) + list (121 names of 273 refusals; `print` / `return` refusals are counted too, hence 273 not 261)
- 2026-11-11 | whole suite with an empty list: 1 failure (the ratchet test, 121 refusals reported) — shows the suite fails on an unlisted, untested refusal; with the list: Ran 363, OK (3.12, about 150 s instead of 115 s); 3.10: Ran 363, OK (skipped=2: the comparison needs 3.12)
- 2026-11-11 | a second demonstration (remove one line from the real list, run, restore) was denied by the permission rules as one shell command; not repeated — the stale-line direction will show when part 2 adds tests
- 2026-11-11 | commit part 1: `3b9c14f`
- 2026-11-11 | part 2, found already covered since the review (not written again): failed restore, timeout after a write, records after a failed apply, mark-applied with another site's export in the multi-site form (`test_apply_recovery_and_readback.py`); jobs.verified on use (`test_pls.py`, `test_side_effects.py`); L-LAD-01 both directions (`test_ladder_decision_names_the_script_and_the_site.py`); prod refusal of apply and migrate. `test_log_failure_never_breaks_a_command` no longer exists (replaced by the P2-5 tests)
- 2026-11-11 | part 2 implemented: `test_refusals_leave_nothing_behind.py` (11 tests), `test_output_on_a_cp932_console.py` (3 tests); assertions added to 7 existing tests (`test_pls.py` ×4 incl. the CRLF test, `test_scope.py`, `test_side_effects.py`, `test_http.py`); no assertion removed
- 2026-11-11 | guards switched off one at a time in a copy `../_agent-scratch/p23-copy/` (script in the session scratch folder): the matching test failed for 17 of 18; the 18th (CRLF: `newline="\n"` on write) is not a real loss of CRLF — two real ones (platform line ends on write, universal newlines on read) both fail the CRLF test. 20 checks, all noticed: L-DEP-01; slot ledger (release-plan, plan); migration required; drift; mark-applied applied / unknown status; jobs-verified no plan / nothing changed / quote; single-site marked again / other site's export; payload keys; prod role in assert_writable; kb-verify dev only; harvest not prod; CRLF ×2; UTF-8 console. No guard was found broken. The repository's `pls` was never changed
- 2026-11-11 | a shell command of mine ended with `git -C . status` and was denied by the deny rule of `5ef09eb` — my mistake, not a bypass attempt; re-run with plain `git status`
- 2026-11-11 | whole suite with the new tests and the old list: 1 failure — the ratchet named 13 list lines that a test now runs (shows acceptance criterion 2 on the real suite); the 13 lines were removed (121 → 108); the ratchet's failure message now prints one name per line
- 2026-11-11 | suites: Python 377 OK (3.12), 377 OK skipped=2 (3.10), node 15 pass
- 2026-11-11 | commit part 2: `151d4d9`
- 2026-11-11 | part 3 implemented: `tools/dev/check_fix_commits.py` (outside `tools/pls/`, so the refusal and layout scans of `tools/pls/*.py` do not read it) + `test_fix_commits_carry_a_test.py` (4 tests, temporary git repositories; skipped without git). Decision: the check looks at the subject `fix…` and at the paths, start commit `151d4d9`; run over the whole history it reports exactly `1a5f67a`, `a060b6c`, `993eae1` (the three of review H3)
- 2026-11-11 | the new test file cannot run on the parent (it imports a script the parent does not have): import error there by construction
- 2026-11-11 | subagent call 1/6: `pls-x-reviewer`, model `sonnet`, effort `medium`, review round 1/2 — verdict accept with fixes; 2 Medium, 3 Low; dispositions in `review.md`; `git status` identical before and after
- 2026-11-11 | after the review: `sys.exit` with a message counts as a refusal (274 refusals); the one it found (Python version guard) got a test that runs the guard as Python 3.9 and as 3.10; limits written into the module docstring, TD-22 and HANDOFF. Not sent for a second review round: no Critical / High finding
- 2026-11-11 | scratch: Nam removed `../_agent-scratch/p23-copy/` himself (my `rm -rf` was denied)
- 2026-11-11 | suites: Python 382 OK (3.12, nothing skipped), 382 OK skipped=2 (3.10), node 15 pass; `python tools/dev/check_fix_commits.py` → 0 commits
- 2026-11-11 | commit part 3: test(pls): fix commits that change pls without a test are reported
- 2026-11-11 | counts: subagent calls 1/6, review rounds 1/2, fix attempts 0/3
- 2026-11-11 | REPORT SENT
