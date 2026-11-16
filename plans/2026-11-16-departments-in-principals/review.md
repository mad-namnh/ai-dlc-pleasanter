# Review — departments in pls principals

## Round 1 (pls-x-reviewer, sonnet, medium) — accept; no Critical/High

- **Low-1:** a numeric `dept_code` never matched → read as text; test.
- **Low-2:** field names of `/api/depts/get` not read back from a real server; the fake shares the assumption → already TD-64 and ADR-0006 as-built line; a wrong name fails safe (lookup refused or missing).
- **Low-3:** P2 skill names only groups / users → TD-64.
- Changed input of `test_only_groups_with_a_final_name_are_created` judged legitimate (EV-02): the "not a group" refusal is still run; Dept non-creation has its own test.
- Not run by the reviewer: 3.10, node, parent check — run by the Orchestrator (log).
