# Log — deterministic phase checks

- 2026-11-16 Nam, verbatim "đồng ý, viết ADR và plan theo thứ tự 2, 1, 3". ADR-0029 written as Proposed with options per part (A knowledge from one source, B phase outputs + pls check, C hooks); plan.md. No code. Decisions 1–4 of plan.md asked of Nam.
- 2026-11-16 Nam 2026-11-16 (AskUserQuestion, his answers verbatim): Part A "A2 generated file (Recommended)"; Part B form "B1 front matter (Recommended)"; gate "Blocking + accept (Recommended)"; hooks / evals "C1 + evals approved now (Recommended)". ADR-0029 Accepted; evals of P1 / P2 / lifecycle approved for this plan.
- 2026-11-16 Part A built in worktree wt-rules (base 904927f): pls_impact_rules.py, classify rule ids, generated impact-rules.md, test_impact_rules.py, P2 skill 0.12, checklist procedure, DES template rule column, TD-64/65/66, ADR-0029 As built.
- P2 eval (approved by Nam) deferred to one run after Part B (B5 changes P1 / P2 / lifecycle again): one eval batch instead of two. P2 0.12 marked "evaluation pending".
- Review round 1 (opus, high; subagent 1/6): accept with fixes (F1–F3 Medium, F4–F8 Low) → all fixed in worktree wt-r2 on 09de5d2 (review.md). Round 2 next.
- Review round 2: accept with fixes, Low only → fixed. Commit.
- 2026-11-16 Part B built in worktree wt-B: pls_front_matter.py, pls_phase_check.py, `pls check`, gate coupling, templates, P1 / P2 / P3 / lifecycle skill text, TD-67.
- Part B review round 1 (opus, high; subagent 3/6): accept with fixes, F1 High → all fixed (review.md). Round 2 next.
- Fixes broke tests that approved G1 for REQ ids without documents (test_gate: now writes complete REQs) and the approver-first refusal (profile test: `GT.validate` runs before the checks); layout test expects `sources` (now joined by pls); refusal list: two gate refusals moved to `validate`.
- Part B review round 2: accept with fixes (R2-1 Medium, R2-2/3 Low) → fixed. Commit after suites.
- 2026-11-17 Part C built in worktree wt-C2 (base 73f2c6b): hook contract notes, pls_hooks.py, `pls hook`, init installs hooks, layout and command table rows, TD-21 note.
- Part C review round 1 (opus, high; subagent 4/6): accept with fixes, F1/F2 High → fixed (review.md). Smoke test on a pls-demo-inquiry copy (git files, no .pls/) in ../_agent-scratch/smoke-C: `hook install` added the three events and kept the file; pre on gates/x.json → deny; stop → systemMessage "p1 15, p2 4 finding(s)" (no front matter yet → TD-68).
- Part C review round 2: accept with fixes, Low only → fixed / documented (review.md). Commit.
