# Plan — record the kb-verify results of the store-promo KB gaps (ADR-0023 step 6)

- **Tier:** Critical (`pls_scope.VERIFIED_KEYS` narrows what `pls release-plan` refuses).
- **Evidence:** `pls kb-verify --env dev` run by Nam on MADLAB dev (1.5.2.0, build 201520) on 2026-11-14, from the trial `pls-trial-store-promo` (report `ops/kb-verify/2026-11-14-dev.md` / `.json` there): 18/20 probes pass, D40-link-lookup-copy and D41-formula-after-lookup fail (looked-up `NumB` = 0).
- **Nam's decision (2026-11-14, "ok" to the proposal):** record the results via the curator, `VERIFIED_KEYS` for what passed, read more source on lookups and propose a revised D40 probe, two small `pls` fixes.

## Work

1. `tools/pls/pls.py` kb-verify: the report keeps every log line of a probe's tests (passing checks too — today only `NG`/`exec`/`expected` lines are kept, so a pass carries no evidence of what was checked); the confirmation asks for "the command name", not "the release id". Tests (`test_kbverify_report_evidence_and_prompt.py`).
2. `tools/pls/pls_scope.py` `VERIFIED_KEYS` + `PermissionForCreating`, `Formulas`, `StatusControls`, with the evidence in the docstring; `tests/test_scope.py` (new test; examples of an unverified key moved to keys still without evidence).
3. KB (curator): D36, D37, D39, D41 (formula part), D42 verified on 1.5.2.0; D40 and D41 (after lookup) failed on 1.5.2.0 with the observation and the open question; `probes/index.json`; `schema.md` rows; `skills/README.md` KB version.
4. Source notes on why the lookup did not copy (`source-notes.md` here); no revised probe until the cause is narrowed (a screen check by Nam distinguishes the hypotheses).

## Out of scope

- Manual probe D38 (person; pending).
- Changing D40's probe before the cause is known; changes in the trial repository.

## Acceptance

- Suites green (3.12, 3.10, node); new tests fail on `b00a551`.
- KB says only what the report shows; fails recorded as fails (I9), not removed.
- Independent review (Critical): no Critical/High open.
