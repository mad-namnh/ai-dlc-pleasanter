# Plan — build ADR-0030 (eval repeats, no-skill baseline, scope and selection cases, cost)

- **Date:** 2026-11-17. **Asked by:** Nam ("sau do lam ADR30", after ADR-0030 was accepted on 2026-11-16 and its build deferred).
- **Nam's choices (AskUserQuestion, 2026-11-17, verbatim):** scope cases "Task sau (Recommended)" (scope / selection cases and their rubrics are a later task); Status "Ghi 'partly built' (Recommended)"; commits "3 commit (Recommended)".
- **Not in this build:** running any eval (the first baseline sweep, 45 runs, is asked of Nam as its own batch); scope / selection cases and rubrics; the open questions of the ADR.

## Steps (one commit each, each reviewed)

1. **Test** (Standard): `tools/pls/tests/test_skills_hold_no_eval_data.py` fails when `skills/` holds an eval dataset, rubric or expected output (ADR-0030 Part 6). Shown failing against a planted file. Review: sonnet, medium.
2. **Eval contract** (Critical): `evals/README.md` (repeats and run separation, baseline arm, scope / selection cases, cost, Part 5 rule, provisional label, result template); HANDOFF "How we work" evals line; ADR-0030 Status "partly built" and its README row. Review: opus, high.
3. **Patches for protected paths** (Critical): `proposed-eval-case-brief.patch`, `proposed-eval-case-runner.patch`, `proposed-agent-rules.patch` in this folder, each with its reason at the top; Nam applies them. Review: opus, high.

## Acceptance criteria

1. Every Decision part of ADR-0030 that is in scope appears in the files above, without contradicting the ADR, an Accepted ADR or the existing eval rules (blindness, relays, hand grading, eval model rule).
2. Protected paths changed only as patches that `git apply --check` accepts on the current commit.
3. Each new test fails on its parent commit (or against a planted fixture) and passes after; both suites green.
4. English only; only this task's paths and hunks committed; other work's uncommitted changes untouched.
