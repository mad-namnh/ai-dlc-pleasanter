# Review — P2-7 tech debt and findings trace

- **Reviewer:** `pls-x-reviewer`, model `sonnet`, effort `medium`; round 1 of 2; uncommitted working tree against `HEAD`, limited to the P2-7 files (a parallel task's files ignored). Suites not run by the reviewer (the Orchestrator ran them).
- **Verdict:** accept with fixes — 0 Critical, 0 High, 2 Medium, 2 Low.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | Open roadmap items without a TD line: H6 / P0-8 (current-version evals), J1 / P0-9 (method-L dry run), P0-7 (Nam's decision per ADR-0014 row) | Fixed: TD-37 (evals, before cstg), TD-38 (method-L, B1 live, C10, before the first production release); TD-35 names the ADR-0014 row decisions and says which Proposed ADRs are not in use |
| M2 | Medium | No suite run recorded; a test might read the documents | `grep -rn "review-findings\|tech-debt" tools/pls/tests` → only a comment in `refusals_without_a_test.txt`; suites run before the commit (log) |
| L1 | Low | D21 cited "T `test_pls.py`" without a test name | Fixed: `test_process_without_display_condition_is_a_lint_error` |
| L2 | Low | Form points (TD-32 numbers, RF- prefix not applied) | No change: numbers accurate; the prefix decision is recorded in the plan |
