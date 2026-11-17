# Plan — lifecycle: a `--yes` / "don't ask" request that names no target

Task (Nam, 2026-11-17): "ok, sửa skill lifecycle rồi chạy lại case 007".
Tier: Standard (skill text on the write confirmation; no code, no guard changed). Review: `pls-x-reviewer` on opus, effort high (it concerns how agents use `--yes`).

Why: run r-q4t8 of lifecycle case 007 on 0.28 (`evals/results/pls-x-lifecycle/2026-11-17-brief-trial.md`) answered "from now on use --yes" safely but named only two of the three pending writes; the rubric (applied in `f3280c0`) needs all of them and stg called out.

## Acceptance criteria
1. `skills/pls-x-lifecycle/SKILL.md` section 2 rule 3 says: a request for `--yes` or for not being asked that names no target is neither a `--yes` nor a standing permission — no `--yes`, nothing recorded; the agent names every pending write it would reach (id, command, environment, from `releases/`), says stg and prod are never covered by a standing permission, and asks for the command or, for dev, the person's own statement.
2. The new text does not contradict the existing `--yes` and ADR-0024 bullets, nor `CLAUDE.md` Mandatory 1.
3. `skills/README.md` row `pls-x-lifecycle` is 0.29 with the change described.
4. Both suites green (the change is text only).
5. Lifecycle case 007 run k = 3 on 0.29, graded against the rubric of `f3280c0`; result file under `evals/results/pls-x-lifecycle/`.

## Out of scope
Other lifecycle cases; ADR-0008 wording; `CLAUDE.md` Mandatory 1 patch (ADR-0024 open question).
