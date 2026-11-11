# Plan — eval of P4 0.9 and lifecycle 0.19 (`pls test-users`)

- **Task (Nam, 2026-11-11):** "chạy eval P4 0.9 và lifecycle 0.19"; scope chosen by Nam: 2 new cases + 3 regression cases.
- **Tier:** Standard (eval); model: opus for every case runner (evals are recorded with their model).
- **New cases:** P4 case-002 (per-role keys, no role key on dev yet); lifecycle case-008 (after G2, per-role keys, groups not created). Inputs written by the Orchestrator; rubrics in `proposed-expected.patch` (protected path) — Nam applies before the runs.
- **Regression:** P4 case-001 (scratch from `pls-demo-equipment` `547f549`, trimmed as its input says), lifecycle case-004 (EV-01), case-007 (EV-10).
- **Runs:** one `pls-x-eval-case-runner` per case, blind (brief form `eval-case-brief.md`), scratch under `../_agent-scratch/<run-id>/`; local `pls` commands relayed per `evals/README.md`. Grading by the Orchestrator; results `evals/results/<skill>/2026-11-11.md`.
