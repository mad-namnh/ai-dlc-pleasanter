# Log — scalar keys verified

- 2026-11-16 Nam: "toi da chay pls kb-verify --env dev". Report read (trial, read-only). D46 failing key traced in source (SiteSettings.cs l.388, l.1254; shipped Dashboard.json false).
- Worktree of 2dca8a3 (`../_agent-scratch/wt-scalar-verified`): the main tree holds uncommitted KB edits of the D40 task.
- Curator (opus, high; subagent 1/6): DONE_WITH_CONCERNS — rows D43–D47, index runs for all 20 entries, schema.md D8 note; D46 verified_on stays [] (convention of D40/D41a); concerns: D46 split needs a probe change, D8 row / SKILL.md Fact 2 not updated (out of brief).
- pls_scope.py: 85 keys; test_scope test reads the probe files.
- KB version 0.29 in skills/README.md (0.28 is the uncommitted D40 change).
- Suites: 3.12 623 OK; 3.10 623 OK (skipped=2); node 16/16. Parent check: the new test fails on 2dca8a3 (1 failure).
- Review round 1 started (pls-x-reviewer, opus, high; subagent 2/6).
- Review round 1: reject — H1 mail keys entered VERIFIED_KEYS against Nam's 2026-11-15 decision (kept out of git, WS1.5) → held back (81 keys), test asserts they stay unverified. M1 checklist row 30, ADR-0023 follow-up (per-key reading, L2), review-findings D43–D47 and D46, sanitized evidence file. L3 version 0.28 (commit order; the D40 task renumbers when it commits). L4 → TD-63. L1 and the D47 rule text → curator.
- Curator fix call (opus, high; subagent 3/6, plus one follow-up message): D43–D47 'pls canon' wording; D47 mail rule (kept out of git; decision record until WS1.5).
- Suites after round-1 fixes: 3.12 623 OK; 3.10 623 OK (skipped=2); node 16/16.
- Review round 2 started (pls-x-reviewer, opus, high; subagent 4/6).
- Review round 2: accept with fixes (M1 D47 rule vs L-DEP-01, M2 safety switches config-only, L1–L4).
- Fixes: six switches held back (75 keys; TD-63 reworded); docstring 'Not here'; checklist columns; curator (opus, high; subagent 5/6) D44 / D46 / D47 rows and SKILL.md Fact 2; README; HANDOFF line. L4 (per-key reading of a failed probe) → for Nam's confirmation in the report.
