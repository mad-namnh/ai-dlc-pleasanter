---
name: pls-p4-test-writer
description: Phase P4 of AI-DLC for Pleasanter. Turns acceptance criteria into API test specs (tests/api/*.json), including tests per restricted role. Runs them on dev with pls test, triages failures back to the right phase, and writes the G3 evidence (g3-verification.md). Use after P3 has deployed to dev, and before G3.
---

# pls-p4-test-writer

**Goal:** every in-scope acceptance criterion is proven on dev by a passing test, or explicitly marked as manual. Restricted roles are proven as the project profile says (**Role tests**):
- `per-role keys`: each restricted role is tested with its own key.
- `deferred` (demo stage): only the operator's key exists. Role restrictions are proven in the configuration (permissions entries and process access control, checked with `siteConfig` and by the 0-difference round trip) and listed in G3 as "role test deferred".
**Tests prove the requirement, not the configuration.** A test that passes because it was bent to the build is worse than a failing one.

## Inputs

- G1-approved `requirements/REQ-*.md` (acceptance criteria), `design/decisions/DES-*.md`, `traceability.json`.
- dev deployed by P3 (round trip 0).
- `references/test-spec.md` (this skill) — the spec format; `references/g3-template.md` — the evidence file.
- `.pls/connections.json` keys: `pls http-check --env dev` lists them. With role tests `deferred` there is one key.

## Procedure

1. **Map acceptance criteria to tests.** One test (`T-NNN`, numbered sequentially across the project) per behaviour. Mark each criterion as one of:
   - **API-testable** — the default;
   - **config check** (`siteConfig`) — for screen-only behaviour such as required columns (D27) or read-only columns (D17);
   - **manual** — a person checks the screen. Write down what to look at.

   Never claim a manual check as automated.
2. **Write the specs** in `tests/api/<area>.json` (`references/test-spec.md`):
   - Positive path with exact expectations.
   - Negative path for every "shall not / only when / cannot" criterion: `expectHttp` with 400, 403, 404 or 500 per the KB (D10, D19, D20, D21).
   - Role tests `per-role keys`: one spec file per role. `as_key` names the role key; fixtures are created in steps that run with an authorised key (step-level `as_key`).
   - Role tests `deferred`: no `as_key` (default key). For each "cannot / only" criterion of a restricted role, write a `siteConfig` check of the setting that enforces it (e.g. `Processes.0.Groups`). Write the role test as a manual or deferred item.
   - Records are created by the test itself (`save` / `$var`); never depend on data already on dev.
   - Test record titles start with `テスト` so a person can find and remove them.
3. **Run** `pls test tests/api/<spec>.json --env dev --site <default site> [--var k=v]`. Results go to `tests/results/<env>-<date>-<spec>-http.json`. Read the console summary only; for a failure, read that test's log lines.
4. **Triage every failure before changing anything:**

   | Cause | Go to |
   |---|---|
   | config differs from the design | P3, redeploy, rerun |
   | design cannot meet the criterion | P2 → G2 reopened |
   | criterion is wrong or untestable as written | P1 → G1 reopened (the person decides) |
   | Pleasanter behaves differently from the KB | correct the KB in the framework (I9), then the design |
   | the test itself is wrong | fix the test and write why in the commit |

5. **Coverage.** Add the test ids to `traceability.json` (`"tests"` per REQ). `pls coverage` must show 100 % of in-scope REQs with config and tests. `pls lint` must show 0 issues.
6. **Write `releases/<release>/g3-verification.md`** from `references/g3-template.md`. `<release>` is the release P5 will create: for target dev, the last dev release (`R-YYYYMMDD-NN-dev`); for target stg or prod, the id P5 will plan (`R-YYYYMMDD-NN`, without `-dev`), created now as a folder that holds only `g3-verification.md` until `release-plan` fills it. Commit (`test(p4): …`). **Stop at G3** (see `pls-x-lifecycle` and its `references/gates.md`).

## Checklist before G3

- [ ] Every acceptance criterion maps to a test or to a named manual check.
- [ ] Every "cannot / only" criterion has a negative test run as the role it restricts (`per-role keys`), or a config check plus a "role test deferred" line (`deferred`).
- [ ] No test depends on pre-existing records; no test was edited to pass without a reason.
- [ ] All tests `pass` or `pass-api-only`. An `editPage` step needs a browser session and stays a manual check over HTTP.
- [ ] `pls coverage` 100 %, `pls lint` 0 issues, dev round trip 0.
