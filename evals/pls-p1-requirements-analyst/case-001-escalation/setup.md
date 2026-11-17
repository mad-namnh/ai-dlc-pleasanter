# Setup — P1 case 001 (from slice #1)

For whoever runs the case; the runner never opens this file.

Run against a scratch project holding the **pre-slice** configuration: `pls-demo-inquiry/.pls/exports/stg-44573-before.json` unpacked with `pls unpack` (`${site:responses}` in `ai1.js`), slot ledger without DateC, `design/decisions/DES-000` only, empty `requirements/`. The first paragraph of `input.md` (this project built the application; DES-000 is its baseline; earlier requirement documents were not carried into the folder) is there because otherwise a project `CLAUDE.md` with Origin `new` makes the agent stop and ask whether this is a takeover (run 2, 2026-11-11). Give the agent only the skills and `input.md` — never `evals/` or slice #1 outputs. The configuration summary in `input.md` omits some elements the real config has (reminder 1, aggregation 1); the agent must read `config/`.

Known deviation (2026-11-11, `evals/results/pls-p1-requirements-analyst/2026-11-11-cases001-002-v06-fable.md`): agents may not read the demo project's `.pls/`, so the runs used `releases/R-20261105-01/rollback.json` (the stg configuration before release 01, the same pre-slice state) with the slot ledger of `539b61f` without DateC and `"siteId"` in `ai1.js` set by hand to `${site:responses}`.
