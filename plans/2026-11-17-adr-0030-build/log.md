# Log — adr-0030-build

- 2026-11-17: Nam "sau do lam ADR30"; choices recorded in plan.md. Main session model: claude-opus-5-5. HEAD a854dec. Uncommitted work of other sessions in the tree (HANDOFF.md, skills/README.md KB row, KB files, ADR-0014/0023, review-findings, tech-debt, settings.json): only this task's hunks are staged.
- Step 1: `tools/pls/tests/test_skills_hold_no_eval_data.py` (folder names eval/evals; file names expected.md, evals.json, EVAL.md, interviewee.md; Markdown with `# Rubric` or `## Must` + `## Must not`). On `a854dec` + the test, with a synthetic rubric planted at `skills/pls-x-lifecycle/references/case-notes.md` (copying a real `expected.md` is refused by the permission rules): FAILED naming that file. Without the plant: Python "Ran 719 tests … OK" (exit 0), node 16/16. Worktree removed.
- Reviewer call 1 (pls-x-reviewer, sonnet, medium — step 1).
- Step 1 review round 1: accept, 2 Low, no change (`review.md`). Subagent calls: 1 of 6.
- Step 2: `evals/README.md` — new section "Repeats, the no-skill baseline, scope and selection cases, cost (ADR-0030)" (k, run separation and holding place, baseline setup / allow-list / lift, scope and selection cases, cost, Part 5 rule, advisory + provisional, result template) and Running step 4; HANDOFF "How we work" evals line. ADR-0030 Status "partly built" moved to step 3, so it is written when the patches exist.
- Reviewer call 2 (pls-x-reviewer, opus, high — step 2, Critical: eval contract).
- Step 2 review round 1: accept with fixes, 2 Medium / 3 Low, all fixed; observation on `docs/` in the baseline allow-list reported to Nam (`review.md`). Subagent calls: 2 of 6.
- Step 2 verified on `d3a3202` + README + HANDOFF evals line only (temporary worktree): Python 719 OK (exit 0), node 16/16.
- Step 3: four patches written from HEAD versions (`git show`), each with its reason and apply command at the top; `git apply --check` OK for all four: `proposed-eval-case-brief.patch`, `proposed-eval-case-runner.patch`, `proposed-agent-rules.patch`, `proposed-dev-orchestrator-skill.patch`. ADR-0030 Status "partly built" (Nam's words) and its row in `docs/adr/README.md`.
- Reviewer call 3 (pls-x-reviewer, opus, high — step 3).
- Step 3 review round 1: accept with fixes, 1 High / 2 Medium / 4 Low, all fixed (`review.md`); also `evals/README.md` (request copied as `request.md`; `HANDOFF.md`, `interviewee.md`, held folder) and `CLAUDE.md` agent-team line. Patches regenerated; applied in `../_agent-scratch/wt-s3` + step-3 files: Python 719 OK (exit 0), node 16/16. Subagent calls: 3 of 6.
- Reviewer call 4 (round 2 of step 3, opus, high).
- Step 3 review round 2: accept with fixes, 3 Medium / 2 Low, all fixed or disposed (`review.md`); M1 asked of Nam. Verified at `62a113f`: patches apply; Python 723 OK, node 16/16. Subagent calls: 4 of 6. Review rounds for step 3: 2 of 2.
- Open for Nam: apply the four patches (or reject); M1 wording; follow-up — with-skill case inputs that carry setup notes / earlier results (P2 case 002 → `evals/results/`, P3 case 001 reference-answer line).
