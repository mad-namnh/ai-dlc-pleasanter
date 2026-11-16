# Log — departments in pls principals

- 2026-11-16 Source: DeptsController (Pleasanter_1.5.2.0) HttpPost Get; field names from the Depts table (not read back). Plan's '--create like groups' not built (new write path outside ADR-0017; departments are the customer's org) — recorded in plan.md.
- Existing test test_only_groups_with_a_final_name_are_created used {principal: Dept} as its 'not a group' case; a Dept role is now looked up, never created (new test: no write with --create). The case is changed to {principal: Role} so the 'not a group' refusal is still run — not a deletion or relaxation (EV-02): the no-creation property for Dept is asserted by test_a_missing_department_is_reported_and_never_created.
- Suites: 3.12 628 OK; 3.10 628 OK (skipped=2); node 16/16 (JS unchanged). Parent check below.
- Parent check (new test file + fake server change on 2dca8a3, bind_principals unchanged there): 3 failures, 1 error in the 4 new tests.
- Review round 1 started (pls-x-reviewer, sonnet, medium — Standard; subagent 1/6).
- Review round 1: accept (Low-1 fixed with a test; Low-2/3 → TD-64). Suites: 3.12 629 OK; 3.10 629 OK (skipped=2); node 16/16. Subagents 1/6.
- Committed (see git log); REPORT SENT
