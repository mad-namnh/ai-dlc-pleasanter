# Log — adr-0030-build

- 2026-11-17: Nam "sau do lam ADR30"; choices recorded in plan.md. Main session model: claude-opus-5-5. HEAD a854dec. Uncommitted work of other sessions in the tree (HANDOFF.md, skills/README.md KB row, KB files, ADR-0014/0023, review-findings, tech-debt, settings.json): only this task's hunks are staged.
- Step 1: `tools/pls/tests/test_skills_hold_no_eval_data.py` (folder names eval/evals; file names expected.md, evals.json, EVAL.md, interviewee.md; Markdown with `# Rubric` or `## Must` + `## Must not`). On `a854dec` + the test, with a synthetic rubric planted at `skills/pls-x-lifecycle/references/case-notes.md` (copying a real `expected.md` is refused by the permission rules): FAILED naming that file. Without the plant: Python "Ran 719 tests … OK" (exit 0), node 16/16. Worktree removed.
- Reviewer call 1 (pls-x-reviewer, sonnet, medium — step 1).
- Step 1 review round 1: accept, 2 Low, no change (`review.md`). Subagent calls: 1 of 6.
- Step 2: `evals/README.md` — new section "Repeats, the no-skill baseline, scope and selection cases, cost (ADR-0030)" (k, run separation and holding place, baseline setup / allow-list / lift, scope and selection cases, cost, Part 5 rule, advisory + provisional, result template) and Running step 4; HANDOFF "How we work" evals line. ADR-0030 Status "partly built" moved to step 3, so it is written when the patches exist.
- Reviewer call 2 (pls-x-reviewer, opus, high — step 2, Critical: eval contract).
- Step 2 review round 1: accept with fixes, 2 Medium / 3 Low, all fixed; observation on `docs/` in the baseline allow-list reported to Nam (`review.md`). Subagent calls: 2 of 6.
- Step 2 verified on `d3a3202` + README + HANDOFF evals line only (temporary worktree): Python 719 OK (exit 0), node 16/16.
