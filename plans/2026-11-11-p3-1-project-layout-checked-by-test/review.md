# Independent review — P3-1 (rest): architecture §3.2 checked by a test

Reviewer: subagent `pls-x-reviewer`, model `sonnet`, effort `medium`, round 1 of 2, 2026-11-11. Reviewed: working tree against `7f4fba3`. `git status` before and after the call: identical.

**Verdict: accept** — no Critical, High or Medium finding; 3 Low.

Acceptance criteria as the reviewer found them: 1–4, 6, 7 met (it ran both suites: Python 357 OK on the current version and on 3.10 with 1 skipped; node 15 pass; and its own mutations of the tree text, which were all reported). Criterion 5 it could not run (no checkout allowed); the Orchestrator ran it in a worktree of `7f4fba3`: 6 of 7 tests fail there.

Per-line check of the tree: no line found false. Not confirmed by the reviewer: `htmls/` (only the map entry at `pls.py:93`), the word "legacy" for `approvals.md`, the meaning of the `ops/env-compare` and `design/decisions` comments.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| L1 | Low | Check C matches a name against every word of every text constant and `code` span, so a name used anywhere passes at any place (`README.md`, `tests`, `drift`, `config` added under the root are accepted) | Kept: declared as not checked (place of a name; check C is the loose direction). Recorded in `HANDOFF.md` as a limit |
| L2 | Low | `HANDOFF.md` names the commit of this change as the last commit before it exists | True once committed; committed in the same commit |
| L3 | Low | The `.gitattributes` comment does not say that `pls merge-install` adds a merge driver line | Not changed: comments are short and not checked |
| — | note | "legacy" for `approvals.md` is the implementer's word (the file is read by `pls_gate.py:335` and shipped by `pls_package.py:30`, and skills still name it) | Fixed: comment now "approvals note for people; the records pls checks are in gates/" |
