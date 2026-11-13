# Log — TD-30

Counts: subagent calls 2/6, review rounds 2/2, fix attempts 0/3.

- 2026-11-13 | plan written; parent `6b1e889`. Tier Standard. Template sync = report only (project owns its copies) — my reading of N1, stated in the plan and the report.
- 2026-11-13 | built: launcher message (N2); skills check/sync orphans, foreign folders, launcher, template hashes (N1); `unpack()` + `refuse_uncommitted_site` (N4), adopt remap calls `unpack()` directly; CLI passes FRAMEWORK explicitly (default arg was bound at import: not mockable); init no longer writes the launcher twice. Tests: new file (9). Docs: TD-30 closed, architecture rows, setup.md troubleshooting, lifecycle 0.27 (eval with TD-37), HANDOFF. Suites 567 OK (3.12), 567 OK skipped=2 (3.10), node 15. Parent check (worktree at 6b1e889, removed): 9 new tests fail (6 FAIL, 3 ERROR).
- 2026-11-13 | subagent 1/6: reviewer sonnet medium round 1/2 — accept with fixes, 4 Low (review.md); tree unchanged. Fixed R1 (edited orphan named), R3 (`_remove_skill_dir`: no deletion through a link / junction); tests +2. Suites 569 OK (3.12), 569 OK skipped=2 (3.10), node 15. Round 2 next.
- 2026-11-13 | subagent 2/6: reviewer sonnet medium round 2/2 — accept, 3 Low; tree unchanged. L1, L2 → TD-43; L3 intended. Parent check again with all 11 new tests: 8 FAIL, 3 ERROR. Commit with explicit paths.
