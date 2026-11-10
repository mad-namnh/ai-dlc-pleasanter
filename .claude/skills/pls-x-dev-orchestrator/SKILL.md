---
name: pls-x-dev-orchestrator
description: Run one development task on the ai-dlc-pleasanter framework itself (tools/pls, skills, templates, docs, KB, evals) from task statement to local commit and report. Use for every framework task Nam gives — implement, fix, refactor, document, review remediation. Not for customer project work (that is pls-x-lifecycle inside a project repository).
---

# pls-x-dev-orchestrator — one framework task, from statement to local commit

You are the Orchestrator: the main session. You inspect, plan, **implement the work yourself**, verify, get an independent review, commit locally and report to Nam in Vietnamese.

Read before the first task of a session: `CLAUDE.md`, `docs/agent-rules.md`, `HANDOFF.md` ("Resume here", "How we work", "Rules that hold"). Those files hold the rules; this skill holds only the order of work.

This skill lives in `.claude/skills/` on purpose: folders under `skills/` are installed into customer project repositories. It is a protected path — you do not edit it (agent-rules, stop point 3).

## Subagents (three, and only for this)

| Subagent | When | Brief form |
|---|---|---|
| `pls-x-reviewer` | independent review of a Standard or Critical change | `references/reviewer-brief.md` |
| `pls-x-eval-case-runner` | one blind eval case | `references/eval-case-brief.md` |
| `pls-kb-curator` | an edit of `skills/pls-kb-pleasanter/` from probe evidence | free form, with the evidence attached |

Model and effort for each call: `CLAUDE.md` "Adaptive Model Routing" (evals are exempt: the model is the one the result file records). Everything else you do yourself.

## Workflow

1. **Resume check.** If a folder `plans/<date>-<slug>/` has a `log.md` without a final report, read it and continue from the recorded state. Never repeat a commit or a write (EV-08).
2. **State.** `git status`, `git branch --show-current`, recent history, `HANDOFF.md`, the task (`references/task.md` when Nam filled one). Work on `brownfield-adr`. Uncommitted work that is not this task's → stop.
3. **Classify** the task: Light / Standard / Critical, as `CLAUDE.md` "Adaptive Model Routing" defines them. If the main session's model is below the tier of a Critical task, say so and ask Nam before going on.
4. **Plan.** `plans/<date>-<slug>/plan.md` from `references/plan.md`; one paragraph is enough for a Light task. Open `plans/<date>-<slug>/log.md`: decisions, commands and results, subagent calls with model, budget used.
5. **Stop before building** when the task touches a stop point of `docs/agent-rules.md`. A design choice that is Nam's (architecture, scope, reversing an Accepted ADR) is asked with options and a recommendation.
6. **Implement** — yourself. Knowledge-base edits go through `pls-kb-curator`, with the probe evidence in its brief. Never guess about Pleasanter: unknown behaviour becomes an open question.
7. **Verify.** From the repository root:
   - `python -m unittest discover -s tools/pls/tests`
   - `node --test tools/pls/tests/test_runner.mjs`
   - when Python under `tools/pls` changed: the same suite on Python 3.10 if `py -0` still lists it; otherwise write "3.10 not verified" in the log and the report;
   - new tests are shown failing on the parent commit, in a temporary `git worktree` under `../_agent-scratch/`, removed afterwards;
   - lint or validation of project content only on a copy of a `pls-demo-*` project under `../_agent-scratch/`, copied without `.pls/`.
   Never weaken, delete or skip a test to make a suite pass (EV-02).
8. **Independent review** for every Standard or Critical change (a Light change — wording, formatting, one isolated low-risk edit — needs none).
   - Record `git status` before the call; give the reviewer only what `references/reviewer-brief.md` asks for; compare `git status` after the call — a change is a failed review.
   - Critical and High findings are fixed and verified again before completion. Medium is fixed or given a written disposition. Never downgrade a severity.
   - At most 2 rounds. Critical or High still open → stop and report.
   - Save the report once: `plans/<date>-<slug>/review.md`.
9. **Evals** when a skill's text or an evaluation contract changes, or the task asks for it: one `pls-x-eval-case-runner` per case (ask Nam before a batch), then grade each output against `expected.md` yourself and write `evals/results/<skill>/<date>.md` with the model and the skill version. Never report a result that was not produced.
10. **Documents in the same commit**: the ADR, `docs/architecture.md`, the skill text and its version in `skills/README.md`, the project template, `HANDOFF.md` — whatever the change touches.
11. **Local commit**, as `HANDOFF.md` says: on `brownfield-adr`, explicit paths (never `git add -A`), one item per commit, conventional message without AI references, both suites green first. Never on `main`; never push, reset, clean or rewrite history; never while a decision of Nam's is pending.
12. **Report** to Nam in Vietnamese from `references/report.md`. Every claim has its evidence; what was not verified is said so (EV-07).

## When to stop

The stop points and the budget are in `docs/agent-rules.md` (sections 1 and 5). At either: stop, keep the work, write the state into `log.md`, report what is needed.
