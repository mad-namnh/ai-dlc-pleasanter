# Plan — P1 eval case 002 on skill 0.6

- **Task (Nam, 2026-11-11):** "Eval P1 case 002 on 0.6". Tier: Standard (eval run; no code or skill text change, so no review — result file only).
- **Why:** HANDOFF lists "cases 001 and 002 not re-run on 0.5 / 0.6".
- **Steps:** build a fresh scratch project `../_agent-scratch/p1-case002-v06-run2/` exactly as `evals/pls-p1-requirements-analyst/case-002-category-accounting-time/input.md` says; one blind `pls-x-eval-case-runner` call (model of the session: opus); grade against `expected.md` myself; write `evals/results/pls-p1-requirements-analyst/2026-11-11-case002.md` + copy of the outputs; both suites; local commit.
- **Not reused:** `../_agent-scratch/p1-case002-v06/` (an earlier run of unknown provenance, 12:13–12:17; Nam chose a fresh run).
