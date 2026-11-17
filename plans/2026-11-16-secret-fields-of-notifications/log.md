# Log — credential fields of notifications and reminders

- 2026-11-16 Nam: "cu lam tuan tu het khong can hoi" (settings coverage, sequential). WS1.2 / 1.4 found done in 1f2d2e5; next WS6c. Tier Critical.
- Source read (Pleasanter_1.5.2.0 Notification.cs l.20–62, 285–370; Reminder.cs l.27–56, 245–320). Existing L-SEC-01: pattern checks only (pls.SECRET_RES).
- Work in a clean worktree of 2dca8a3 (`../_agent-scratch/wt-secret-paths`): the main tree holds uncommitted work of the mail-settings and D40 tasks.
- Suites: 3.12 625 OK; 3.10 625 OK (skipped=2); node 16/16. Parent check (module copied, not wired): 10 failures in the 3 new tests.
- Review round 1 started (pls-x-reviewer, opus, high; subagent 1/6).
- Review round 1: accept with fixes (M1 pack, M2 env values / raw export, M3 patterns, L1 docs, L2 OverflowError, L3 hint) → review.md.
- Fixes: pack refuses the resolved payload; unpack / harvest also check the raw export; lint checks each environment's payload; header names read as JSON keys, wider name words, query names, known webhook hosts; OverflowError; ADR-0005 hint in the refusal; ADR-0005 open question annotated. New test test_pack_and_lint_refuse_a_credential_kept_as_an_environment_value.
- refusals_without_a_test.txt: acl_from_refs unresolved-principal refusal is now run by a test (lint resolves every environment's payload) → line removed, as the meta-test requires.
- Suites after fixes: 3.12 626 OK; node 16/16; 3.10 re-run with round 2.
- Review round 2 started (pls-x-reviewer, opus, high; subagent 2/6).
- Suites (round-1 fixes): 3.10 626 OK (skipped=2).
- Review round 2: accept with fixes, F1 High open (single-site `pls plan` writes releases/ without L-SEC-01) → review.md.
- Fixes after round 2 (no third review round: agent-rules item 8): F1 plan refuses (payload and live rollback) before writing; F2 unpack test with a credential equal to an environment value (harvest's raw check untested → TD-62); F3 test of the unmapped-principal refusal through pack; F4 env-compare and mark-applied → TD-62; F5 lint catches Fail only and reports "not checked for env"; F6 numbers, enum names, user:pass URLs; docstring limits; F7 architecture I7 / L-SEC-01, adr/README, review-findings D5.
- Suites after round-2 fixes: 3.12 630 OK; 3.10 630 OK (skipped=2); node 16/16. Parent check (module copied, not wired): 16 failures in 6 of the 11 tests; the other 5 test the module itself (absent on the parent) or an existing refusal (F3).
- STOP (agent-rules item 8): a High finding was open after round 2. It is fixed and tested, but not independently re-reviewed. Not committed; Nam decides: a third review round, or commit on the tests.
- 2026-11-16 Nam, verbatim "1a" (to: (a) a third review round of the F1 fix, then commit; (b) commit on the tests; (c) reject the product consequence): third review round, scope the F1 fix; consequence (Slack / Teams / RocketChat / LINE WORKS / token notifications refused by unpack, adopt, release-plan) not objected to. Review round 3 started (pls-x-reviewer, opus, high; subagent 3/6).
- Review round 3: accept with fixes (R3-1 Medium, R3-2..4 Low) → all fixed (review.md). New lint test fails on the pre-fix code (copy of tools/pls with the fix reverted); the plan payload test guards the check (fails on 2dca8a3, where plan has no check). Suites: 3.12 632 OK, 3.10 632 OK (skipped=2), node 16/16. Subagents 3/6. Commit.
