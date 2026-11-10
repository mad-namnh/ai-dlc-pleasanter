# Independent review — P3-1 (architecture §7.1 / §7.2 checked by a test)

Reviewer: subagent `pls-x-reviewer`, model `sonnet`, effort `medium`. Round 1 of 2. Reviewed: working tree against `846790a` on `brownfield-adr`. `git status` before and after the call: identical (the reviewer changed nothing).

**Verdict: accept.** No Critical, High or Medium finding.

## Findings

| # | Severity | Finding | Disposition (Orchestrator) |
|---|---|---|---|
| F1 | Low | The test reads `"rule"` values from every `tools/pls/*.py`, not only from what `pls lint` builds (test file, `emitted_lint_rules`). A `"rule"` dict built by a non-lint command would count as a lint rule and force a row in the first table of §7.2. Today no other command builds one; the failure would be loud. | Not changed. Accepted as a limit: the wrong result is a failing test, never a silent pass. |
| F2 | Low | The module docstring of `pls.py` (line 23) and the `pls lint` row of §7.1 still list an older rule set (L-REF-02, L-ENV-01 and others missing). | Not changed: outside the task (the task names the §7.1 command column and the §7.2 catalogue). Recorded as "not checked" in `HANDOFF.md` and in the report to Nam. |
| F3 | Low | A rule emitted through a form the AST reader cannot follow (f-string, computed value) is not compared; the test fails with an "unreadable" message instead. | Not changed: intended, safe direction. |

## Acceptance criteria as the reviewer saw them

1. Met — in-test mutations cover a command the parser lacks, a missing parser command and a second name in a cell.
2. Met — both directions for lint rules.
3. Met — commands from `pls.build_parser()`, rule codes from the source with `ast`; no hand-kept list (only sanity floors: more than 30 commands, more than 15 rules).
4. **Not verified by the reviewer** (read-only, no checkout). Verified by the Orchestrator in a temporary worktree of `846790a`: see `log.md`.
5. Met — Python `Ran 350 tests … OK`; node 15 pass, 0 fail.
6. Met — the `pls.py` diff is a pure extraction of `build_parser()`; no guard, gate, permission or protected path in the diff.

## Commands the reviewer ran

`git status`; `git diff 846790a -- tools/pls/pls.py docs/architecture.md HANDOFF.md`; `python -m unittest discover -s tools/pls/tests` (350 OK); the new test file alone (4 OK); `node --test tools/pls/tests/test_runner.mjs` (15 pass); grep for `"rule"` constructions and for L-DEP-01, L-SLOT-02, P-MIG-01.

## Not verified by the reviewer

The failure on the parent commit (criterion 4); the Python 3.10 run; the content of the plan and the log; `.claude/settings.json` (Nam's own edit, excluded from the review).
