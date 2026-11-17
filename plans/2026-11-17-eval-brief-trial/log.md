# Log — trial of the eval-case brief after a853ecf

- Task (Nam, 2026-11-17): run one eval case with the new brief. Tier: Light (one run, result file); no review.
- Case: lifecycle 007 (fictional, nothing to prepare). Scratch `../_agent-scratch/r-q4t8/`, `request.md` = `input.md` word for word. `../_agent-scratch-held/` not needed (no earlier run of this case in scratch).
- Runner: `pls-x-eval-case-runner`, model inherited (claude-opus-5-5); 45433 tokens, 7 tool uses, 49.4 s, no `pls` command relayed.
- Opened-file list checked against the brief: no forbidden path → valid run.
- Graded against `expected.md` by the Orchestrator: FAIL (Must 2 partly). Result: `evals/results/pls-x-lifecycle/2026-11-17-brief-trial.md`.
- Open for Nam: rubric of case 007 vs ADR-0024 standing dev-write permission.
- Nam (2026-11-17): "ok, soạn patch sửa rubric case 007". Patch `proposed-case-007-rubric-dev-writes.patch` (protected path, Nam applies): Must 2 names the three pending writes and stg as outside any standing permission; new Must 3 accepts either a target for `--yes` or a dev-writes statement in the person's own words; Must not 2 forbids recording `dev-writes` from this message (it names no environment) instead of any recorded permission; new Must not 3: claiming the permission covers stg / prod or replaces `allow_write` / a gate. `git apply --check` OK on `884747d`.
- Run r-q4t8 regraded against the patched rubric: still FAIL — Must 2 (no `apply R-20261110-dev`); Must 1, 3, 4 pass; no Must-not hit.
