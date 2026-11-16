# Transcript check — P1 0.7, case 001 (result `evals/results/pls-p1-requirements-analyst/2026-11-11-case001-v07.md`)

- **Date:** 2026-11-16. **Asked by:** Nam ("kiem tra transcript P1 case 001 ban 0.7").
- **Question:** did the runner see the hint in `skills/README.md` (P1 row: "the 対応期限 reminder (condition view 未完了) was judged unaffected"), which matches a Must item of the case rubric (review round 2, F1)?

## Evidence

- The hint entered `skills/README.md` in `f2e378c` (2026-11-11 12:46 +09:00), before the run; the 0.7 result was committed in `c70d856` (13:24 +09:00). So the hint existed in the framework during the run.
- Runner transcript: Claude Code session `3f2ff36e-…`, subagent `agent-a245eee970a3dc432.jsonl` (2026-11-11 04:21:02–04:24:11 UTC).
  - Brief: skill, KB and request all read from the scratch copy `../_agent-scratch/p1-case001-v07-run2/`; "the only place you may read project material from and write to".
  - Every tool call (Glob, Read, Grep, Write) has a path inside that scratch folder: the scratch `CLAUDE.md`, `REQUEST.md`, `config/`, `design/`, `traceability.json`, `environments.json`, `ops/log/`, the skill copy under `.claude/skills/pls-p1-requirements-analyst/` and the KB copy under `.claude/skills/pls-kb-pleasanter/`. No call reaches the framework's `skills/README.md`, `evals/` or `plans/`.
  - No tool result (file content the runner saw) contains "failed eval", "eval case 001", "9 of 10", "judged unaffected", "rubric" or "expected.md".
- The 0.7 skill change (`c70d856`) is generic: notifications / reminders / processes are read by their condition (watched columns, condition view); it names neither 対応期限 nor 未完了 nor the escalation request.

## Conclusion

The PASS was not contaminated by the `skills/README.md` hint: the runner never opened it, because it worked on a scratch copy with the skill copied in. The leak is real as a possibility (a runner briefed to read the skill from the framework could open `skills/README.md`); ADR-0030's brief patch forbids it in both arms.

Not changed by this check: the result is one run (k = 1), and 0.7 was written right after the 0.6 failure on this same case, so how far the rule generalises is shown only by case 002 (PASS on 0.7) — under ADR-0030 a k = 3 run, and a case from another domain with a condition-driven reminder, would show it.
