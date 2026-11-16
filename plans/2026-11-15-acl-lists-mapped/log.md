# Log — access lists mapped

- 2026-11-15 Implemented ACL_LISTS / acl_items in pls.py; lint, payload, adopt summary use it; pls_scope message. Test in test_pls (views with ']' in the name, exports, dashboard parts, status controls, column access controls; raw id refused).
- Parent check (worktree of f2e5208, removed): new test FAILS.
- Docs: ADR-0006 Consequences note, architecture L-PERM-01, inventory rows.
- Suites: 3.12 618 OK, 3.10 618 OK (skipped=2), Node 16/16. Review started (pls-x-reviewer, opus, high; subagent 1/6). Nam: work through the open tasks in order; he checks tomorrow.
- Review round 1: accept with fixes (Low only, review.md). L1, L3, L4 fixed; L2 + nested views → TD-58. Re-running suites.
- Suites after fixes: 3.12 618 OK, 3.10 618 OK (skipped=2), Node 16/16. Committing (tech-debt.md: TD-58 only).
