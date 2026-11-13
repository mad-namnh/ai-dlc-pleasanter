# Plan — TD-37 evals on current skill versions (2026-11-13)

- **Nam's decision (2026-11-12, AskUserQuestion):** "Run all ~17 (Recommended)".
- **Tonight:** the skills AU1 (parked, uncommitted) does not change: P3 config-builder 0.8, script-engineer 0.6, P5 0.12, P6 0.3, onboarding 0.7, spec-recovery 0.4 — 7 cases. P2 (0.10 in the parked AU1 change) and lifecycle (its `references/kb-gaps.md` changed there) wait until AU1 is decided, so their results name a committed version.
- **How:** one fresh `pls-x-eval-case-runner` per case (model inherited: claude-opus-5-5), brief form `eval-case-brief.md`, scratch `../_agent-scratch/eval-20261113-<case>/`; grade against `expected.md` myself; results `evals/results/<skill>/2026-11-13.md`.
