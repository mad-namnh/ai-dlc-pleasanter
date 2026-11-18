# Log — D40 deployed-site check

- 2026-11-15 Opened after Nam's O-15/16/17 reports. Budget: subagents 0/6.
- Curator started (opus, high; subagent 1/6). TD-50 added (release needs a screen save for JSON links).
- Curator DONE_WITH_CONCERNS (D41 row/api.md mention only the API path — still true; left). Orchestrator: README 0.28, review-findings D40/D41, HANDOFF. Impact checklist update → separate commit.
- Review started (pls-x-reviewer, opus, high; subagent 2/6).
- Review round 1: accept with fixes (M1–M3, L1–L4) → review.md. Nam's answers → evidence 6–8. Curator fix call (opus, high; subagent 3/6).
- Orchestrator fixes: TD-50 (M2 drift wording, M1), TD-48 (M1, L3), TD-51 (impact checklist), README/HANDOFF (M3), ADR-0023 follow-up, review-findings D40/D41 status (L3).
- Curator fixes DONE (subagent 3/6). README and evidence header aligned (account not stated). Review round 2 next (subagent 4/6).
- 2026-11-15 Nam: resume (answers 1 code is for trial, 2 finish D40, 3 trial keeps lookup, 4 order agreed). Review round 2 started (pls-x-reviewer, opus, high; subagent 4/6).
- Review round 2: accept with fixes, H1 open (review.md). Stop per orchestrator rule (2 rounds). Questions to Nam for H1. git status unchanged by reviewer.
- Nam answers H1 q1/q2 (evidence 9–10); he repeats one updatesite deploy (evidence 11) — KB fix (curator) waits for that result. M1 (TD-50 export+drift), L2 (plan), L3 (evidence) fixed by Orchestrator.
- 2026-11-16 (other session): commit 5554586 took KB 0.28 (scalar probes); this task's README row was renumbered 0.29 in the working tree. Its texts that say "KB 0.28" (HANDOFF line, TD-50 / TD-51) need 0.29 when this task commits.
- 2026-11-16 (other session): commit 676d28c took KB 0.29; this task's README row is renumbered 0.30 in the working tree (texts saying KB 0.28 / 0.29 for D40 need 0.30 when this task commits).
- 2026-11-16 (other session): commit 904927f took KB 0.30 (D16 advice) and the mail-keys commit takes 0.31; this task's README row is renumbered 0.32 (texts saying KB 0.28 / 0.29 / 0.30 for D40 need 0.32 when this task commits).
- 2026-11-16 (other session): ADR-0029 A (75f9b3b) generates skills/pls-p2-solution-designer/references/impact-rules.md from the committed KB; when this task commits its behaviours.md rows, run `python tools/pls/pls_impact_rules.py --write` in the same commit (test_impact_rules fails otherwise) — that also closes TD-51.
- 2026-11-17 (other session): 62a113f took KB 0.32 (probes D48–D51); this task is renumbered 0.33 in the working tree.
- 2026-11-17 (other session): 29796bb took KB 0.33 (D16 サマリ); this task renumbered 0.34. Its D16-related texts may need the サマリ naming when committed.
- 2026-11-18 (other session): f48f1ae took KB 0.34; this task renumbered 0.35.
- 2026-11-18 (other session): e32c9b8 took KB 0.35 (TD-63); this task renumbered 0.36. When committing, also run `python tools/pls/pls_impact_rules.py --write`.
