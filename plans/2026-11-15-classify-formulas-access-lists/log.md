# Log — classify formulas and access lists

- 2026-11-15 Implemented in pls.py classify (+ _names_principals helper shared with the process rule). Tests in test_pls. Parent check (worktree of a503d21, removed): 5 access-list subtests + formula test FAIL; NotInheritPermissionsWhenCreatingSite already permission-impacting on the parent (key name) — inventory corrected.
- ADR-0004 Consequences as-built note; inventory counts corrected (5 wrong classes).
- Budget: subagents 0/6.
- Suites: 3.12 616 OK, 3.10 616 OK (skipped=2), Node 16/16. Review started (pls-x-reviewer, opus, high; subagent 1/6).
- Review round 1: accept with fixes (review.md). F1–F6 fixed; F7 disposition. New flat_diff-driven test FAILs with the round-1 regexes (worktree, removed; the revert there also broke the older access-list test, so only the new test is evidence).
- Suites after fixes: 3.12 617 OK, 3.10 617 OK (skipped=2), Node 16/16. Committing.
