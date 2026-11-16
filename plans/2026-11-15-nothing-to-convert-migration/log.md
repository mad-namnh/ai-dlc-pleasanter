# Log — nothing-to-convert migration

- 2026-11-15 Code written earlier for the trial (Nam confirmed), held out of 2989ddd (stop point 1), restored onto 2989ddd from the session scratchpad. Added: apply re-check (pls.py, after MI.pending) + test.
- Parent check (worktree of 2989ddd, removed): 3 new tests FAIL on parent code; the re-check test FAILS with the re-check removed; `empty data without the flag` passes on parent (regression guard for the refusal moved out of refusals_without_a_test.txt).
- test_migrate_over_http: 12 OK. Budget: subagents 0/6.
- Nam approved the proposed ADR text ("duyet", 2026-11-15) — before review round 1; the review changes it, so the final text goes back to Nam.
- Suites: 3.12 FAILED 1 (test_every_refusal…: apply re-check MigrateError branch untested); 3.10 600 OK (skipped=2); Node 15/15.
- Review round 1 (pls-x-reviewer, opus, high; subagent 1/6): reject — F1 suite red; F2 prod package carries nothing-to-convert with no check; F3 folder site not tied to the data-impacting site; F4 one such folder blocks rollback of the whole release; F5 re-check before the typed confirmation; F6 count = what the key can see; F7 re-check follows today's folder; F8 failure paths untested, `migrating` dead end; F9 docs. → review.md. Decisions F2/F6 to Nam.
- Nam 2026-11-15: F2 → package / prod refuses nothing-to-convert; F6 → wording 'visible to the key' + ADR open question + tech debt (probe).
- Fixes for review round 1: F1 (re-check driven by the run entry, refusals tested), F2 (package + prod plan refuse), F3 (folder site must be data-impacting in the release; plan + release-plan), F4 (rollback skips such folders), F5 (re-check after the confirmation, window in the comment and ADR text), F6 (wording "visible to this key", ADR open question, TD-53), F7 (run entry: nothing_to_convert, records_read; apply reads from it), F8 (tests: read errors, unfinished entry re-runs, folder needs backup/ + dry-run.md), F9 (architecture tree, confirmation text, TD-52 P5 skill, TD-54 coverage gap). 9 tests added; affected modules 76 OK. ADR text v2 → Nam.
- Nam approved ADR text v2 ("duyet ban 2", 2026-11-15); written into ADR-0004 (Status, Decision 2 and 3, Open questions).
- Suites: 3.12 609 OK, 3.10 609 OK (skipped=2), Node 15/15 (after load-rollback test). Parent check (worktrees removed): 12 new tests FAIL on 2989ddd; 'still needs backup/dry-run' strengthened (no keys/rollback) after it passed on parent; 'empty data without the flag' passes on parent (regression guard). Review round 2 started (subagent 2/6).
- Review round 2: reject (R2-H1 BOM bypass). STOP (agent-rules §1 item 8): reported to Nam; no fix applied. Subagents 2/6.
- Nam 2026-11-15: fix R2-H1 + L1–L3, review round 3 allowed.
- Round-2 fixes: R2-H1 (read_nothing_to_convert reads utf-8-sig like load/rj; unreadable → MigrateError; plan problems + package refuse), R2-L1 (rollback skip from the forward run entry), R2-L2 (flag in the first record), R2-L3 (architecture P5). R2-L4: TD-54 (disposition). Tests: BOM (package, prod/site problems, rollback skip), unreadable file, run entry decides rollback; each shown failing on the round-2 code (worktrees removed). Suites running.
- Suites: 3.12 610 OK, 3.10 610 OK (skipped=2), Node 15/15. Review round 3 started (Nam allowed; subagent 3/6).
- Review round 3: accept with fixes (review.md). R3-L1..L3 fixed, R3-L4 disposition, TD-55/56 recorded. Re-running suites before commit.
- Suites: 3.12 610 OK, 3.10 610 OK (skipped=2), Node 15/15. Committing (tech-debt.md: only TD-52..56 staged; the D40 rows stay unstaged).
