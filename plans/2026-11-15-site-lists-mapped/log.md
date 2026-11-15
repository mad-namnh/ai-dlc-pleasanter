# Log — site lists mapped

- 2026-11-15 Module pls_site_lists.py (drafted while the WS1.1 review ran, applied after its commit af5a80a); pls.py logical / payload / lint + site_id_of helper. Test in test_pls. Parent check (worktree of af5a80a, removed): new test FAILS.
- Docs: architecture L-PERM-01 row, inventory rows (WS1.2 closed by source).
- Refusal-coverage test asked for tests of site_id_of and the text-list refusal → test_site_list_refusals. Suites: 3.12 620 OK, 3.10 620 OK (skipped=2), Node 16/16 (unchanged JS). Review started (pls-x-reviewer, opus, high; subagent 1/6).
- Review round 1: accept with fixes (review.md); fixes applied, tests added (edge shapes, shared write). Re-running suites.
- Unreachable 'JSON is not a list' branch removed (text starting with '[' that parses is a list). Suites: 3.12 622 OK, 3.10 622 OK (skipped=2), Node 16/16. Committing.
