# Independent review — P2-3 (negative tests for refusals, ratchet, fix-commit check)

Reviewer: subagent `pls-x-reviewer`, model `sonnet`, effort `medium`, round 1 of 2, 2026-11-11. Reviewed: `f77b47a..151d4d9` plus the uncommitted part 3. `git status` before and after the call: identical.

**Verdict: accept with fixes** — no Critical or High finding; 2 Medium, 3 Low.

What the reviewer ran: the Python suite on 3.12 (381 OK), the node suite (15 pass), `python tools/dev/check_fix_commits.py` (exit 0), the diff of the four changed test files (additions only; each removed line is an exit-code assertion replaced by the same assertion plus more). Not verified by the reviewer: Python 3.10 (its launcher did not find it — the Orchestrator ran it: 382 OK, 2 skipped), the guard switch-off results, a test for every H1 row.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | The ratchet sees only a `raise` and a `print` / `return` with REFUSED / NOT marked / NOT VERIFIED; a refusal written another way (`sys.exit("…")`, a message with other words then `return 1`, a message appended to a list) is invisible | Fixed in part: `sys.exit` with a message is now a refusal (one more was found, the Python-version guard, and got a test that runs it: `test_an_older_python_is_refused_before_the_other_imports`). The remaining forms are stated as a limit in the module docstring, `HANDOFF.md` and TD-22 |
| M2 | Medium | The comparison runs only on Python 3.12+, on a whole-suite run, with the coverage slot free; elsewhere it is a skipped test that is easy to miss; a refusal reached only in a child process cannot be cleared | No CI exists to enforce it. Stated in the module docstring and in `HANDOFF.md` ("How we work"): the run that counts is the whole suite on 3.12+ with **no skipped test**. Kept as a limit in TD-22 |
| L3 | Low | A test that reaches a refusal without asserting anything clears it | Stated limit (module docstring); the review of each test covers it |
| L4 | Low | Many older guard tests begin with an exit-code assertion; the reviewer read some, not all, and those also assert no write | Not changed: the eight exit-code-only tests the design review listed were all handled (seven strengthened, one no longer exists) |
| L5 | Low | `check_fix_commits`: only a subject starting with `fix`; needs a changed test file, not a failing-on-parent proof; behaviour with an unknown start or a shallow clone | By design and stated (docstring, `HANDOFF.md`). An unknown start raises `GitError` (tested); the repository-history test skips when the start commit cannot be read |
